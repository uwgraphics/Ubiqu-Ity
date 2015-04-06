/* Begin sloppy globals */
// http://stackoverflow.com/a/956878
function countProperties(obj) {
    var count = 0;

    for(var prop in obj) {
        if(obj.hasOwnProperty(prop))
            ++count;
    }

    return count;
}

// http://stackoverflow.com/a/646643/1991086
if (typeof String.prototype.startsWith != 'function') {
    String.prototype.startsWith = function (str){
        return this.slice(0, str.length) == str;
    };
}

var updateTimeout;
var topic_colors = {};
var activeTopics = [];
var tags_top_only = true;
var color_ramps = false;
var color_set_name = "seq_single_hue_ramps_3_based_on_7";
/* End sloppy globals */

/* Code for tag buttons in sidebar */
var handleTagButtons = function(event) {
    var topic_class_str = $(this).attr("data-key");
    if (localStorage[corpus_name] == undefined) {
        localStorage[corpus_name] = '';
    }
    var storedTopics = localStorage[corpus_name].split(',');
    if (storedTopics.indexOf(topic_class_str) == -1 && ! $(this).hasClass('active')) {
        storedTopics.push(topic_class_str);
        localStorage[corpus_name] = storedTopics;
    } else if (storedTopics.indexOf(topic_class_str) != -1 && $(this).hasClass('active')) {
        storedTopics.splice(storedTopics.indexOf(topic_class_str),1);
        localStorage[corpus_name] = storedTopics;
    }
    toggleTopic(topic_class_str);
};

var toggleTopic = function(topic_class_str) {
    var $that = $('#btn-' + topic_class_str);
    if (! $that.hasClass("active")) {
        $that.addClass("active");
        $(".html_formatter").addClass(topic_class_str);
        activeTopics.push(topic_class_str);
    }
    else {
        $that.removeClass("active");
        $(".html_formatter").removeClass(topic_class_str);
        // Free up this topic's color.
        delete topic_colors[topic_class_str];
        activeTopics.splice(activeTopics.indexOf(topic_class_str), 1);
    }
    clearTimeout(updateTimeout);
    updateTimeout = setTimeout(
        updateLineGraph,
        100
    );
};

var getNextUnusedColorIndex = function(colors, topic_colors) {
    // The index to use when all other colors are used up.
    var index_to_return = colors.length - 1;
    for (var j = 0; j < colors.length - 1; j++) {
        var color = colors[j];
        if (countProperties(topic_colors) == 0) {
            index_to_return = j;
            break;
        }
        else {
            // Verify that this color is unused.
            var is_unused = true;
            for (var prop in topic_colors) {
                if (topic_colors.hasOwnProperty(prop) && color == topic_colors[prop]) {
                    is_unused = false;
                }
            }
            if (is_unused) {
                index_to_return = j;
                break;
            }
        }
    }
    return index_to_return;
};

var applyActiveClasses = function() {
    var tag_key_classes = {};
    for (var i = 0; i < activeTopics.length; i++) {
        // Is this tag_map tagged with this tag key?
        var tag_key = activeTopics[i];
        if ($(this).is("[data-key~='" + tag_key + "']")) {
            // Figure out which class corresponds with this data key.
            for (var j = 0; j < this.classList.length; j++) {
                var class_name = this.classList[j];
                if (class_name.indexOf(tag_key) !== -1) {
                    tag_key_classes[tag_key] = class_name;
                }
            }
        }
    }

    var highest_active_tag_key;
    var highest_active_ramp_index = -1;
    for (var tag_key in tag_key_classes) {
        var tag_key_class = tag_key_classes[tag_key];
        var tag_key_class_split = tag_key_class.split("_");
        var tag_key_ramp_index = parseInt(tag_key_class_split[tag_key_class_split.length - 1], 10);
        if (tag_key_ramp_index > highest_active_ramp_index) {
            highest_active_ramp_index = tag_key_ramp_index;
            highest_active_tag_key = tag_key;
        }
    }

    if (
        highest_active_tag_key !== null &&
        (
            countProperties(tag_key_classes) == 1 || (countProperties(tag_key_classes) >= 1 && tags_top_only)
        )
    ) {
        $(this).attr("data-active-tag-key", highest_active_tag_key);
    }
    else if (countProperties(tag_key_classes) > 0) {
        var attr_value = "!MULTIPLE" + " " + highest_active_tag_key;
        if (color_ramps) {
            attr_value +=  " " + "!MULTIPLE" + "_" + highest_active_ramp_index;
        }
        $(this).attr("data-active-tag-key", attr_value);
    }
    else {
        $(this).attr("data-active-tag-key", "");
    }
};

var updateLineGraph = function() {
    var colors = app_colors[color_set_name];
    for (var j = 0; j < activeTopics.length; j++) {
        var class_str = activeTopics[j];
        var color_index = getNextUnusedColorIndex(colors, topic_colors);
        if (! topic_colors.hasOwnProperty(class_str)) {
            topic_colors[class_str] = colors[color_index];
        }
    }
    // Generate CSS for topics based on the colors we assigned them.
    var css_str = "";
    // Generic stuff for active tags
    var active_selectors_str = "";
    for (var j = 0; j < activeTopics.length; j++) {
        var topic_key = activeTopics[j];
        active_selectors_str += ".html_formatter." + topic_key + " > span[data-key~='" + topic_key + "']";
        if (j < activeTopics.length - 1) {
            active_selectors_str += ", ";
        }
    }
    css_str += active_selectors_str + " { box-shadow: 0 0 0 1px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.15); text-shadow: 0 1px 1px rgba(255,255,255,0.5), 0 -1px 1px rgba(255,255,255,0.5), -1px 0 1px rgba(255,255,255,0.5), 1px 0 1px rgba(255,255,255,0.5), 0 1px 2px rgba(255,255,255,0.35); }";
    // Colors!
    for (var topic_key in topic_colors) {
        if (topic_colors.hasOwnProperty(topic_key)) {
            var topic_color = topic_colors[topic_key];
            var topic_color_ramp;
            if (typeof topic_color != "string") {
                // Cool, we have a color ramp.
                topic_color = topic_colors[topic_key][0];
                topic_color_ramp = topic_colors[topic_key][1];
            }
            /* Colored Button Styles */
            css_str += "#topic_model_tag_buttons .btn.active#btn-" + topic_key + " { background-color: " + topic_color + "; }\n";

            /* HTMLFormatter Styles */
            // Use the color ramp if available (and we're supposed to).
            // Use the second-last ramp color for the multi-tagged "underline".
            var multiple_active_styles_color = topic_color_ramp[topic_color_ramp.length - 2];
            // var multiple_active_styles = "background-image: -webkit-linear-gradient(top, rgba(0,0,0,0) 0%, rgba(0,0,0,0) 75%, rgba(255,255,255,0.35) 75%, rgba(255,255,255,0.35) 81.25%, rgba(0,0,0,0.15) 81.25%, rgba(0,0,0,0.15) 87.5%, " + multiple_active_styles_color + " 87.5%, " + multiple_active_styles_color + " 100%);";
            var multiple_active_styles = "background-image: -webkit-linear-gradient(top, rgba(0,0,0,0) 0%, rgba(0,0,0,0) 82.25%, rgba(255,255,255,0.5) 81.25%, rgba(255,255,255,0.5) 87.5%, " + multiple_active_styles_color + " 87.5%, " + multiple_active_styles_color + " 100%);";
            var active_class = "[data-active-tag-key='" + topic_key + "']";
            var multiple_active_class = "[data-active-tag-key~='!MULTIPLE'][data-active-tag-key~='" + topic_key + "']";
            var base_selector = ".html_formatter." + topic_key + " > span[data-key~='" + topic_key + "']";

            if (color_ramps && topic_color_ramp !== null && topic_color_ramp.length > 0) {
                for (var ramp_index = 0; ramp_index < topic_color_ramp.length; ramp_index++) {
                    var active_styles = "background-color: " + topic_color_ramp[ramp_index] + ";";
                    var selector = base_selector + "." + topic_key + "_" + ramp_index;
                    css_str += selector + active_class + " { " + active_styles + " }\n";
                    css_str += selector + multiple_active_class + " { " + multiple_active_styles + " }\n";
                }
            }
            // Just use the color instead.
            else {
                css_str += base_selector + " { background-color: " + topic_color + "; }\n";
                css_str += base_selector + multiple_active_class + " { " + multiple_active_styles + " }\n";
            }

            /* LineGraphFormatter Styles */
            css_str += ".topic_model_line_graph g." + topic_key + " { opacity: 1.0; }\n";
            // css_str += ".topic_model_line_graph g." + prop + ":hover { opacity: 1.0; }\n";
            css_str += ".topic_model_line_graph g." + topic_key + " rect { fill-opacity: 0.0625; }\n";
            css_str += ".topic_model_line_graph g." + topic_key + ":hover rect { fill-opacity: 0.375; }\n";
            // css_str += ".topic_model_line_graph g." + prop + ":hover rect { fill-opacity: 0.75; }\n";
            css_str += ".topic_model_line_graph g." + topic_key + " use.polyline { stroke: " + topic_color + "; }\n";
            css_str += ".popover rect[data-key~=" + topic_key + "] { fill: " + topic_color + "; }\n";
        }
    }
    /* More CSS for all active tags */
    // Insert the CSS into the DOM.
    var $css_el = $("<style class='topic_model' type='text/css'>");
    $css_el.text(css_str);
    if ($("style.topic_model").get(0)) {
        $("style.topic_model").replaceWith($css_el);
    }
    else {
        $("head").append($css_el);
    }


    // Find the set of tokens to which we should apply the new "active" classes.
    $(".html_formatter > span").each(applyActiveClasses);
};

var fetchLineGraph = function() {
    $("#right_sidebar_content").addClass("withLoadingIndicator");
    // Generate the URI to the new line graph SVG.
    var pixel_size = $('#right_sidebar_content').height();
    var line_graph_uri = flask_util.url_for(
        "text_get_topic_model_line_graph", {
            "corpus_name": corpus_name,
            "text_name": text_name,
            "pixel_size": pixel_size
        }
    );
    // Fetch the new SVG DOM with jQuery and insert it into the DOM.
    var $old_el = $("#right_sidebar_content .topic_model_line_graph");
    $.get(line_graph_uri, function(response) {
        var $response = $(response);
        $("#right_sidebar_content").removeClass("withLoadingIndicator");
        $old_el.replaceWith($response);

        // Attach events.
        attachLineGraphEventsToElement($response);
    });
};

var attachLineGraphEventsToElement = function(el) {
    $("g[data-key]", el).on("click", function() {
        // var $parent = $(this).parents("g[data-key]");
        console.log(this);
        var $buttons_to_activate = $("#sidebar .btn-tag").filter("." + $(this).attr("data-key"));
        $buttons_to_activate.trigger("click");
    }).on("mouseover", function() {
        syncTopicBrushing($(this).attr("data-key"));
    }).on("mouseout", function() {
        endSyncTopicBrushing($(this).attr("data-key"));
    }).on("contextmenu", function() {
        var $buttons_to_activate = $("#sidebar .btn-tag").filter("." + $(this).attr("data-key"));
        $buttons_to_activate.trigger("contextmenu");
    });
};

/* End code for tag buttons in sidebar */

/* Code for word distribution popovers */
var clearPopovers = function() {
    $("body .popover").remove();
    $("body .html_formatter > span.active").removeClass("active");
    clearPopoverEvents();
};

var getBottomPosition = function(popover_el) {
    // This only works correctly for pixel values!!!
    return (
        parseInt(
            $(popover_el).css("top")
        ) +
        $(popover_el).height() +
        parseInt(
            $(popover_el).css("padding-top")
        ) +
        parseInt(
            $(popover_el).css("padding-bottom")
        ) +
        parseInt(
            $(popover_el).css("border-top")
        ) +
        parseInt(
            $(popover_el).css("border-bottom")
        )
    );
};

var clearPopoverEvents = function() {
    $(window)
        .off("click.getTopicsForWordElement")
        .off("scroll.getTopicsForWordElement")
        .off("resize.getTopicsForWordElement")
        .off("keydown.getTopicsForWordElement");
};

var conditionallyClearPopovers = function(event) {
    var condition = ! (
        $(event.target).is("#main .html_formatter > span") ||
        $(event.target).parents("#main .html_formatter > span").length > 0
    );

    if (condition) {
        clearPopovers();
    }
};

var reshowActivePopovers = function(event) {
    var $active_spans = $(".html_formatter > span.active");
    $active_spans.popover('show');
};

var reshowActivePopoversWithTimeout = function(event) {
    clearTimeout(updateTimeout);
    updateTimeout = setTimeout(
        reshowActivePopovers,
        100
    );
};

var closePopoversWithEscKey = function(event) {
    // Look for keycode for Esc key
    if (event.keyCode == 27) {
        clearPopovers();
    }
};

var attachPopoverEvents = function(element) {
    $(element)
        .on("click.getTopicsForWordElement", conditionallyClearPopovers)
        .on("scroll.getTopicsForWordElement", reshowActivePopoversWithTimeout)
        .on("resize.getTopicsForWordElement", reshowActivePopoversWithTimeout)
        .on("keydown.getTopicsForWordElement", closePopoversWithEscKey);
};

// Events for .html_formatter tokens, etc.
var getTopicsForWordElement = function() {
    var word = $.trim($(this).text());
    // Do nothing if this "word" was either nothing or just whitespace.
    if (word === "") {
        return;
    }
    // Remove existing popovers.
    clearPopovers();
    // Create the new popover right away.
    var that = this;
    var topic_dist_container_id = "topic_dist_" + $(this).attr("id");
    $(this)
        .addClass("active")
        .popover({
            title: "Topic Distributions for &ldquo;" + word + "&rdquo;",
            html: true,
            trigger: "manual",
            placement: "bottom",
            animation: false,
            container: "body"
        });
        // .popover('show');
    $(this).data("popover").options.content = "<div id='" + topic_dist_container_id + "' class='withLoadingIndicator' style='height: 84px'></div>";
    $(this).popover("show");
    /* Reposition the popover if it's tall enough to be off-screen. */
    if (getBottomPosition($(this).data().popover.$tip) > $(window).height() - 12) {
        $(this).data().popover.options.placement = "top";
        $(this).popover("show");
    } else {
        $(this).data().popover.options.placement = "bottom";
        $(this).popover("show");
    }

    // Generate the topic distribution.
    genWordView(corpus_name, text_name, word, this);

    // Attach events to close the popovers.
    attachPopoverEvents(window);
};
/* end code for word distribution popovers */

/* Code for synced brushing */

var syncTopicBrushing = function(tag_key) {
    // Add ".highlight" to related elements.
    d3.selectAll(".topic_model_line_graph g[data-key='" + tag_key + "']")
        .classed("highlight", true);
    d3.selectAll("#sidebar .btn-tag[data-key='" + tag_key + "']")
        .classed("highlight", true);
    d3.selectAll(".popover rect.bar[data-key='" + tag_key + "']")
        .style("fill", "#ffff99");
    // Trying out this new jQuery viewport selector plugin.
//    $(".html_formatter > span[data-key~='" + tag_key + "']:in-viewport")
//        .addClass("highlight");
};

var endSyncTopicBrushing = function(tag_key) {
    d3.selectAll(".topic_model_line_graph g[data-key='" + tag_key + "']")
        .classed("highlight", false);
    d3.selectAll("#sidebar .btn-tag[data-key='" + tag_key + "']")
        .classed("highlight", false);
    d3.selectAll(".popover rect.bar[data-key='" + tag_key + "']")
        .style("fill", false);
    // Trying out this new jQuery viewport selector plugin.
//    $(".html_formatter > span[data-key~='" + tag_key + "'].highlight")
//        .removeClass("highlight");
};

var updateStyleElement = function(class_str, styles_str) {
    var $style_el = $("<style class='" + class_str + "' type='text/css'>");
    $style_el.text(styles_str);
    if ($("style." + class_str.replace(" ", ".")).get(0)) {
        $("style." + class_str.replace(" ", ".")).replaceWith($style_el);
    }
    else {
        $("head").append($style_el);
    }
};

/* End code for synced brushing */

// Code for changing the text tagging display mode.
var changeTagDisplayMode = function(new_mode_value) {
    if (new_mode_value !== undefined) {
        tags_top_only = new_mode_value;
    }
    else {
        tags_top_only = ! tags_top_only;
    }
    if (tags_top_only) {
        $(".btn-group.color_ramps .btn").addClass("tags_top_only_on");
        $(".btn-group.tags_top_only .btn.btn-tags_top_only_on").addClass("btn-primary");
        $(".btn-group.tags_top_only .btn.btn-tags_top_only_off").removeClass("btn-primary");
    }
    else {
        $(".btn-group.color_ramps .btn").removeClass("tags_top_only_on");
        $(".btn-group.tags_top_only .btn.btn-tags_top_only_on").removeClass("btn-primary");
        $(".btn-group.tags_top_only .btn.btn-tags_top_only_off").addClass("btn-primary");
    }
    $(".html_formatter > span").each(applyActiveClasses);
};

var changeColorRampsMode = function(new_mode_value) {
    if (new_mode_value !== undefined) {
        color_ramps = new_mode_value;
    }
    else {
        color_ramps = ! color_ramps;
    }
    if (color_ramps) {
        $(".btn-group.tags_top_only .btn").addClass("color_ramps_on");
        $(".btn-group.color_ramps .btn.color_ramps_on").addClass("btn-primary");
        $(".btn-group.color_ramps .btn.color_ramps_off").removeClass("btn-primary");
    }
    else {
        $(".btn-group.tags_top_only .btn").removeClass("color_ramps_on");
        $(".btn-group.color_ramps .btn.color_ramps_on").removeClass("btn-primary");
        $(".btn-group.color_ramps .btn.color_ramps_off").addClass("btn-primary");
    }
    $(".html_formatter > span").each(applyActiveClasses);
};

// Attach event listeners with jQuery.
(function() {
    $("#sidebar .btn-tag")
        .on("click", handleTagButtons)
        .on('contextmenu', function(event) {
            event.preventDefault();
            var $this = $(this);
            var topicNum = parseInt($this.attr('data-key').split('_')[1]);
            genTopicView(corpus_name, topicNum, '#topicDist', $this.text());
            $('#topicDistModal').modal('show');
        });

    $(".clear_all_tags").on("click", function() {
        $("#sidebar .btn-tag.active").each(handleTagButtons);
    });

    // Attach getTopicsForWordElement() to .html_formatter and delegate to span.token elements.
    $("#main_content").on("click", ".html_formatter > span[data-key!='!UNTAGGED']", getTopicsForWordElement);

    // Attach brushing events.
    $("#sidebar .btn-tag[data-key]").on("mouseover", function() {
        syncTopicBrushing($(this).attr("data-key"));
    }).on("mouseout", function() {
        endSyncTopicBrushing($(this).attr("data-key"));
    });

    // Attach cross-tab topic toggling
    window.addEventListener('storage', function() {
        if (event.key == corpus_name) {
            var oldTopics = event.oldValue.split(',');
            var newTopics = event.newValue.split(',');
            for (var i = 0; i < oldTopics.length; i++) {
                if (newTopics.indexOf(oldTopics[i]) == -1) {
                    toggleTopic(oldTopics[i]);
                }
            }
            for (var i = 0; i < newTopics.length; i++) {
                if (oldTopics.indexOf(newTopics[i]) == -1) {
                    toggleTopic(newTopics[i]);
                }
            }
        }
    }, false);

    // Now the line graph should get an update on page load.
    fetchLineGraph();

    // Load the HTML if we're supposed to
    if (text_name !== undefined && $(".html_formatter").get(0)) {
        var html_uri = flask_util.url_for(
            "text_get_html_partial",
            {
                corpus_name: corpus_name,
                text_name: text_name
            }
        );
        $.get(html_uri, function(response) {
            $("#main_content").removeClass("withLoadingIndicator");
            $(".html_formatter").replaceWith(response);
        });
    }

//    $("body").on(".popover rect", "mouseover", function() {
//        syncTopicBrushing($(this).attr("data-key"));
//    }).on(".popover rect", "mouseout", function() {
//        endSyncTopicBrushing($(this).attr("data-key"));
//    });

    // Also, attach the line graph events to any and all line graphs.
//    $(".topic_model_line_graph").each(attachLineGraphEventsToElement);

    // Initialize "Text Tagging Display" buttons.
    changeTagDisplayMode(tags_top_only);
    changeColorRampsMode(color_ramps);

    $(".btn-group.tags_top_only .btn.btn-tags_top_only_on").click(function() {
        changeTagDisplayMode(true);
    });

    $(".btn-group.tags_top_only .btn.btn-tags_top_only_off").click(function() {
        changeTagDisplayMode(false);
    });

    $(".btn-group.color_ramps .btn.color_ramps_on").click(function() {
        changeColorRampsMode(true);
    });

    $(".btn-group.color_ramps .btn.color_ramps_off").click(function() {
        changeColorRampsMode(false);
    });

    $("#right_sidebar_content").click("svg", function(event) {
        // Don't do anything when clicking on lines.
        if ($(event.target).is("use")) {
            return;
        }
        var click_vertical_percent = (
            (event.pageY - $(this).get(0).offsetTop) / $(this).height()
        );

        if (click_vertical_percent < 0) {
            click_vertical_percent = 0.0;
        }
        else if (click_vertical_percent > 1.0) {
            click_vertical_percent = 1.0;
        }

        console.log("Clicked " + (click_vertical_percent * 100) + "% down the element.");
        var main_content_scroll_top = $("#main_content > .html_formatter").height() * click_vertical_percent;
        $("#main_content").get(0).scrollTop = main_content_scroll_top;
    });
}());
