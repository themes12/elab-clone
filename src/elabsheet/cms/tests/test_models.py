from django.test import TestCase
from cms.models import Task

######################
MD_PYTHON3_WITH_TEST_CASES = """\
Test Cases
==========

::elab:begincode language="python3"
x = int(input())
y = int(input())
print(x+y)
::elab:endcode

::elab:begintest
8
4
::elab:endtest

::elab:begintest
2
5
::elab:endtest"""

######################
MD_CODE_BLANKS_BLOCK = """\
Code Blanks - Block
===================

::elab:begincode language="python3",blank=True
x = int(input())
y = int(input())
print(x+y)
::elab:endcode
"""

SOL_CODE_BLANKS_BLOCK = """\
x = int(input())
y = int(input())
print(x+y)
"""

SUB_CODE_BLANKS_BLOCK = {0:"my statement"}

OUT_CODE_BLANKS_BLOCK = """\
my statement
"""

######################
MD_CODE_BLANKS_INLINE = """\
Code Blanks - Inline
===================

::elab:begincode language="python3"
x = int({{input()}})
y = int(input())
print({{x+y}})
::elab:endcode
"""

SOL_CODE_BLANKS_INLINE = """\
x = int(input())
y = int(input())
print(x+y)
"""

SUB_CODE_BLANKS_INLINE = {
    0 : "replace0",
    1 : "replace1",
}

OUT_CODE_BLANKS_INLINE = """\
x = int(replace0)
y = int(input())
print(replace1)
"""

######################
MD_CODE_BLANKS_MULTILINE = """\
Code Blanks - Inline
===================

::elab:begincode language="python3"
{{x = int(input())}}
{{y = int(input())}}
print(x+y)
::elab:endcode
"""

SOL_CODE_BLANKS_MULTILINE = """\
x = int(input())
y = int(input())
print(x+y)
"""

SUB_CODE_BLANKS_MULTILINE = {
    0 : """\
line1
line2
  line3""",
}

OUT_CODE_BLANKS_MULTILINE = """\
line1
line2
  line3
print(x+y)
"""

######################
MD_CODE_BLANKS_MULTILINE_INDENT = """\
Code Blanks - Inline
===================

::elab:begincode language="python3"
def read_input():
    {{x = int(input())  }}
    {{y = int(input())  }}
    {{return x,y        }}

x,y = read_input()
print(x+y)
::elab:endcode
"""

SOL_CODE_BLANKS_MULTILINE_INDENT = """\
def read_input():
    x = int(input())  
    y = int(input())  
    return x,y        

x,y = read_input()
print(x+y)
"""

SUB_CODE_BLANKS_MULTILINE_INDENT = {
    0 : """\
line1
line2
  line3""",
}

OUT_CODE_BLANKS_MULTILINE_INDENT = """\
def read_input():
    line1
    line2
      line3

x,y = read_input()
print(x+y)
"""

class TestTestCase(TestCase):

    def test_testcase1(self):
        task = Task(name="Dummy",source=MD_PYTHON3_WITH_TEST_CASES,language="python3")
        task.save()
        sols = task.testcases
        self.assertEqual(sols[0]['output'],"12\n")
        self.assertEqual(sols[1]['output'],"7\n")


class TaskModelTestCase(TestCase):

    def setUp(self):
        task = Task(name="Test",source=MD_PYTHON3_WITH_TEST_CASES,language="python3")
        task.save()
        self.task_id = task.id

    def test_task_count(self):
        tasks = Task.objects.all()
        self.assertEqual(tasks.count(),1)

    def test_read_task(self):
        task = Task.objects.get(id=self.task_id)
        self.assertEqual(task.name,"Test")
        self.assertEqual(task.source,MD_PYTHON3_WITH_TEST_CASES)
        self.assertEqual(task.language,"python3")


class TaskModelBlank(TestCase):

    def setUp(self):
        task = Task(name="Test",source=MD_CODE_BLANKS_BLOCK,language="python3")
        task.save()
        self.id_code_blanks_block = task.id

        task = Task(name="Test",source=MD_CODE_BLANKS_INLINE,language="python3")
        task.save()
        self.id_code_blanks_inline = task.id

        task = Task(name="Test",source=MD_CODE_BLANKS_MULTILINE,language="python3")
        task.save()
        self.id_code_blanks_multiline = task.id

        task = Task(name="Test",
                source=MD_CODE_BLANKS_MULTILINE_INDENT,
                language="python3")
        task.save()
        self.id_code_blanks_multiline_indent = task.id

    def test_code_blanks_block(self):
        task = Task.objects.get(id=self.id_code_blanks_block)
        self.assertEqual(
                task.code.dump_solution(),
                SOL_CODE_BLANKS_BLOCK)
        self.assertEqual(
                task.code.dump(SUB_CODE_BLANKS_BLOCK),
                OUT_CODE_BLANKS_BLOCK)

    def test_code_blanks_inline(self):
        task = Task.objects.get(id=self.id_code_blanks_inline)
        self.assertEqual(
                task.code.dump_solution(),
                SOL_CODE_BLANKS_INLINE)
        self.assertEqual(
                task.code.dump(SUB_CODE_BLANKS_INLINE),
                OUT_CODE_BLANKS_INLINE)

    def test_code_blanks_multiline(self):
        task = Task.objects.get(id=self.id_code_blanks_multiline)
        self.assertEqual(
                task.code.dump_solution(),
                SOL_CODE_BLANKS_MULTILINE)
        self.assertEqual(
                task.code.dump(SUB_CODE_BLANKS_MULTILINE),
                OUT_CODE_BLANKS_MULTILINE)

    def test_code_blanks_multiline_indent(self):
        task = Task.objects.get(id=self.id_code_blanks_multiline_indent)
        self.assertEqual(
                task.code.dump_solution(),
                SOL_CODE_BLANKS_MULTILINE_INDENT)
        self.assertEqual(
                task.code.dump(SUB_CODE_BLANKS_MULTILINE_INDENT),
                OUT_CODE_BLANKS_MULTILINE_INDENT)
