import os
import stat
import shutil
import tempfile
try:
    import pwd
except ImportError:
    pass

from random import randint

from django.conf import settings

from .builders import BuilderFactory, BuildError

class NoInputProvided(Exception):
    pass

class NoSourceProvided(Exception):
    pass

class BoxNotReady(Exception):
    def __init__(self,value=''):
        self.value = value
    def __str__(self):
        return repr(self.value)

# tmie limit in seconds
DEFAULT_TIME_LIMIT = settings.DEFAULT_TIME_LIMIT

# mem limit in megabytes
DEFAULT_MEMORY_LIMIT = settings.DEFAULT_MEMORY_LIMIT  

INPUT_FILENAME = 'sandbox-input.txt'
OUTPUT_FILENAME = 'sandbox-output.txt'

BOX_FILENAME = 'box'
BOX_STAT_FILENAME = 'box.out'

class SourceCode:
    """
    SourceCode is the minimal container for (language,body) pair.
    """
    def __init__(self,language,body):
        self.language = language
        self.body = body

class BuiltSourceCode:
    """
    BuiltSourceCode is a source code that has already been built.  

    This is used to separate compilation from source code evaluation
    to improve evaluation speed for compile languages.

    It only keeps the executable filename and compiler messages.
    """
    def __init__(self,executable_filename, compiler_messages):
        self.executable_filename = executable_filename
        self.compiler_messages = compiler_messages

class Sandbox:
    """
    This class encapsulate the sandbox functionality.  It aims to be
    programming language independent.

    It enforces memory and time limitation through box.cc.  The box
    should be run as user nobody:nogroup (through setuid) so that the
    file permission can be enforced.
    """

    def __init__(self, scratch_dir, 
                 temp_subdir=False,
                 create_scratch_dir=False,
                 time_limit=DEFAULT_TIME_LIMIT,
                 memory_limit=DEFAULT_MEMORY_LIMIT,
                 clean_dir=False,
                 builder_factory=BuilderFactory,
                 use_box=None, verify_box=True,
                 flags={}): 
        """
        Initialize a sandbox.  

        Required argument: 
        * scratch_dir 

        Keyworded arguments:
        * create_scratch_dir : if scratch dir should be created
        * temp_subdir : if sandbox should use subdir inside scratch dir
        * clean_dir : clean the scratch dir (or subdir) after evaluation?

        * time_limit : in seconds
        * memory_limit : in megabytes

        * builder_factory : a factory used to create a builder,
          some object that builds an executable from a sourcecode,
          for each supporting language.

        * use_box : use settings.USE_BOX_IN_SANDBOX if None
        * verify_box : check existance and permissions of box before use

        * flags : indicate 'build' and 'run' flags to be given to the
                  builder and application loader, respectively

        """
        self.input_scratch_dir = os.path.abspath(scratch_dir)
        self.scratch_dir = Sandbox.prepare_scratch_dir(scratch_dir,
                                                       temp_subdir,
                                                       create_scratch_dir)
        self.scratch_dir_created = create_scratch_dir
        self.temp_subdir_created = temp_subdir

        self.sandbox_dir = os.path.abspath(os.path.dirname(__file__))
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.builder_factory = builder_factory
        self.clean_dir = clean_dir
        self.verify_box = verify_box
        self.flags = flags

        if use_box==None:
            # check settings
            try:
                self.use_box = settings.USE_BOX_IN_SANDBOX
            except:
                self.use_box = True
        else:
            self.use_box = use_box


    @staticmethod
    def prepare_scratch_dir(scratch_dir, temp_subdir, create_scratch_dir):
        sdir = os.path.abspath(scratch_dir)
        if temp_subdir:
            path = tempfile.mkdtemp(dir=sdir)
            os.chmod(path, stat.S_IRWXU | stat.S_IROTH | stat.S_IXOTH |
                     stat.S_IRGRP | stat.S_IXGRP)
            return path
        if create_scratch_dir and (not os.path.exists(sdir)):
            os.makedirs(sdir)
        return sdir

    def clean_scratch_dir(self):
        if self.scratch_dir_created:
            target = self.input_scratch_dir
        else:
            # clean up only temp_subdir (when temp_subdir is created)
            target = self.scratch_dir

        try:
            files = os.listdir(target)
            for f in files:
                try:
                    full_name = os.path.join(target,f)
                    if os.path.isdir(full_name):
                        for sub_f in os.listdir(full_name):
                            os.remove(os.path.join(full_name,sub_f))
                        os.rmdir(full_name)
                    else:
                        os.remove(full_name)
                except:
                    pass
            
        except:
            pass

        if self.temp_subdir_created:
            shutil.rmtree(self.scratch_dir)

        if self.scratch_dir_created:
            # we have to remove it too
            shutil.rmtree(self.input_scratch_dir)

    def prepare_input_file(self, input_string):
        input_filename = os.path.join(self.scratch_dir,INPUT_FILENAME)
        f = open(input_filename,"w")
        f.write(input_string)
        f.close()
        return input_filename

    def prepare_output_file(self, output_filename):
        if output_filename==None:
            out_fname = os.path.join(self.scratch_dir,OUTPUT_FILENAME)
        else:
            out_fname = os.path.join(self.scratch_dir,output_filename)
        f = open(out_fname,"w")
        f.close()
        os.chmod(out_fname,0o777)
        return out_fname

    def check_box(self):
        """
        Checks if box satisfying the following requirements:
        - exists
        - has the correct owner (settings.BOX_USER)
        - has the suid bit on (to prevent accessing/manipulating files)
        """
        box_filename = os.path.join(self.sandbox_dir,BOX_FILENAME)
        if not os.path.exists(box_filename):
            raise BoxNotReady('box does not exist.')

        try:
            # maybe pwd module can't be import (when runs on Windows)
            box_uid = pwd.getpwnam(settings.BOX_USER).pw_uid
        except:
            raise BoxNotReady('can not determine box\'s user\'s userid.')

        box_stat = os.stat(box_filename)
        if box_stat.st_uid!=box_uid:  # check owner
            raise BoxNotReady('box\'s owner is invalid.')
        if box_stat.st_mode & stat.S_ISUID == 0:  # check mode
            raise BoxNotReady('box\'s mode is invalid.')

    def prepare_command_line_without_box(self, executable_filename,
                                         input_filename,
                                         output_filename):
        return (executable_filename + " < " + input_filename + 
                " > " + output_filename)

    def prepare_command_line_with_box(self, executable_filename,
                                      input_filename,
                                      output_filename):
        box_filename = os.path.join(self.sandbox_dir,BOX_FILENAME)
        box_stat_filename = os.path.join(self.scratch_dir, BOX_STAT_FILENAME)
        return (box_filename + ' -T ' + 
                ' -e ' +
                ' -t ' + str(self.time_limit) + 
                ' -m ' + str(self.memory_limit * 1024) +
                ' -i ' + input_filename +
                ' -o ' + output_filename +
                (' -w ' if settings.USE_WALL_CLOCK else '') +
                ' ' + executable_filename +
                ' 2> ' + box_stat_filename)

    def build(self, source):
        builder = self.builder_factory.get(source.language)
        executable_filename = builder.build(source.body, self.scratch_dir, self.flags)
        compiler_messages = builder.get_compiler_messages()
        return BuiltSourceCode(executable_filename, compiler_messages)

    def evaluate(self, source=None, built_source=None, 
                 input_string=None, input_filename=None, 
                 output_filename=None, capture=False):

        # set a flag in case the evaluated code needs to know
        os.putenv("ELAB_GRADING","1")

        if input_string == None and input_filename == None:
            raise NoInputProvided()

        if source==None and built_source==None:
            raise NoSourceProvided()

        if built_source==None:
            builder = self.builder_factory.get(source.language)
            executable_filename = builder.build(source.body, self.scratch_dir, self.flags)
            self.compiler_messages = builder.get_compiler_messages()
        else:
            executable_filename = built_source.executable_filename
            self.compiler_messages = built_source.compiler_messages

        if input_string != None:
            input_filename = self.prepare_input_file(input_string)

        real_output_filename = self.prepare_output_file(output_filename)

        initial_dir = os.getcwd()
        os.chdir(self.scratch_dir)
        os.chmod(self.scratch_dir,
                stat.S_IRUSR |
                stat.S_IWUSR |
                stat.S_IXUSR |
                stat.S_IRGRP |
                stat.S_IWGRP |
                stat.S_IXGRP)

        if self.use_box:
            if self.verify_box:
                self.check_box()
            cmd = self.prepare_command_line_with_box(executable_filename,
                                                     input_filename,
                                                     real_output_filename)
        else:
            cmd = self.prepare_command_line_without_box(executable_filename,
                                                        input_filename,
                                                        real_output_filename)
        os.system(cmd)

        os.chdir(initial_dir)

        # TODO: FIX THIS: this part is a bit ugly
        if output_filename == None:
            try:
                # TODO: get rid of the hard-coded number
                output_str = open(real_output_filename).read(1000000)
            except:
                #import traceback
                #traceback.print_exc()
                output_str = None
            if self.clean_dir:
                self.clean_scratch_dir()
            return output_str
        else:
            os.chmod(real_output_filename,0o644)
            if self.clean_dir:
                self.clean_scratch_dir()

    def get_compiler_messages(self):
        return self.compiler_messages

    @staticmethod
    def get_languages():
        return BuilderFactory.get_languages()

    @staticmethod
    def get_languages_with_extensions():
        return BuilderFactory.get_languages_with_extensions()

    def get_scratch_dir(self):
        return self.scratch_dir
