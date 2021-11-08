Code with Aligned Blanks
========================

This is for testing a code block with aligned blanks.

::elab:begincode language="python3"
def func1(x):
{{    y = x*2      }}
{{    return y     }}

def func2(x):
    {{y = 2*x      }}
    {{return y     }}

x = float(input("Enter x: "))
y = {{func1(x)}}
print(f"y = {y}")
::elab:endcode
