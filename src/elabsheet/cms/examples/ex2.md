Calling Functions
=================

<u>**Example 1**</u> Built-in Functions.

* Python comes with a number of built-in functions, which can be used right
  away in a program.
* All of the functions we have used previously are built-in functions.
* A complete list of available built-in functions can be found <a
  target="_blank" href="https://docs.python.org/3/library/functions.html">here</a>.

<pre class="output"><span class="console">&gt;&gt;&gt; </span><span class="stdin"><span class="BUILTIN">print</span>(<span class="STRING">"Hello"</span>)   <span class="COMMENT"># print() function prints values of given expressions</span>
</span><span class="stdout">Hello
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">a = <span class="BUILTIN">int</span>(<span class="STRING">"32"</span>)    <span class="COMMENT"># int() function converts a given string or a given float to an integer</span>
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">a
</span><span class="stdout">32
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">b = <span class="BUILTIN">len</span>(<span class="STRING">"abc"</span>)   <span class="COMMENT"># len() function gives the length of a given string</span>
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">b
</span><span class="stdout">3
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin"><span class="BUILTIN">type</span>(38)         <span class="COMMENT"># type() function gives the type of a specified variable or expression</span>
</span><span class="stdout">&lt;class 'int'&gt;
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin"><span class="BUILTIN">type</span>(<span class="STRING">"38"</span>)
</span><span class="stdout">&lt;class 'str'&gt;
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin"><span class="BUILTIN">type</span>(38.0)
</span><span class="stdout">&lt;class 'float'&gt;
</span><span class="console">&gt;&gt;&gt; </span>
</pre>


<u>**Example 2**</u> Function arguments

* *Arguments* can be given to a function call inside the pair of parentheses
  in order to send values to the function.
* Some functions take no argument, some take one, and some other take more
  than one.

<pre class="output"><span class="console">&gt;&gt;&gt; </span><span class="stdin">a = <span class="BUILTIN">input</span>()  <span class="COMMENT"># input() takes zero or one argument; zero is given</span>
<em>hello</em>
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">a
</span><span class="stdout">'hello'
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">a = <span class="BUILTIN">input</span>(<span class="STRING">"Enter your name: "</span>)  <span class="COMMENT"># optional 'prompt' argument may be given</span>
</span><span class="stdout">Enter your name: </span><span class="stdin"><em>Arthur</em>
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">a
</span><span class="stdout">'Arthur'
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">b = <span class="BUILTIN">round</span>(39.5)     <span class="COMMENT"># round() takes one argument</span>
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">b
</span><span class="stdout">40
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin"><span class="BUILTIN">pow</span>(2,8)            <span class="COMMENT"># pow() takes two arguments</span>
</span><span class="stdout">256
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin"><span class="BUILTIN">max</span>(3,1,8,10,21,5)  <span class="COMMENT"># max() takes any number of arguments</span>
</span><span class="stdout">21
</span><span class="console">&gt;&gt;&gt; </span>
</pre>


<u>**Example 3**</u> Returned Values.

* Most functions return a value, which can be used as an expression
* Certain functions return no value, while some functions may return a group
  of values.

<pre class="output"><span class="console">&gt;&gt;&gt; </span><span class="stdin">a = <span class="BUILTIN">abs</span>(-38)         <span class="COMMENT"># abs() takes one argument and return one value</span>
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">a
</span><span class="stdout">38
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">b = <span class="BUILTIN">print</span>(<span class="STRING">"Hello"</span>)   <span class="COMMENT"># print() outputs a value, but returns nothing (i.e., None)</span>
</span><span class="stdout">Hello
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">b
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin"><span class="BUILTIN">print</span>(b)
</span><span class="stdout">None
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">c = <span class="BUILTIN">divmod</span>(17,3)     <span class="COMMENT"># divmod() returns a pair of values, the quotient and remainder of an integer division</span>
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">c
</span><span class="stdout">(5, 2)
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">q,r = <span class="BUILTIN">divmod</span>(17,3)   <span class="COMMENT"># two variables can be specified to store the two returned values</span>
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">q
</span><span class="stdout">5
</span><span class="console">&gt;&gt;&gt; </span><span class="stdin">r
</span><span class="stdout">2
</span><span class="console">&gt;&gt;&gt; </span>
</pre>

-----------------------
Exercises
---------

<u>**Exercise 1**</u>
Execute each command in the shell.  Enter the result in the boxes.
::elab:begincode language="pycon"
::elab:hide --- ex1.txt
>>> len("Hello, Python!")
{{14}}
>>> pow(3,5)
{{243}}
>>> 3**5
{{243}}
>>> q,r = divmod(135,60)
>>> q
{{2}}
>>> r
{{15}}
::elab:endcode

::elab:begintest
elab-split-files source.txt ---
cat ex1.txt
::elab:endtest

<u>**Exercise 2**</u>
Complete each command so that it prints out the exact value shown in the shell.
::elab:begincode language="pycon"
::elab:hide --- ex2.txt
>>> len({{"aaaaaaaaaa"}})
10
>>> pow({{8,2}})
64
::elab:endcode

::elab:begintest
elab-split-files source.txt ---
elab-run-python-session ex2.txt
::elab:endtest

<u>**Exercise 3**</u>
Complete each command so that it prints out the exact value shown in the shell.
::elab:begincode language="pycon"
::elab:hide --- ex3.txt
>>> q,r = divmod({{22,5}})
>>> q
4
>>> r
2
::elab:endcode

::elab:begintest
elab-split-files source.txt ---
elab-run-python-session ex3.txt
::elab:endtest


------------------------------------
Task Revision History
---------------------
* 2017-07-20 Chaiporn Jaikaeo (chaiporn.j@ku.ac.th)
    * Originally created for Python
* 2017-08-10 Chaiporn Jaikaeo (chaiporn.j@ku.ac.th)
    * Fixed errors (thanks to Worawat Songwiwat for pointing them out)
* 2017-08-19 Chaiporn Jaikaeo (chaiporn.j@ku.ac.th)
    * Fixed errors caused by expressions giving no output
* 2017-11-09 Chaiporn Jaikaeo (chaiporn.j@ku.ac.th)
    * Fixed grading errors for Exercise 3

