#from cgi import escape
from html import escape
from pygments import lexers
from pygments import token
from pygments.formatters import HtmlFormatter
from markdown.util import etree,AtomicString
from sandbox.builders import LEXER_CLASS_MAP

def append_text_or_elem(dom,text_or_elem):
    '''Append a text or a DOM element at the end of a given DOM element
    >>> from markdown.util import etree,AtomicString
    >>> p = etree.Element('p')
    >>> span = etree.Element('span')
    >>> span.text = 'one'
    >>> append_text_or_elem(p, 'two')
    >>> append_text_or_elem(p, span)
    >>> append_text_or_elem(p, 'three')
    >>> etree.dump(p)
    <p>two<span>one</span>three</p>
    >>> isinstance(p.text, AtomicString)
    True
    >>> isinstance(span.tail, AtomicString)
    True
    '''

    # First, determine whether the to-be-appended element is an actual DOM
    # element
    if etree.iselement(text_or_elem):
        dom.append(text_or_elem)  # this is an actual element
    else:
        # what to be appended is a text

        # check if this DOM element already has a child
        clist = dom.getchildren()
        if len(clist) > 0:
            # then attach the text at the end of the last child's tail
            lastChild = clist[-1]
            if lastChild.tail is None:
                lastChild.tail = text_or_elem
            else:
                lastChild.tail += text_or_elem
            # make it atomic so that it's no further processed
            lastChild.tail = AtomicString(lastChild.tail)
        else:
            # if not, attach the text as the 'text' part of this element
            if dom.text is None:
                dom.text = text_or_elem
            else:
                dom.text += text_or_elem
            # make it atomic so that it's no further processed
            dom.text = AtomicString(dom.text)


def getclass(token_dict, ttype):
    'Returns an appropriate css classname for the given token type.'
    getcls = token_dict.get
    while True:
        cls = getcls(ttype)
        if cls: break
        ttype = ttype.parent
        if ttype is None: break
    return cls

class Highlighter():
    def __init__(self, language):
        self.formatter = HtmlFormatter()
        self.lexer = None
        if language in LEXER_CLASS_MAP.keys():
            lexer_class = LEXER_CLASS_MAP[language] 
            if lexer_class is not None:
                self.lexer = lexer_class()
        else:
            try:
                self.lexer = lexers.get_lexer_by_name(language)
            except lexers.ClassNotFound:
                pass

    def highlight(self,code):
        'Returns a list of DOM objects representing highlighted code.'
        if not self.lexer or code.strip() == '':
            return [code]
        doms = []
        for ttype,text in self.lexer.get_tokens(code):
            # C-lexer acts quite strangely.  It often returns empty
            # strings after ; and }, so we detect and ignore them
            if text == '': continue
            cls = getclass(self.formatter.ttype2class, ttype)
            if cls: # there is a class defined for this token type
                # make a span element with appropriate 'class' attribute
                elem = etree.Element('span')
                elem.set('class', cls)
                elem.text = AtomicString(text)
                if elem.text.endswith('\n'):
                    elem.text = AtomicString(elem.text[:-1])
                doms.append(elem)
            else: # just append the text as-is
                doms.append(text)

        # get rid of unnecessary newline token at the end
        if isinstance(doms[-1],str) and doms[-1].strip() == '':
            return doms[:-1]
        else:
            return doms


#############################################
if __name__ == '__main__':
    import sys

    top = etree.Element('pre')
    code = 'sum = 0\nfor x in range(10):\n    sum += x\nprint sum'
    #code = '\n'
    ht = Highlighter('python')
    for x in ht.highlight(code):
        append_text_or_elem(top, x)
    print(etree.dump(top))
