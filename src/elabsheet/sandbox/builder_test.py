import os
import shutil
import unittest

from nose.tools import assert_equal, assert_true

from builders import JavaBuilder

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
TEST_TEMP = 'test-tmp/scratch'
TEST_SCRATCH_DIR = os.path.join(TEST_DIR,TEST_TEMP)

def setup():
    if not os.path.exists(TEST_SCRATCH_DIR):
        os.makedirs(TEST_SCRATCH_DIR)

def teardown():
    #shutil.rmtree(TEST_SCRATCH_DIR)
    pass

def test_java_builder_should_extract_information_from_source():
    source = """
// elab-source: mypackage/util/Test.java
something

// elab-source: Stuff.java
another thing

// elab-mainclass: mypackage.util.Test
"""

    source_info = JavaBuilder.extract_info(source)
    files = source_info['files']
    assert_equal(len(files),2)
    assert_equal(files[0][0],'mypackage/util/Test.java')
    assert_equal(files[1][0],'Stuff.java')
    assert_equal(source_info['main_class'], 'mypackage.util.Test')


def test_java_builder_should_extract_data_for_each_file_from_source():
    source_data1 = """code line1
code
code line3
"""
    source_data2 = """another code
coding
hello
"""
    source = """
// elab-source: mypackage/util/Test.java
""" + source_data1 + """// elab-source: Stuff.java
""" + source_data2

    source_info = JavaBuilder.extract_info(source)
    files = source_info['files']
    assert_equal(files[0][1],source_data1)
    assert_equal(files[1][1],source_data2)

def test_java_builder_should_infer_main_class_name_from_source():
    source = """
// elab-source:   mypackage/util/Test.java
something

// elab-source: Stuff.java
another thing
"""

    source_info = JavaBuilder.extract_info(source)
    files = source_info['files']
    assert_equal(len(files),2)
    assert_equal(source_info['main_class'], 'mypackage.util.Test')


