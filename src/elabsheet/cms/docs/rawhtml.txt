Raw HTML
--------
Quoted from
[Markdown syntax page](http://daringfireball.net/projects/markdown/syntax#html):

> For any markup that is not covered by Markdown's syntax, you simply use HTML
> itself. There's no need to preface it or delimit it to indicate that you're
> switching from Markdown to HTML; you just use the tags.
> 
> The only restrictions are that block-level HTML elements -- e.g. `<div>`,
> `<table>`, `<pre>`, `<p>`, etc. -- must be separated from surrounding content by
> blank lines, and the start and end tags of the block should not be indented
> with tabs or spaces. Markdown is smart enough not to add extra (unwanted)
> `<p>` tags around HTML block-level tags.

Therefore, Markdown will produce an HTML block as appear in source *if* the
HTML block is **preceded by an empty line**.  So, be careful when preparing a
document containing an HTML block with special Markdown syntax inside such as
an answer field.

For example, the following markdown source is processed as desired:
<table width="100%">
<tr><td>
**Markdown Source**
<pre><code>
Fill in the blanks:
&lt;table border="1"&gt;
&lt;tr&gt;
  &lt;td&gt;Question 1&lt;/td&gt;
  &lt;td&gt;{% templatetag openvariable %}answer1{% templatetag closevariable %}&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
  &lt;td&gt;Question 2&lt;/td&gt;
  &lt;td&gt;{% templatetag openvariable %}answer2{% templatetag closevariable %}&lt;/td&gt;
&lt;/tr&gt;
&lt;/table&gt;
</code></pre>
</td>
<td>
**Output**

<p>Fill in the blanks:
<table border="1">
<tr>
  <td>Question 1</td>
  <td><input class="textblank" name="b1" size="18" type="text" value="{% templatetag openvariable %}b1{% templatetag closevariable %}" /></td>
</tr>
<tr>
  <td>Question 2</td>
  <td><input class="textblank" name="b1" size="18" type="text" value="{% templatetag openvariable %}b2{% templatetag closevariable %}" /></td>
</tr>
</table></p>
</td>
</tr>
</table>

However, inserting an empty line right before the `table` tag may give an
undesirable result, as shown:
<table width="100%">
<tr><td>
**Markdown Source**
<pre><code>
Fill in the blanks:<br/>
&lt;table border="1"&gt;
&lt;tr&gt;
  &lt;td&gt;Question 1&lt;/td&gt;
  &lt;td&gt;{% templatetag openvariable %}answer1{% templatetag closevariable %}&lt;/td&gt;
&lt;/tr&gt;
&lt;tr&gt;
  &lt;td&gt;Question 2&lt;/td&gt;
  &lt;td&gt;{% templatetag openvariable %}answer2{% templatetag closevariable %}&lt;/td&gt;
&lt;/tr&gt;
&lt;/table&gt;
</code></pre>
</td>
<td>
**Output**

<p>Fill in the blanks:</p>
<table border="1">
<tr>
  <td>Question 1</td>
  <td>{% templatetag openvariable %}answer1{% templatetag closevariable %}</td>
</tr>
<tr>
  <td>Question 2</td>
  <td>{% templatetag openvariable %}answer2{% templatetag closevariable %}</td>
</tr>
</table>
</td>
</tr>
</table>

