Java-specific source syntax
---------------------------

Since Java is very strict in source file names and the system is not
good enough to figure them all out by itself, you should help it.  The
system supports many source files and lets the user specify the main
class to be called. It can also infer class name from the first source
file name.

There are two ways to include many source files for Java.

**1. Inside source field of Task.**  (This is required.)

Users must specify the source file names in the source by placing the
following options (as comments) inside the `elab::begincode` -
`elab::endcode` tags.
    
* Specifying source file name:

        // elab-source: filename (with path)

* Specifying main class:

        // elab-mainclass:  mainclass.Name

The source field in task shall be broken into many source files at
places where the elab-source options are.  The content before the
first option is discarded.

If main class is not specify, the name is derived from the first
source filename.

**2. As Task supplements.**

Users can also add more related source files as the task supplements.
All files should be compressed (using zip or gzip) so that to save the
original path and file names.  The files will be extracted to the sand
box directory when the program gets compiled and executed.  Then,
JavaBuilder will search for all files with .java extension and compile
them.
