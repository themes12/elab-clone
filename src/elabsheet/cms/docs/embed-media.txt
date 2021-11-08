Embedding Media
---------------

Media such as Youtube video may be embedded into a task using the
`::elab:embed` tag, which must be followed by a `media` argument to specify
the media type and identifier.  Media embedded via `::elab:embed` tag will
automatically be rendered with a feedback dialog attached so that students can
provide comments and ratings for the media in the embedding task.

For example, the following line embeds the Youtube video with video ID `PfCFzezMLxM` into the task.

<pre>
::elab:embed media="youtube:PfCFzezMLxM"
</pre>


Note that embedded media will not show up in the task editing page.  Save the task first and view the result in the task test page.
