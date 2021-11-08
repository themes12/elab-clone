import re
import json

############################################################
def extract_params(obj,params):
    valid_params = obj.REQUIRED_PARAMS + obj.OPTIONAL_PARAMS
    req_params = set(obj.REQUIRED_PARAMS)
    for (k,v) in params.items():
        if k in valid_params:
            setattr(obj, k, v)
            if k in req_params:
                req_params.remove(k)
        else:
            raise ElabException("Unknown parameter '%s'" % k)
    if req_params:
        raise ElabException("Missing required parameters: %s" % 
            ','.join("'{}'".format(p) for p in req_params)
            )

############################################################
class ExtractedTask:

    #########################
    def __init__(self):
        self.codesegs = []
        self.testCases = []
        self.embeddedMedia = []
        self.language = 'python'
        self.markers = ('{{', '}}')
        self.score_markers = ('[', ']')
        self.textBlanks = {}
        self.countBlanks = 0
        self.buildflags = []
        self.runflags = []

    #########################
    def config(self, **params):
        for (k,v) in params.items():
            if k in ['lang', 'markers']:
                setattr(self, k, v)
            else:
                raise ElabException('Unknown parameter: %s' % k)

    #########################
    def addCodeSegment(self, codeseg):
        # resolve for each blank's id
        for p in codeseg:
            if isinstance(p, Blank):
                self.countBlanks += 1
                p.id = self.countBlanks

        self.codesegs.append(codeseg)

    #########################
    def addTestCase(self, testcase):
        self.testCases.append(testcase)

    #########################
    def addTextBlank(self, answer, score):
        self.countBlanks += 1
        self.textBlanks[self.countBlanks] = (answer,score)
        return self.countBlanks

    #########################
    def addBuildFlags(self, flags):
        self.buildflags.append(flags)

    #########################
    def addRunFlags(self, flags):
        self.runflags.append(flags)

    #########################
    def getCode(self):
        return Code(self.codesegs, {
            'build' : ' '.join(self.buildflags),
            'run'   : ' '.join(self.runflags),
            })

    #########################
    def getTestCases(self):
        return self.testCases

    #########################
    def getTextBlanks(self):
        return self.textBlanks


############################################################
class HiddenLine(str):
    pass

############################################################
class ExcludedLine(str):
    pass

############################################################
class Code:
    'Holds an entire code portion of a certain task'

    def __init__(self,codesegs=[],flags={}):
        self.sequence = []
        self.mapSeqToBlank = {}
        self.flags = flags
        blankCount = 0
        for t in codesegs:
            if t.excluded:
                continue
            for s in t.sequence:
                # if this piece of code is a blank, create a map from the
                # sequence index to the blank index for later use
                if isinstance(s, Blank):
                    self.mapSeqToBlank[len(self.sequence)] = blankCount
                    blankCount += 1
                self.sequence.append(s)
            # TODO: elab's markdown processor sometimes adds a new line at the
            # end of a code segment.  This needs more tests for consistency.
            if self.sequence and self.sequence[-1] != '\n':
                self.sequence.append('\n')

    def dump_solution(self):
        '''
        returns solution.
        '''
        lines = []
        for s in self.sequence:
            if isinstance(s,Blank):
                lines.append(s.formattedAnswer(None))
            elif isinstance(s,HiddenLine):
                lines.append(s)
                lines.append('\n')
            elif isinstance(s,ExcludedLine):
                pass
            else:
                lines.append(s)

        return ''.join(lines)

    def dump(self,updates={}):
        '''
        If a dict is provided as updates argument, blanks inside the
        original code will be replaced by values from the dict.  If
        the blank's key does not exist, '' will be used.
        '''
        lines = []
        for i,s in enumerate(self.sequence):
            if isinstance(s,Blank):
                newAns = None
                try:
                    newAns = updates[self.mapSeqToBlank[i]]
                except KeyError:
                    newAns = ''
                lines.append(s.formattedAnswer(newAns))
            elif isinstance(s,HiddenLine):
                lines.append(s)
                lines.append('\n')
            elif isinstance(s,ExcludedLine):
                pass
            else:
                lines.append(s)

        return ''.join(lines)


############################################################
class Blank:
    def __init__(self, answer, indent=0):
        self.answer = [answer]
        self.indent = indent
        self.length = len(answer)

    def addRow(self, answer):
        self.answer.append(answer)

    def rowCount(self):
        return len(self.answer)

    def rawAnswer(self):
        return '\n'.join(self.answer)

    def formattedAnswer(self, answer=None):
        if answer != None:
            answer = answer.replace('\r\n','\n').split('\n')
        else:
            answer = self.answer

        return '\n'.join([
            answer[0]] + [(' '*self.indent)+x for x in answer[1:]])

    def __str__(self):
        return self.rawAnswer()

    def __repr__(self):
        return 'Ans(%s)' % self.rawAnswer().replace('\n',r'\n')


############################################################
class CodeSegment:

    REQUIRED_PARAMS = []
    OPTIONAL_PARAMS = [
        'hidden','lineno','highlight','excluded','blank','language',
    ]

    #########################
    def __init__(self, markers, **params):
        self.hidden = False
        self.lineno = False
        self.highlight = True
        self.markers = markers
        self.excluded = False
        self.blank = False
        self.language = None
        extract_params(self, params)

    #########################
    def makeSequence(self,code,start_line):
        'makes a sequence of shown and hidden code portions'
        begin, end = self.markers
        marker_re = re.compile(re.escape(begin) + "(.*?)" + re.escape(end))
        seq = []
        prevBlank = None
        for lineno,line in enumerate(code):
            # make sure all resulting pieces are wrapped by the same class as
            # the original line
            lineclass = line.__class__
            line = line.rstrip()
            pieces = [lineclass(x) for x in marker_re.sub('\n', line).split('\n')]
            blanks = marker_re.findall(line)
            indent = 0

            # in case the entire code segment is made blank
            # just remove all the markers and add the whole line to the blank
            if self.blank:
                tmpline = [pieces[0]]
                for (i,p) in enumerate(pieces[1:]):
                    tmpline.append(blanks[i])
                    tmpline.append(p)
                wholeline = ''.join(tmpline)
                if len(seq) == 0:
                    seq.append(Blank(wholeline))
                else:
                    seq[0].addRow(wholeline)

            # See whether this line can be merged with surrounding lines so that
            # multi-row field will be used instead.
            #
            # The conditions are:
            #  - there is exactly one blank
            #  - preceded with all spaces
            #  - and nothing following
            elif len(blanks) == 1 and pieces[0] == ' '*len(pieces[0]) \
                    and pieces[1] == '':

                indent = len(pieces[0])

                # if indent and blank sizes are all matched, merge with previous
                if prevBlank and \
                        prevBlank.indent == indent and \
                        prevBlank.length == len(blanks[0]):
                    prevBlank.addRow(blanks[0])
                else:
                    blank = Blank(blanks[0], indent)
                    seq.append(pieces[0])
                    seq.append(blank)
                    seq.append('\n')
                    prevBlank = blank

            else:
                seq.append(pieces[0])
                if isinstance(pieces[0],HiddenLine) and len(pieces) > 1:
                    raise ElabException("Hidden line must not contain a blank",
                            (lineno+start_line+2) )
                if isinstance(pieces[0],ExcludedLine) and len(pieces) > 1:
                    raise ElabException("Excluded line must not contain a blank",
                            (lineno+start_line+2) )
                for (i,p) in enumerate(pieces[1:]):
                    seq.append(Blank(blanks[i]))
                    seq.append(p)
                if not isinstance(pieces[0],HiddenLine) and \
                   not isinstance(pieces[0],ExcludedLine):
                    seq.append('\n')
                prevBlank = None

        self.sequence = seq

    #########################
    def __iter__(self):
        for x in self.sequence: yield x


############################################################
class ExtractedTestCase:

    REQUIRED_PARAMS = []
    OPTIONAL_PARAMS = ['hint','visible']

    #########################
    def __init__(self, **params):
        self.hint = ""
        self.visible = False
        extract_params(self, params)

    #########################
    def set_input(self, input):
        self.input = '\n'.join(input)

############################################################
class ElabException(Exception):

    def __init__(self,msg,lineno=None):
        Exception.__init__(self,msg)
        self.lineno = lineno

############################################################
class EmbeddedMedia:

    REQUIRED_PARAMS = ['media']
    OPTIONAL_PARAMS = ['feedback']

    #########################
    def __init__(self, **params):
        self.feedback = False
        extract_params(self, params)
        media_info = self.media.split(':',1)
        if len(media_info) != 2:
            raise ElabException('Invalid media identifier')
        self.type = media_info[0]
        self.media_id = media_info[1]

