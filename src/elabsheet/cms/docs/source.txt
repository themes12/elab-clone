Source code
-----------

Enclose source code in `::elab:begincode` and `::elab:endcode`, and
mark blanks in `{{ }}`.  See an example below.

<table width="100%">
<tr><td>
<p>
Consider the following code: <pre><code>::elab:begincode
x = int(raw_input())
print {{x + 100}}
::elab:endcode
</code></pre>
</p>
</td><td>
<p>
Consider the following code:
<pre>x = int(raw_input())
print <input type="text" size="15"/>
</pre>
</p>
</td></tr>
</table>

Line numbering can be turned on by using a ``lineno=True`` directive.

<table width="100%">
<tr><td>
<p>
Consider the following code: <pre><code>::elab:begincode lineno=True
x = int(raw_input())
print {{x + 100}}
::elab:endcode
</code></pre>
</p>
</td><td>
<p>
Consider the following code:
<pre>1: x = int(raw_input())
2: print <input type="text" size="15"/>
</pre>
</p>
</td></tr>
</table>

A code block can be customized by specifying *directives*.  The following
directives are currently supported:

* ``hidden`` (default ``False``) controls whether the block will
  show up when a student is working on the task.  However, the code block will
  still be included in the automatic grading process.
* ``highlight`` (default ``True``) enables syntax highlighting on the source
  code.
* ``lineno`` (default ``False``) enables line numbering on the source code.
* ``excluded`` (default ``False``) specifies whether the code block is to be
  excluded from the code compilation.  The code block will be displayed no
  matter what the value is.
* ``blank`` (default ``False``) specifies whether the code block is to
  be made entirely blank.
* ``language`` (default ``None``) explicitly specifies the language for which
  the code segment will be highlighted.  If this parameter is None and
  ``highlight`` is True, the code segment will be highlighted based on the
  language setting at the task level.

Source hiding and exclusion
---------------------------

Each individual line inside a `::elab:begincode` and `::elab:endcode` block
can be marked hidden from viewing or excluded from the source by prefixing the
line with the directives `::elab:hide` and `::elab:exclude`, respectively.

For example, the following markdown code
<pre>::elab:begincode
def main():
::elab:exclude     x = randint(0,100)
::elab:hide     x = int(raw_input())
    print x
::elab:endcode
</pre>
will be displayed in the task view as
<pre>
def main():
    x = randint(0,100)
    print x
</pre>
However, the actual source to be seen and executed by the grader is
<pre>
def main():
    x = int(raw_input())
    print x
</pre>

Extra build and run flags
-------------------------

Extra build and run flags can be specified using `::elab:buildflags` and `::elab:runflags`, respectively.

*Build flags* will be inserted into the build command, i.e., when compiling the code.  For example, if the following line is used in a C# task,

    ::elab:buildflags -reference:mylib.dll

then the C# compiler, `gmcs`, will be called with the option `-reference:mylib.dll` when compiling the model code and code submitted by students.

*Run flags* will be inserted into the command that runs the code.  For example, if the following line is used in a Java task,

    ::elab:runflags -Dmy.property="hello"

then the Java interpreter, `java` will be called with the option `-Dmy.property="hello"` when running the code.
