import sys
import re
import codecs
import markdown
from . import mdx_elabsheet, mdx_mathjax
from .elab import ExtractedTask

############################################################
def process_markdown_source(text,lang):
    lines = []
    for line in text.replace('\r','').split('\n'):
        # We put a 'blank-line' placeholder at every blank line to prevent
        # Markdown from getting rid of two consecutive lines.  These
        # placeholders will be replaced by blank lines later in the
        # preprocessor
        if re.match(r'^\s*$', line):
            lines.append(mdx_elabsheet.BLANKLINE_PLACEHOLDER+line)
        else:
            lines.append(line)

    # Add ^M at the end of this line
    # TODO: Find out why this is needed
    #text = '\r\n'.join(lines)
    text = '\n'.join(lines)

    task = ExtractedTask()
    md = markdown.Markdown()
    mdx_elabsheet.ELabExtension(
            {'task':task,'lang':lang}
        ).extendMarkdown(md, markdown.__dict__)

    mdx_mathjax.MathJaxExtension().extendMarkdown(md, markdown.__dict__)

    html = md.convert(text)
    code = task.getCode()
    tests = task.getTestCases()
    textBlanks = task.getTextBlanks()
    return html,code,tests,textBlanks

############################################################
def insert_test_dialog(html,dialogs):
    result = []
    for line in html.split('\n'):
        match = mdx_elabsheet.TESTCASE_PLACEHOLDER_RE.match(line)
        if match:
            tid = int(match.group(1))
            dialog = dialogs[tid]
            line = mdx_elabsheet.TESTCASE_PLACEHOLDER_RE.sub(dialog, line, count = 1)
        result.append(line)
    return '\n'.join(result)

#
# run this code if not loaded as module
#
if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: python {} <input> <output> <lang>'.format(sys.argv[0]))
        sys.exit(1)

    input = codecs.open(sys.argv[1], mode='r', encoding='utf8')
    text = input.read()
    input.close()
    html,code,tests,textBlanks = process_markdown_source(text,sys.argv[3])

    out = codecs.open(sys.argv[2], 'w', encoding='utf-8')
    #print('------------ HTML Template -----------------',file=out)
    print(html,file=out)
    #print('------------ Original Code -----------------',file=out)
    #print(code.dump(),file=out)
    #print('------------ Test Case(s) -----------------',file=out)
    #print(tests,file=out)
    #print(textBlanks)
    out.close()

