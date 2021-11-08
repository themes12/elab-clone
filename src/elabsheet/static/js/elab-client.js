////////////////////////////////////////////////////
// Client-side component rendering for E-Labsheet
////////////////////////////////////////////////////

ElabClient = {

  ////////////////////////////////////////
  // render all elab-specific elements, such as <elab-embed>, on the client
  // side
  render_components: function(task_id,labinsec_id) {
    this.task_id = task_id;
    if (typeof labinsec_id == 'undefined')
      this.labinsec_id = 'none';
    else
      this.labinsec_id = labinsec_id;
    this.render_embedded_media();
  },

  ////////////////////////////////////////
  create_feedback_button: function() {
    var button = $("<button>")
        .attr("type","button")
        .addClass("feedback-button")
        .text("Feedback");
    return button;
  },

  ////////////////////////////////////////
  // create a div to be displayed as a modal dialog for getting user feedback
  // on the embedded media
  create_feedback_dialog: function(id,type,media) {
    self = this;
    var div = $("<div>").attr("title","Feedback")
                        .addClass("feedback-dialog")
                        .attr("id",id)
                        .attr("media-type",type)
                        .attr("media-id",media);

    div.append($("<p>").html(
      '<p style="font-weight:bold">Comments / Suggestions:</p>\n' +
      '<textarea id="feedback-comments" rows="3" style="width:100%"></textarea>\n' +
      '<p style="font-weight:bold">Rating:</p>\n' +
      '<p><select id="feedback-rating" name="rating" autocomplete="off">\n' +
      '  <option value="1">1</option>\n' +
      '  <option value="2">2</option>\n' +
      '  <option value="3">3</option>\n' +
      '  <option value="4">4</option>\n' +
      '  <option value="5">5</option>\n' +
      '</select></p>'
    ));

    var url = Urls['feedback:process'](self.task_id,self.labinsec_id,type,media);
    var comments = div.find('#feedback-comments');
    var rating = div.find('#feedback-rating');
    rating.barrating({
      theme: 'css-stars'
    });

    // try to fetch existing feedback for this media
    $.ajax({
      type: 'GET',
      url: url,
      success: function(data) {
        comments.val(data.comments);
        rating.barrating('set',data.rating);
      },
    });

    // create 'save' event to be triggered by the external code
    div.on('save',function() {
      $.ajax({
        type: 'POST',
        url: url,
        data: {
          comments: comments.val(),
          rating: rating.val()
        },
      });
    });

    return div;
  },

  ////////////////////////////////////////
  create_youtube_div: function(media) {
    var src = "https://www.youtube.com/embed/" + media;
    var div = $("<div>");
    div.append(
      $("<iframe>")
        .attr("width","560")
        .attr("height","315")
        .attr("src",src)
        .attr("frameborder","0")
        .attr("allowfullscreen",""));
    return div;
  },

  ////////////////////////////////////////
  // replace each <elab-embed> tag with the corresponding element to display
  // the media of the type and id specified in the attributes
  render_embedded_media: function() {
    var self = this;
    $("#assignment-body").find("elab-embed").replaceWith(function() {
      var type = $(this).attr("type");
      var media = $(this).attr("media");
      var id = type + "-" + media;

      var media_div;
      if (type == "youtube")
        media_div = self.create_youtube_div(media);
      else
        return $("<div>").text("Unsupported media type");

      var button = self.create_feedback_button().attr("id",id);
      var dialog = self.create_feedback_dialog(id,type,media);

      return [
        media_div,
        $("<div>").append(button),
        dialog];
    });

    // attach a dialog to the corresponding feedback button
    $(".feedback-dialog").each(function() {
      // make sure the dialog has not been built already
      if (!$(this).hasClass("ui-dialog-content")) {
        var button_select = ".feedback-button#" + $(this).attr("id");
        var dialog = $(this).dialog({
          autoOpen: false,
          modal: true,
          buttons: {
            'Save' : function() {
              $(this).trigger('save');
              $(this).dialog('close');
            },
            'Cancel' : function() {
              $(this).dialog('close');
            }
          }
        });
        $(button_select).on("click",function() {
          dialog.dialog("open");
        });
      }
    });
  },

  ////////////////////////////////////////
  // Fetch grading result explanation of the given submission and display it
  // in a modal dialog
  show_result_explanation: function(element,submission) {
    if (typeof(submission) === "number") {
      $.get(Urls['lab:explain-submission-results'](submission), function(data) {
        var dialog_id = "dialog-explain-"+submission;
        var dialog_div = $("<div>").attr("title","Result Explanation")
                            .addClass("result-explain-dialog")
                            .attr("id",dialog_id)
                            .append(data);
        $(element).after(dialog_div);
        $(element).next().dialog({
          autoOpen: true,
          modal: true,
          width: 600,
          height: 500,
          buttons: {
            'Close' : function() {
              $(this).dialog('close');
            }
          }
        });
      });
    }
    else if (typeof(submission) === "string") {
      // submission results are provided as rendered HTML string
      var dialog_div = $("<div>").attr("title","Result Explanation")
                          .addClass("result-explain-dialog")
                          .append(submission);
      $(element).after(dialog_div);
      $(element).next().dialog({
        autoOpen: true,
        modal: true,
        width: 600,
        height: 500,
        buttons: {
          'Close' : function() {
            $(this).dialog('close');
          }
        }
      });
    }
  },

  ////////////////////////////////////////
  // Create an empty manual score box to each of the manual answers inside
  // the specified jquery element
  create_manual_score_boxes: function($element,options) {
    $(".textblank",$element).each(function(i) {
      score_box = $("<input>")
        .attr("type","text")
        .attr("size","1")
        .attr("class","scorebox")
        .attr("name","score_" + this.name);
      $(this).after(score_box);
      if (options && options.readOnly)
        score_box.attr("readOnly",true);
    });
  },

  ////////////////////////////////////////
  // Update manual score boxes with the provided scores
  update_manual_score_boxes: function($element,scores) {
    $("input.scorebox",$element).attr("value","");
    $(".textblank",$element).each(function(i) {
      if ((scores != null) && (this.name in scores)) {
        var score = scores[this.name];
        $element.find("input.scorebox[name='score_" + this.name + "']")
          .attr("value",score)
          .attr("size",Math.max(String(score).length,1));
      }
    });
  },

  remove_manual_score_boxes: function($element) {
    $("input.scorebox",$element).remove();
  }
};

