
(function() {

    var textareaInFocus = false;
    var blurTimeoutId = null;

    function wrapAt(start, end, startTags, endTags) {
        // save scrollbar state
        var scTop = $("#id_source").prop('scrollTop');

        var st = $("#id_source").val();
        var selected = st.substr(start, end - start);
        $("#id_source").val(st.substr(0,start) +
                            startTags + selected + endTags +
                            st.substr(end));

        // returning states
        var newCursorPos = end + (startTags + endTags).length;

        // prevent the delayed blur event handler to execute as it'll
        // change textareaInFocus to false.
        if(blurTimeoutId)
            clearTimeout(blurTimeoutId);

        $("#id_source")
            .prop('selectionStart',newCursorPos)
            .prop('selectionEnd',newCursorPos)
            .prop('scrollTop', scTop)
            .focus();
    }

    function wrapSelectionWith(startTags, endTags) {
        var range = $("#id_source").getSelection();
        if(range.length>0) {
            wrapAt(range.start, range.end, startTags, endTags);
        }
    }

    function wrapSelectedLinesWith(startTags, endTags) {
        var range = $("#id_source").getSelection();
        var st = $("#id_source").val();
        var lineStart = st.lastIndexOf('\n',range.start) + 1;
        var lineEnd = st.indexOf('\n',range.end);
        if(lineEnd==-1)
            lineEnd = range.end;
        else
            lineEnd;
        
        wrapAt(lineStart, lineEnd, startTags, endTags);
    }

    var editorFunctions = {
        "blank": function() {
            wrapSelectionWith("{{","}}");
        },

        "b": function() {
            wrapSelectionWith("**","**");
        },

        "c": function() {
            wrapSelectionWith("`","`");
        },

        "::code": function() {
            wrapSelectedLinesWith("::elab:begincode\n",
                                  "\n::elab:endcode");
        },

        "::test": function() {
            wrapSelectedLinesWith("::elab:begintest\n",
                                  "\n::elab:endtest");
        }
    };

    function addButtons() {
        // add buttons
        $("#id_source").wrap('<div id="task_editor" style="display: inline-block;"></div>').before('<div id="id_editor_button_list"></div>');

        // build buttons from function list
        var bcount = 0;
        $.each(editorFunctions, function(name) {
            bcount++;
            $('#id_editor_button_list').append(
                '<button id="id_editor_button' + bcount + '" ' + 
                    'class="task-editor-button">' +
                    name + '</button>'
            );
            var f = this;
            $('#id_editor_button' + bcount).click(function(e) {
                e.preventDefault();
                if(textareaInFocus) {
                    f();
                } 
            });
        });

    }

    function main() {
          $('#id_source').focus(function() {
              textareaInFocus = true;
          });
          $('#id_source').blur(function() {
          // delayed state change to make sure that the buttons
          // response when textareaInFocus = true.
              blurTimeoutId = setTimeout(function() {
                  textareaInFocus = false;
              }, 1000);
          });
          addButtons();
    }

    $(document).ready(main);

})();
