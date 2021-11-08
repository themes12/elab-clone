import os
import stat
import sys
import re
from pygments import lexers
from django.conf import settings

# A builder for each language is responsible for building an excutable
# given a sourcecode (as string).  Each builder should support: 
#
# * build(source, scratch_dir): build source and return executable
#   filename (callable from box or shell), can write anything
#   (including output executable) to directory scratch_dir.
#

# This dictionary is to be populated by builder registration and will later be
# used by CMS's syntax highlighter
LEXER_CLASS_MAP = { }

class UnknownLanguage(Exception):
    pass

class BuildError(Exception):
    def __init__(self, error_messages=None):
        self.error_messages = error_messages


class BuilderFactory:
    registered_builders = {}
    source_extensions = {}
    extension_map = {}

    @classmethod
    def register(cls, language, ext, builder, lexer=None):
        """
        Registers a builder for language with source extension ext.
        """
        cls.registered_builders[language] = builder
        cls.source_extensions[language] = ext
        cls.extension_map[ext] = language
        LEXER_CLASS_MAP[language] = lexer

    @classmethod
    def get(cls, language):
        if language in cls.registered_builders:
            builder_cls = cls.registered_builders[language]
            return builder_cls()
        else:
            raise UnknownLanguage()

    @classmethod
    def get_by_ext(cls, ext):
        if ext in cls.extension_map:
            return cls.get(cls.extension_map[ext])
        else:
            raise UnknownLanguage()

    @classmethod
    def get_languages(cls):
        return cls.registered_builders.keys()

    @classmethod
    def get_languages_with_extensions(cls):
        return [(x,cls.source_extensions[x]) 
                for x in cls.registered_builders.keys()]


class PythonBuilder:

    def python_executable(self):
        try:
            return settings.BUILDERS['python']
        except:
            import subprocess
            return subprocess.getoutput('which python2.7')

    def build(self, source, scratch_dir, flags):
        """
        Saves source as (scratch_dir)/source.py.

        Returns a command-line that calls a python interpreter
        (obtained from sys.executable) with the source file.

        """
        python_source_filename = os.path.join(scratch_dir, "source.py")
        
        pfile = open(python_source_filename,"w")
        pfile.write(source)
        pfile.close()

        executable_filename = "%s %s %s" % (
                self.python_executable(),
                flags['run'],
                python_source_filename,
                )

        return executable_filename

    def get_compiler_messages(self):
        return ''

BuilderFactory.register('python', 'py', PythonBuilder, lexers.PythonLexer)
BuilderFactory.register('python2', 'py', PythonBuilder, lexers.PythonLexer)


class Python3Builder(PythonBuilder):
    def python_executable(self):
        try:
            return settings.BUILDERS['python3']
        except:
            import subprocess
            return subprocess.getoutput('which python3.6')

BuilderFactory.register('python3', 'py', Python3Builder, lexers.Python3Lexer)


def cygpath(fn):
    """
    Converts a unix-based file/path name on Cygwin into the corresponding
    windows-based file/path name.
    """
    f = os.popen('cygpath -w ' + fn, 'r')
    ret = f.read().rstrip()
    f.close()
    return ret


class CSharpBuilder:
    """
    Builds C# executable.  It works differently on MS Windows with
    Cygwin (determined by os.uname), MS Windows (os.name='nt') and
    Linux (os.name='posix).

    - For Linux, it uses gmcs (from Mono) to build a .net assembly,
      then calls 'mono' to execute it.  (If you only execute that
      'source.exe', there'll be a problem with setgid and
      binfmt-support.)
    - For Windows, it calls 'csc' to compile and just call the
      executable.  
    - For Cygwin, it calls 'csc' with all paths translated to Windows'
      paths.
    """

    def read_compiler_messages(self, filename):
        try:
            self.compiler_messages = open(filename).read()
        except:
            self.compiler_messages = ''

    def build(self, source, scratch_dir, flags):
        source_filename = os.path.join(scratch_dir, "source.cs")
        executable_filename = os.path.join(scratch_dir, "source.exe")
        message_filename = os.path.join(scratch_dir, "error.msg")
        
        source_file = open(source_filename,"w")
        source_file.write(source)
        source_file.close()

        if os.name=='nt':
            # for windows
            os.system("csc -lib:%s %s -out:%s %s > %s" % (
                scratch_dir,
                flags['build'],
                executable_filename, 
                source_filename,
                message_filename))

            self.read_compiler_messages(message_filename)
            return executable_filename

        elif os.uname()[0].startswith('CYGWIN'):
            # for cygwin
            os.system("csc -lib:%s %s -out:'%s' '%s'> '%s'" % (
                scratch_dir,
                flags['build'],
                cygpath(executable_filename),
                cygpath(source_filename),
                cygpath(message_filename)))

            self.read_compiler_messages(message_filename)
            return executable_filename

        elif os.name=='posix':
            # for posix (or linux)
            os.system("gmcs -lib:%s %s %s -out:%s > %s 2>&1" % (
                scratch_dir,
                flags['build'],
                source_filename, 
                executable_filename,
                message_filename))

            self.read_compiler_messages(message_filename)
            mono_path = os.popen("which mono").read().strip()
            return "%s %s %s" % (mono_path, flags['run'], executable_filename)

        raise BuildError("Don't know how to build")

    def get_compiler_messages(self):
        return self.compiler_messages

BuilderFactory.register('csharp', 'cs', CSharpBuilder, lexers.CSharpLexer)

class JavaBuilder:
    """
    Builds java sources.  It supports many source files and lets the
    user specify the main class to be called. It can also infer class
    name from the first source file name.

    There are two ways to include many source files for Java.

    1. Inside source field of Task.  (This is required.)

      Users must specify the source file names in the source by
      placing the following options (as comments) inside the
      elab::begincode - elab::endcode tags.
    
        * Specifying source file name:

        // elab-source: filename (with path)

        * Specifying main class:

        // elab-mainclass:  mainclass.Name

      The source field in task shall be broken into many source files
      at places where the elab-source options are.  The content before
      the first option is discarded.

      If main class is not specify, the name is derived from the first
      source filename.

    2. As Task supplements.

      Users can also add more related source files as the task
      supplements.  All files should be compressed (using zip or gzip)
      so that to save the original path and file names.  The files
      will be extracted to the sand box directory when the program
      gets compiled and executed.  Then, JavaBuilder will search for
      all files with .java extension and compile them.

    Issues 
    ------ 

    Currently there seems to be some problem with sun java 6 when
    running under box as a different user with set-uid bit on.  The
    jvm complains that it can't find the required shared library.
    Running under normal box works fine.

    """
    @staticmethod
    def class_name_from_filename(filename):
        """
        >>> JavaBuilder.class_name_from_filename('hello/world/Baby.java')
        'hello.world.Baby

        >>> JavaBuilder.class_name_from_filename('hello\\World.java')
        'hello.World'

        >>> JavaBuilder.class_name_from_filename('JavaTest.java')
        'JavaTest'
        """
        f = filename.partition('.')[0]
        return f.replace('/','.').replace('\\','.')

    @staticmethod
    def extract_info(source):
        """
        Extracts files and main class information from source.

        Returns a dictionary with two keys:
        1. 'files' is a list of tuple (file_name, body)
        2. 'main_class' is string containing the main class name
        """
        
        import re

        source_regex = re.compile(r'//\s*elab-source:\s*(\S+)\s*')
        main_regex = re.compile(r'//\s*elab-mainclass:\s*(\S+)\s*')

        files = []
        current_filename = ''
        main_class = ''
        body = ''
        for line in source.splitlines(True):
            source_res = source_regex.match(line)
            if source_res:
                # clear old body
                if current_filename!='':
                    files.append((current_filename,body))

                body = ''
                current_filename = source_res.group(1)
                current_filename = current_filename.replace('\\','/')
                continue

            main_res = main_regex.match(line)
            if main_res:
                main_class = main_res.group(1)
                continue

            body = body + line

        # clear last body
        if current_filename!='':
            files.append((current_filename,body))

        # auto infer main_class
        if main_class=='':
            if len(files)!=0:
                main_class = JavaBuilder.class_name_from_filename(files[0][0])

        return {'files': files,
                'main_class': main_class}

    def read_compiler_messages(self, filename):
        try:
            self.compiler_messages = open(filename).read()
        except:
            self.compiler_messages = ''

    def save_source_files(self,scratch_dir,files):
        for fname, body in files:
            # only allow relative paths
            if fname[0]!='/':
                abs_fname = os.path.join(scratch_dir, fname)
                path = os.path.split(abs_fname)[0]
                if not os.path.exists(path):
                    os.makedirs(path)
                try:
                    fp = open(abs_fname,"w")
                    fp.write(body)
                    fp.close()
                except IOError:
                    pass

    @staticmethod
    def find_all_java_files(path):
        flist = []
        for r, dirs, files in os.walk(path):
            for fname in files:
                if os.path.splitext(fname)[1]=='.java':
                    flist.append(os.path.join(r,fname))
        return flist

    def build_for_nt(self, scratch_dir, sources, message_filename, flags):
        initial_dir = os.getcwd()
        os.chdir(scratch_dir)
        os.system("javac %s %s > %s" % (flags['build'], sources, message_filename))
        os.chdir(initial_dir)

    def build_for_cygwin(self, scratch_dir, sources, message_filename, flags):
        initial_dir = os.getcwd()
        new_sources = ' '.join([("'%s'" % cygpath(fname)) 
                                for fname in sources.split(' ')])
        os.chdir(scratch_dir)
        os.system("javac %s %s > '%s'" % (flags['build'], new_sources, 
                                       cygpath(message_filename)))
        os.chdir(initial_dir)

    def build_for_posix(self, scratch_dir, sources, message_filename, flags):
        initial_dir = os.getcwd()
        os.chdir(scratch_dir)
        os.system("javac %s %s > %s 2>&1" % (flags['build'], sources, message_filename))
        os.chdir(initial_dir)

    def get_compiler_messages(self):
        return self.compiler_messages

    def build(self, source, scratch_dir, flags):
        sinfo = JavaBuilder.extract_info(source)
        self.save_source_files(scratch_dir, sinfo['files'])
        main_class = sinfo['main_class']
        executable_filename = os.path.join(scratch_dir, "run")
        message_filename = os.path.join(scratch_dir, "error.msg")

        # find all *.java files
        source_list = JavaBuilder.find_all_java_files(scratch_dir)
        source_list_str = ' '.join(source_list)

        java_options = "-cp . -Xmx32m"

        if os.name=='nt':
            # windows
            self.build_for_nt(scratch_dir, 
                              source_list_str, 
                              message_filename,
                              flags)
            self.read_compiler_messages(message_filename)
            return "java %s %s %s" % (java_options, flags['run'], main_class)

        elif os.uname()[0].startswith('CYGWIN'):
            # cygwin
            self.build_for_cygwin(scratch_dir, 
                                  source_list_str, 
                                  message_filename,
                                  flags)
            self.read_compiler_messages(message_filename)
            return "java %s %s %s" % (java_options, flags['run'], main_class)

        elif os.name=='posix':
            # linux (or other posix)
            self.build_for_posix(scratch_dir, 
                                 source_list_str, 
                                 message_filename,
                                 flags)
            self.read_compiler_messages(message_filename)

            # have to create a script for doing that for otherwise the
            # java parameters may interfere with box's parameters.
            java_executable = os.popen("which java").read().strip()
            ex_fp = open(executable_filename,"w")
            ex_fp.write("#!/bin/sh\n")
            ex_fp.write("%s %s %s %s $*\n" % (java_executable, 
                                        java_options,
                                        flags['run'],
                                        main_class))
            ex_fp.close()
            os.system("chmod a+x %s" % executable_filename)
            return executable_filename

        raise BuildError("Don't know how to build")

BuilderFactory.register('java', 'java', JavaBuilder, lexers.JavaLexer)

class CBuilder:
    """
    Builds C executable using gcc.
    """

    def compiler_command(self):
        return 'gcc'
    def source_extension(self):
        return 'c'

    def read_compiler_messages(self, filename):
        try:
            self.compiler_messages = open(filename).read()
        except:
            self.compiler_messages = ''

    def build(self, source, scratch_dir, flags):
        source_filename = os.path.join(scratch_dir, 
                                       "source.%s" % 
                                       (self.source_extension()))
        executable_filename = os.path.join(scratch_dir, "a.out")
        message_filename = os.path.join(scratch_dir, "error.msg")
        
        source_file = open(source_filename,"w")
        source_file.write(source)
        source_file.close()

        if os.name=='nt':
            # for windows
            raise BuildError("Not implemented")

        elif os.uname()[0].startswith('CYGWIN'):
            # for cygwin
            os.system("%s %s -o '%s' '%s' 2> '%s' -lm" % (
                    self.compiler_command(),
                    flags['build'],
                    cygpath(executable_filename),
                    cygpath(source_filename),
                    cygpath(message_filename)))

            self.read_compiler_messages(message_filename)
            return executable_filename

        elif os.name=='posix':
            # for posix (or linux)
            os.system("%s %s -o %s %s > %s 2>&1 -lm" % (
                    self.compiler_command(),
                    source_filename, 
                    executable_filename,
                    flags['build'],
                    message_filename))
            
            self.read_compiler_messages(message_filename)
            return executable_filename

        raise BuildError("Don't know how to build")

    def get_compiler_messages(self):
        return self.compiler_messages

BuilderFactory.register('c', 'c', CBuilder, lexers.CLexer)

class CppBuilder(CBuilder):
    """
    Builds C++ executable using g++.  It mainly uses CBuilder, it only
    changes the compiler command.
    """

    def compiler_command(self):
        return 'g++'
    def source_extension(self):
        return 'cpp'

BuilderFactory.register('c++', 'cpp', CppBuilder, lexers.CppLexer)
    
class Cpp11Builder(CBuilder):
    """
    Builds C++ executable using g++ and enables C++11.  It mainly uses CBuilder, it only
    changes the compiler command.
    """

    def compiler_command(self):
        return 'g++ -std=c++11'
    def source_extension(self):
        return 'cpp'

BuilderFactory.register('c++11', 'cpp', Cpp11Builder, lexers.CppLexer)
 

class PlainTextBuilder:
    """
    Simply 'builds' the task by saving the input text file and returns a shell
    to execute scripts provided by each test case
    """

    def source_filename(self):
        return "source.txt"

    def shell_executable(self):
        return "/bin/bash"

    def cleanup_source(self,source):
        return source

    def build(self, source, scratch_dir, flags):
        """
        Saves source in the (scratch_dir) with the name provided by
        source_filename()

        Simply returns a shell executable to execute scripts provided by each test case
        """
        sourcefile = os.path.join(scratch_dir, self.source_filename())
        
        pfile = open(sourcefile,"w")
        pfile.write(self.cleanup_source(source))
        pfile.close()

        executable_filename = "%s %s" % (
                self.shell_executable(),
                flags['run'],
                )

        return executable_filename

    def get_compiler_messages(self):
        return ''

BuilderFactory.register('plaintext', 'txt', PlainTextBuilder)


class MakefileBuilder(PlainTextBuilder):
    """
    Based on PlainTextBuilder, it only saves the source into the file named 'Makefile'
    """
    def source_filename(self):
        return "Makefile"

    def cleanup_source(self,source):
        # substitute 2 or more whitespaces at the beginning of each line with a tab
        lines = []
        for line in source.split('\n'):
            newline = re.sub(r"^\s\s\s*","\t",line)
            lines.append(newline.rstrip())
        return '\n'.join(lines)

BuilderFactory.register('makefile', '', MakefileBuilder, lexers.MakefileLexer)


class ShellScriptBuilder:

    def source_filename(self):
        return "source.sh"

    def shell_executable(self):
        return "/bin/bash"

    def cleanup_source(self,source):
        return source

    def build(self, source, scratch_dir, flags):
        """
        Saves source in the (scratch_dir) with the name provided by
        source_filename()
        """
        sourcefile = os.path.join(scratch_dir, self.source_filename())
        
        pfile = open(sourcefile,"w")
        pfile.write(self.cleanup_source(source))
        pfile.close()

        executable_filename = "%s %s %s" % (
                self.shell_executable(),
                flags['run'],
                self.source_filename(),
                )

        return executable_filename

    def get_compiler_messages(self):
        return ''

BuilderFactory.register('shellscript', '.sh', ShellScriptBuilder, lexers.BashLexer)
