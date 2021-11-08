import os
from django.test import TestCase
from cms.models import Task

TEST_DATA_DIR = "cms/tests/test-data"

######################
MD_TEMPLATE_TAG_ESCAPE = """\
Source with template tags
=========================
{% load static %}

{% load static %}
"""

######################
HTML_TEMPLATE_TAG_ESCAPE = """\
Source with template tags
=========================
{% load static %}

{% load static %}
"""


######################

def task_from_file(testcase,lang):
    """Create Task object from the given Markdown source file"""
    infile = os.path.join(TEST_DATA_DIR,testcase+".md")
    md = open(infile).read()
    task = Task(name="Output generator",source=md,language=lang)
    task.save()
    return task


class HtmlGenerationTestCase(TestCase):

    def prepare_output(self,testcase,lang):
        """Generate HTML template output for the given Markdown source file"""
        task = task_from_file(testcase,lang)
        outfile = os.path.join(TEST_DATA_DIR,testcase+".html")
        print(f"Saving output to {outfile}, using language '{lang}'")
        f = open(outfile,"w")
        f.write(task.html_template)
        f.close()

    def check_html_generation(self,testcase,lang):
        infile = os.path.join(TEST_DATA_DIR,testcase+".md")
        outfile = os.path.join(TEST_DATA_DIR,testcase+".html")
        md = open(infile).read()
        html = open(outfile).read()
        task = Task(name="Empty",source=md,language=lang)
        task.save()
        self.assertEqual(task.html_template,html)

    def test_dummy(self):
        """A dummy test to prepare output for test data.
        Please comment out during actual test."""
    #    self.prepare_output("simple-header","plaintext")
    #    self.prepare_output("python-code-nohighlight","plaintext")
    #    self.prepare_output("python-code-highlight","plaintext")
    #    self.prepare_output("code-blanks","plaintext")
    #    self.prepare_output("code-aligned-blanks","plaintext")
    #    self.prepare_output("text-blanks","plaintext")
    #    self.prepare_output("text-multiline-blanks","plaintext")
    #    self.prepare_output("templatetag-escape","plaintext")
    #    self.prepare_output("embedded-youtube","plaintext")
    #    self.prepare_output("utf8-source","plaintext")

    def test_task_simple_header(self):
        self.check_html_generation("simple-header","plaintext")

    def test_task_python_code_nohighlight(self):
        self.check_html_generation("python-code-nohighlight","plaintext")

    def test_task_python_code_highlight(self):
        self.check_html_generation("python-code-highlight","plaintext")

    def test_task_code_blanks(self):
        self.check_html_generation("code-blanks","plaintext")

    def test_task_code_aligned_blanks(self):
        self.check_html_generation("code-aligned-blanks","plaintext")

    def test_task_text_blanks(self):
        self.check_html_generation("text-blanks","plaintext")

    def test_task_text_multiline_blanks(self):
        self.check_html_generation("text-multiline-blanks","plaintext")

    def test_task_templatetag_escape(self):
        self.check_html_generation("text-multiline-blanks","plaintext")

    def test_task_embedded_youtube(self):
        self.check_html_generation("embedded-youtube","plaintext")

    def test_task_utf8_source(self):
        self.check_html_generation("utf8-source","plaintext")
