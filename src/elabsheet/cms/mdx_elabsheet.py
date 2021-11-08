import re
import markdown
from markdown.util import etree,AtomicString
from markdown.treeprocessors import Treeprocessor
from .elab import \
        HiddenLine,ExcludedLine,Code, \
        Blank,CodeSegment,ExtractedTestCase,EmbeddedMedia, \
        ElabException
from .syntax import Highlighter,append_text_or_elem

# Constants
ELAB_PREFIX = '::elab:'
BLANKLINE_PLACEHOLDER = ELAB_PREFIX + 'blankline'
CODESEG_PLACEHOLDER = ELAB_PREFIX + 'codeseg'

TESTCASE_PLACEHOLDER = ELAB_PREFIX + 'testcase'
TESTCASE_PLACEHOLDER_PATTERN = re.escape(TESTCASE_PLACEHOLDER) + ' ([0-9]*)'
TESTCASE_PLACEHOLDER_RE = re.compile(TESTCASE_PLACEHOLDER_PATTERN)

EMBEDDED_MEDIA_PLACEHOLDER = ELAB_PREFIX + 'embed'
EMBEDDED_MEDIA_PLACEHOLDER_PATTERN = re.escape(EMBEDDED_MEDIA_PLACEHOLDER) + ' ([0-9]*)'
EMBEDDED_MEDIA_PLACEHOLDER_RE = re.compile(EMBEDDED_MEDIA_PLACEHOLDER_PATTERN)

BLANK_ID_PREFIX = 'b'
DEFAULT_SCORE = 1

# Compiled regex to match e-labsheet markups
ELAB_TAG_RE = re.compile(r'^%s(\w*)(\W(.*)|$)' % ELAB_PREFIX)


#########################
def blank_len(l):
    'Adds a safety factor to the length of a blank'
    return max(l + 3, int(l*1.2))

#########################
def text_dimension(text):
    'Returns the width and height of the given text'
    lines = text.split('\n')
    width = max(map(lambda x:len(x), lines))
    height = len(lines)
    return width,height

#########################
def create_blank_element(width, height, id):
    '''
    Creates an appropriate HTML text field for the specified width and
    height.  It creates a text input box for the width of 1, and a textarea
    otherwise.
    '''
    if height == 1:
        text = etree.Element('input')
        text.set('type', 'text')
        text.set('size', str(blank_len(width)))
        text.set('value', '{{%s}}' % id)
        texttype = 'input'
    else:
        text = etree.Element('textarea')
        text.set('cols', str(blank_len(width)))
        text.set('rows', str(height))
        # prevent this text from being reprocessed by other inline patterns
        text.text = AtomicString('{{%s}}' % id)
        texttype = 'textarea'
    return text,texttype

############################################################
class ELabExtension(markdown.Extension):

    #########################
    def __init__(self, configs):
        self.task = configs['task']
        self.lang = configs['lang']

    #########################
    def extendMarkdown(self, md, md_globals):
        self.md = md
        md.registerExtension(self)

        # Append a preprocessor
        preprocessor = ELabPreprocessor(self)
        preprocessor.md = md
        md.preprocessors.add('elab_preprocessor', preprocessor, '_begin')

        # Insert an inline pattern for text-based answer fields
        self.md.inlinePatterns.add(
                'elab_answerfield', AnswerFieldPattern(self), '<escape')

        # Insert an inline pattern for code segment placeholder
        self.md.inlinePatterns.add(
                'elab_codeseg', CodeSegPattern(self), '_end')

        # Insert an inline pattern for testcase placeholder
        self.md.inlinePatterns.add(
                'elab_testcase', TestCasePattern(self), '_end')

        # Insert an inline pattern for embedded media placeholder
        self.md.inlinePatterns.add(
                'elab_testcase', EmbeddedMediaPattern(self), '_end')

        # Insert an inline pattern for template tag
        self.md.inlinePatterns.add('elab_templatetag',
                TemplateTagPattern(md,
                    '({}){}({})'.format(
                        re.escape('{%'),
                        r'(.+?)',
                        re.escape('%}'))
                    ), '_begin')

        # Force use not-so-smart _emphasis_ because the 'smart' one seems a
        # little buggy
        self.md.inlinePatterns["emphasis2"] = \
            markdown.inlinepatterns.SimpleTagPattern(r'(_)(.+?)\2', 'em')

        # Get rid of the prettify treeprocessor as it sometimes messes up code segments
        # wrapped inside <pre>
        del self.md.treeprocessors["prettify"]

    #########################
    def reset(self):
        self.task.__init__()


############################################################
class ELabPreprocessor(markdown.preprocessors.Preprocessor):
    '''
    Preprocess e-labsheet commands of the form

        ::elab:<command> [parameters]

    e.g.,

        ::elab:begincode hidden=True
    '''

    #########################
    def __init__(self, elab):
        self.elab = elab

    #########################
    def run(self, lines):
        TEXT = 0; CODE = 1; TEST = 2 # available states
        state = TEXT
        task = self.elab.task
        start_line = 0

        parts = {}
        parts[TEXT] = []
        try:
            for lineno,line in enumerate(lines):
                (cmd,params) = self.checkTag(line)
                if cmd is not None:
                    if cmd == 'config':
                        exec('task.config(%s)' % params)
                    elif cmd == 'begincode':
                        if state is not TEXT:
                            raise ElabException("Unexpected 'begincode' statement")
                        state = CODE
                        start_line = lineno
                        parts[CODE] = []
                        codeSeg = eval("CodeSegment(task.markers,{})".format(params))
                    elif cmd == 'endcode':
                        if state is not CODE:
                            raise ElabException("Unexpected 'endcode' statement")
                        state = TEXT
                        codeSeg.makeSequence(parts[CODE],start_line)
                        parts[TEXT].append('%s %d' % 
                                (CODESEG_PLACEHOLDER, len(task.codesegs)))
                        task.addCodeSegment(codeSeg)
                    elif cmd == 'begintest':
                        if state is not TEXT:
                            raise ElabException("Unexpected 'begintest' statement")
                        state = TEST
                        parts[TEST] = []
                        testcase = eval("ExtractedTestCase({})".format(params))
                    elif cmd == 'endtest':
                        if state is not TEST:
                            raise ElabException("Unexpected 'endtest' statement")
                        state = TEXT
                        testcase.set_input(parts[TEST])
                        task.addTestCase(testcase)
                    elif cmd == 'blankline':
                        parts[state].append(params)
                    elif cmd == 'buildflags':
                        task.addBuildFlags(params)
                    elif cmd == 'runflags':
                        task.addRunFlags(params)
                    elif cmd == 'hide':
                        if state != CODE:
                            raise ElabException("Command '%s' must be inside a code segment" % cmd)
                        else:
                            parts[CODE].append(HiddenLine(params[1:]))
                    elif cmd == 'exclude':
                        if state != CODE:
                            raise ElabException("Command '%s' must be inside a code segment" % cmd)
                        else:
                            parts[CODE].append(ExcludedLine(params[1:]))
                    elif cmd == 'embed':
                        if state in [CODE,TEST]:
                            raise ElabException("Unexpected 'embed' statement")
                        else:
                            media = eval("EmbeddedMedia({})".format(params))
                            parts[TEXT].append('%s %d' % 
                                (EMBEDDED_MEDIA_PLACEHOLDER, len(task.embeddedMedia)))
                            task.embeddedMedia.append(media)
                    else:
                        raise ElabException("Unrecognized elab command '%s'" % cmd)
                    continue
                parts[state].append(line)
            lineno = 'EOF'
            if state is CODE:
                raise ElabException("'endcode' expected")
            elif state is TEST:
                raise ElabException("'endtest' expected")
        except Exception as e:
            if type(lineno) is int:
                lineno += 1
            if type(e) is SyntaxError:
                e = "Syntax error"
            if type(e) is ElabException:
                lineno = e.lineno if e.lineno is not None else lineno
            parts[TEXT].append("")
            parts[TEXT].append("<span style='color:red;'>*Error: Line %d: %s*</span>" % (lineno,e))
            parts[TEXT].append("")

        return parts[TEXT]

    #########################
    def checkTag(self,line):
        '''
        Checks whether this line is an e-labsheet tag.  It returns a command and
        an optional parameter string if a tag is found.  Otherwise None is
        returned.
        '''
        match = ELAB_TAG_RE.match(line)
        if match is None:
            return (None,None)
        return match.group(1), match.group(2)


############################################################
class CodeSegPattern(markdown.inlinepatterns.Pattern):

    #########################
    def __init__(self, elab):
        pattern = re.escape(CODESEG_PLACEHOLDER) + ' ([0-9]*)'
        markdown.inlinepatterns.Pattern.__init__(self, pattern)
        self.elab = elab
        self.highlighter = Highlighter(self.elab.lang)

    #########################
    @staticmethod
    def createLineNoElem(lineno):
        lineno_span = etree.Element('span')
        lineno_span.set('class', 'lineno')
        lineno_span.text = AtomicString('%2d: ' % lineno)
        return lineno_span

    #########################
    def handleMatch(self, m):
        # extract task ID from the code segment placeholder
        tid = int(m.group(2))

        # use the task ID to retrieve the code segment data
        codeseg = self.elab.task.codesegs[tid]
        if codeseg.hidden:
            return ''

        # the code segment will be wrapped inside the tags:
        # <fieldset><pre><code class="source">...</code></pre></fieldset>
        fs = etree.Element('fieldset')
        pre = etree.Element('pre')
        code = etree.Element('code')
        code.set('class', 'source')
        lineno = 1
        lineno_elem = self.createLineNoElem(lineno)
        for piece in codeseg:
            if codeseg.lineno and lineno_elem is not None:
                code.append(lineno_elem)
                lineno_elem = None

            if isinstance(piece,Blank):
                blank_id = BLANK_ID_PREFIX + str(piece.id)
                width,height = text_dimension(piece.rawAnswer())
                text,texttype = create_blank_element(width, height, blank_id)
                text.set('class', 'codeblank')
                text.set('name', blank_id)
                if (texttype == 'textarea'):
                    text.set('wrap', 'off')
            else:  # piece is a string, not a blank
                if isinstance(piece,HiddenLine):
                    text = None
                else:
                    if codeseg.highlight:
                        if codeseg.language is None:
                            text = self.highlighter.highlight(piece)
                        else:
                            text = Highlighter(codeseg.language).highlight(piece)
                    else:
                        text = piece

            # resulting 'text' from a highlighter is a list
            if type(text) is list:
                for x in text:
                    append_text_or_elem(code, x)
            elif text is not None:
                append_text_or_elem(code, text)

            # Excluded line is not followed by a new line, so add one
            if isinstance(piece,ExcludedLine):
                append_text_or_elem(code,"\n")

            if piece == '\n' or isinstance(piece,ExcludedLine):
                lineno += 1
                lineno_elem = self.createLineNoElem(lineno)

        pre.append(code)
        fs.append(pre)
        #xx = """
        #<fieldset><pre><code><span>name</span> = <span>x</span></code></pre></fieldset>"""
        #fs = etree.fromstring(xx)
        #etree.dump(fs)
        return fs

############################################################
class AnswerFieldPattern(markdown.inlinepatterns.Pattern):

    #########################
    def __init__(self, elab):
        self.task = elab.task
        begin,end = self.task.markers
        score_begin,score_end = self.task.score_markers
        self.score_re = re.compile('^' + re.escape(score_begin) +
                '([0-9][0-9]*)' + re.escape(score_end) + '(.*)',
                re.DOTALL)

        # Note the ? after the * for the shortest match possible
        # so that something like "{{one}} and {{two}}" will be interpreted as
        # two answer fields instead of one
        pattern = re.escape(begin) + '(.*?)' + re.escape(end)
        markdown.inlinepatterns.Pattern.__init__(self, pattern)

    #########################
    def handleMatch(self, m):
        ans = m.group(2)
        score = DEFAULT_SCORE
        score_match = self.score_re.match(ans)
        if score_match:
            score = int(score_match.group(1))
            ans = score_match.group(2)
        ans_id = BLANK_ID_PREFIX + str(self.task.addTextBlank(ans,score))
        width,height = text_dimension(ans)
        text,texttype = create_blank_element(width, height, ans_id)
        text.set('class', 'textblank')
        text.set('name', ans_id)
        return text

############################################################
class TestCasePattern(markdown.inlinepatterns.Pattern):

    #########################
    def __init__(self, elab):
        pattern = TESTCASE_PLACEHOLDER_PATTERN
        markdown.inlinepatterns.Pattern.__init__(self, pattern)
        self.elab = elab

    #########################
    def handleMatch(self, m):
        tid = int(m.group(2))
        pre = etree.Element('pre')
        pre.set('class', 'output')
        pre.text = '\n%s %d' % (TESTCASE_PLACEHOLDER,tid)
        return pre

############################################################
class EmbeddedMediaPattern(markdown.inlinepatterns.Pattern):

    #########################
    def __init__(self, elab):
        pattern = EMBEDDED_MEDIA_PLACEHOLDER_PATTERN
        markdown.inlinepatterns.Pattern.__init__(self, pattern)
        self.elab = elab

    #########################
    def handleMatch(self, m):
        mid = int(m.group(2))
        media = self.elab.task.embeddedMedia[mid]
        tag = etree.Element('elab-embed')
        tag.set('type', media.type)
        tag.set('media', media.media_id)
        tag.set('feedback', 'yes' if media.feedback else 'no')
        tag.text = "Embedded media not shown in this view"
        return tag

############################################################
class TemplateTagPattern(markdown.inlinepatterns.Pattern):

    #########################
    def __init__(self, md, pattern):
        markdown.inlinepatterns.Pattern.__init__(self, pattern, md)

    #########################
    def handleMatch(self, m):
        text = m.group(2) + m.group(3) + m.group(4)
        return self.markdown.htmlStash.store(text)
