Code Blanks
===========

An `::elab:begincode` marks the beginning of a code block, which must end with
`::elab:endcode`.  Use \{\{ and \}\} pair to make a blank in the code section.

::elab:begincode
name = input("What is your name? ")
name = input("What is your name? ")
name = input("What is your name? ")
name = input("What is your name? ")
print({{"Hello, {}".format(name)}})
::elab:endcode

An `::elab:begintest` and `::elab:endtest` pair creates a test case for the
code.

::elab:begintest
Arthur
::elab:endtest
