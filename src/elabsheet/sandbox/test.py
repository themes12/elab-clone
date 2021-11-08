import os
import shutil
import unittest

from nose.tools import assert_equal, assert_true

# setting DJANGO_SETTINGS_MODULE so that conf can access settings
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'elabsheet.settings'

from django.conf import settings

from .__init__ import Sandbox
from .builders import JavaBuilder

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
TEST_TEMP = 'test-tmp/scratch'
TEST_SCRATCH_DIR = os.path.join(TEST_DIR,TEST_TEMP)

def setup():
    if not os.path.exists(TEST_SCRATCH_DIR):
        os.makedirs(TEST_SCRATCH_DIR)

def teardown():
    #shutil.rmtree(TEST_SCRATCH_DIR)
    pass

class StubbedSource:
    def __init__(self,lang,body):
        self.language = lang
        self.body = body

def box_available():
    return os.name=='posix' and (not os.uname()[0].startswith('CYGWIN'))

def test_sandbox_should_evaluate_python_source():
    python_source_body = """
x = int(raw_input())
print x+100
"""
    python_source = StubbedSource('python', python_source_body)
    input_string = "100\n"

    sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=True)
    output_string = sandbox.evaluate(python_source,
                                     input_string=input_string)

    assert_equal(output_string,"200\n")


def test_sandbox_should_evaluate_python_source_without_box():
    python_source_body = """
x = int(raw_input())
print x+100
"""
    python_source = StubbedSource('python', python_source_body)
    input_string = "100\n"

    sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=False)
    output_string = sandbox.evaluate(python_source,
                                     input_string=input_string)

    assert_equal(output_string,"200\n")


def test_sandbox_should_evaluate_csharp_source():
    source_body = """
using System;

class MainClass
{
	public static void Main(string[] args)
	{
		int x = int.Parse(Console.ReadLine());
		Console.WriteLine("{0}",x+100);
	}
}
"""
    source = StubbedSource('csharp', source_body)
    input_string = "100\n"

    if box_available():
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=True)
    else:
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=False)
        
    output_string = sandbox.evaluate(source,
                                     input_string=input_string)

    assert_equal(output_string,"200\n")



def test_sandbox_should_produce_compiler_messages_for_csharp():
    source_body = """
using System;

class MainClass
{
	public static void Main(string[] args)
		int x = int.Parse(Console.ReadLine());
		Console.WriteLine("{0}",x+100);
	}
}
"""
    source = StubbedSource('csharp', source_body)
    input_string = "100\n"

    if box_available():
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=True)
    else:
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=False)
        
    sandbox.evaluate(source,
                     input_string=input_string)

    assert_true('rror' in sandbox.get_compiler_messages())



def test_sandbox_should_clean_scratch_dir():
    python_source_body = """
print 'hello world'
"""
    python_source = StubbedSource('python', python_source_body)
    input_string = ""

    sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=True)
    output_string = sandbox.evaluate(python_source,
                                     input_string=input_string)
    assert_equal(len(os.listdir(TEST_SCRATCH_DIR)),0)


def test_sandbox_should_only_clean_subdir_when_use_temp_subdir():
    python_source_body = """
print 'hello world'
"""
    python_source = StubbedSource('python', python_source_body)
    input_string = ""

    sandbox = Sandbox(TEST_SCRATCH_DIR, 
                      temp_subdir=True, clean_dir=True, use_box=True)

    # create a few files in TEST_SCRATCH_DIR
    tmp_dirname = os.path.join(TEST_SCRATCH_DIR,'newtemp')
    tmp_filename = os.path.join(TEST_SCRATCH_DIR,'newfile')
    os.mkdir(tmp_dirname)
    open(tmp_filename,"w").close()
    
    output_string = sandbox.evaluate(python_source,
                                     input_string=input_string)
    
    assert_equal(len(os.listdir(TEST_SCRATCH_DIR)),2)

    os.rmdir(tmp_dirname)
    os.remove(tmp_filename)


def test_sandbox_should_return_to_the_original_dir():
    # this doesn't seem to be a problem when running in python, it
    # seems that python interprete changes dir back to the original
    # automatically after it finishes.  But this may be an issue on
    # other languages.  (Especially, when the sandbox cleans the dir.)
    original_cwd = os.getcwd()

    python_source_body = """
import os

os.chdir("/tmp")
dir_listing = os.listdir(".")
for f in dir_listing:
  print f
"""
    python_source = StubbedSource('python', python_source_body)
    input_string = ""

    sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=True)
    output_string = sandbox.evaluate(python_source,
                                     input_string=input_string)

    assert_equal(os.getcwd(),original_cwd)
    

def test_sandbox_should_kill_too_long_process():
    python_source_body = """
import os

while True:
  pass
""" 
    python_source = StubbedSource('python', python_source_body)
    input_string = ""

    sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=True)
    output_string = sandbox.evaluate(python_source,
                                     input_string=input_string)

    assert_equal(output_string,"")


def test_sandbox_should_kill_too_long_csharp_process():
    source_body = """
using System;

class MainClass
{
	public static void Main(string[] args)
	{
          while(true) ;                
	}
}
""" 
    source = StubbedSource('csharp', source_body)
    input_string = ""

    sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=True)
    output_string = sandbox.evaluate(source,
                                     input_string=input_string)

    assert_equal(output_string,"")


def test_sandbox_should_not_allow_file_manipulation():
    python_source_body = """
import os

os.system("rm source.py")
os.system("echo HELLO > mynewfile")
""" 
    python_source = StubbedSource('python', python_source_body)
    input_string = ""

    sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=False, use_box=True)
    output_string = sandbox.evaluate(python_source,
                                     input_string=input_string)

    assert_equal(os.path.exists(os.path.join(TEST_SCRATCH_DIR,"source.py")),
                 True)
    assert_equal(os.path.exists(os.path.join(TEST_SCRATCH_DIR,"mynewfile")),
                 False)

    # clean it for the next tests
    sandbox.clean_scratch_dir()
                                

def test_sandbox_should_produces_output_file():
    python_source_body = """
x = int(raw_input())
print x+100
"""
    python_source = StubbedSource('python', python_source_body)
    input_string = "100\n"

    output_filename = os.path.join(TEST_SCRATCH_DIR,"output.txt")
    sandbox = Sandbox(TEST_SCRATCH_DIR, use_box=True)
    sandbox.evaluate(python_source,
                     input_string=input_string,
                     output_filename=output_filename)

    assert_equal(os.path.exists(output_filename), True)
    
    output_string = open(output_filename).read()
    assert_equal(output_string,"200\n")

    # clean it for the next tests
    sandbox.clean_scratch_dir()

def test_sandbox_should_evaluate_python_source_with_tempdir():
    python_source_body = """
x = int(raw_input())
print x+100
"""
    python_source = StubbedSource('python', python_source_body)
    input_string = "100\n"

    old_file_count = len(os.listdir(TEST_SCRATCH_DIR))

    sandbox = Sandbox(TEST_SCRATCH_DIR, 
                      temp_subdir=True, 
                      clean_dir=False,
                      use_box=True)
    output_string = sandbox.evaluate(python_source,
                                     input_string=input_string)

    assert_equal(output_string,"200\n")
    assert_equal(len(os.listdir(TEST_SCRATCH_DIR)),old_file_count+1)

    sandbox.clean_scratch_dir()

def test_sandbox_should_clean_scratch_dir_with_tempdir():
    python_source_body = """
print 'hello world'
"""
    python_source = StubbedSource('python', python_source_body)
    input_string = ""

    sandbox = Sandbox(TEST_SCRATCH_DIR, 
                      temp_subdir=True, 
                      clean_dir=True, 
                      use_box=True)
    output_string = sandbox.evaluate(python_source,
                                     input_string=input_string)
    assert_equal(len(os.listdir(TEST_SCRATCH_DIR)),0)


def test_sandbox_should_evaluate_java_source():
    source_body = """
// elab-source: Sum.java
import java.util.Scanner;

public class Sum {

	public static void main(String [] args) {
		Scanner s = new Scanner(System.in);
		int i = s.nextInt();
		System.out.println("" + (i+100));
	}
}
"""
    source = StubbedSource('java', source_body)
    input_string = "100\n"

    if box_available():
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=True)
    else:
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=False)
        
    output_string = sandbox.evaluate(source,
                                     input_string=input_string)

    assert_equal(output_string.strip(),"200")


def test_sandbox_should_evaluate_java_source_with_many_files():
    source_body = """
// elab-source: SumMain.java
import java.util.Scanner;
import mypackage.Sum;

public class SumMain {

	public static void main(String [] args) {
		Scanner s = new Scanner(System.in);
		int i = s.nextInt();

                Sum sum = new Sum();
                sum.doSum(i);
	}
}

// elab-source: mypackage/Sum.java
package mypackage;

public class Sum {

        public void doSum(int n) {
		System.out.println("" + (n+100));
	}
}

"""
    source = StubbedSource('java', source_body)
    input_string = "100\n"

    if box_available():
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=True)
    else:
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=False)
        
    output_string = sandbox.evaluate(source,
                                     input_string=input_string)

    assert_equal(output_string.strip(),"200")


def test_sandbox_should_evaluate_c_source():
    source_body = """
#include <stdio.h>

main()
{
  int a;
  scanf("%d",&a);
  printf("%d\\n",a+100);
}
"""
    source = StubbedSource('c', source_body)
    input_string = "100\n"

    if box_available():
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=True)
    else:
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=False)
        
    output_string = sandbox.evaluate(source,
                                     input_string=input_string)

    assert_equal(output_string.strip(),"200")


def test_sandbox_should_evaluate_loop_c_source():
    source_body = """
#include <stdio.h>

main()
{
  int a;
  scanf("%d",&a);
  while(1)
    ;
  printf("%d\\n",a+100);
}
"""
    source = StubbedSource('c', source_body)
    input_string = "100\n"

    if box_available():
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=True)
    else:
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=False)
        
    output_string = sandbox.evaluate(source,
                                     input_string=input_string)

    assert_equal(output_string.strip(),"")


def test_sandbox_should_evaluate_cpp_source():
    source_body = """
#include <cstdio>

main()
{
  int a;
  scanf("%d",&a);
  for(int i=0; i<100; i++)
    a++;
  printf("%d\\n",a);
}
"""
    source = StubbedSource('c++', source_body)
    input_string = "100\n"

    if box_available():
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=True)
    else:
        sandbox = Sandbox(TEST_SCRATCH_DIR, clean_dir=True, use_box=False)
        
    output_string = sandbox.evaluate(source,
                                     input_string=input_string)

    assert_equal(output_string.strip(),"200")


