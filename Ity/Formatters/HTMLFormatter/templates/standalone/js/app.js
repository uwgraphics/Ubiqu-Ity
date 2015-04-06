var pages_contains_filenames = false;
var current_page_index = -1;
var read_only_mode = false;
var ignored_read_only_mode = false;
var $prev = $(".page_window_prev");
var $curr = $(".page_window_current");
var $next = $(".page_window_next");
var scroll_lock = false;
if (typeof pages === "undefined") {
    var pages = null;
}
// a colorbrewer palette for default colors
var colors = [
    ["#8dd3c7", false],
    ["#ffffb3", false],
    ["#bebada", false],
    ["#fb8072", false],
    ["#80b1d3", false],
    ["#fdb462", false],
    ["#b3de69", false],
    ["#fccde5", false],
    ["#d9d9d9", false],
    ["#bc80bd", false],
    ["#ccebc5", false],
    ["#ffed6f", false]
];
var tag_keys_in_uri_params = [];
var tag_keys_with_weights = [];
var tag_keys_with_colors = [];

var tag_key_sort = function(a, b) {
    if (typeof tags === "object" && tags.hasOwnProperty(a) && tags[a].hasOwnProperty("num_tags") && tags.hasOwnProperty(b) && tags[b].hasOwnProperty("num_tags")) {
        var a_num = tags[a]["num_tags"];
        var b_num = tags[b]["num_tags"];

        if (a_num < b_num) {
            return -1;
        } else if (a_num == b_num) {
            return 0;
        } else if (a_num > b_num) {
            return 1;
        }
    }
    else {
        return 0;
    }
};

var initTagButtons = function() {
    $(".sidebar .tags").remove();
    var $tagContainer = $("<div class='tags'></div>");
    $tagContainer.appendTo(".sidebar");

    var tag_keys = Object.keys(tags);
    tag_keys.sort(tag_key_sort);
    tag_keys.reverse();

    for (var i = 0; i < tag_keys.length; i++) {
        var tag_key = tag_keys[i];
        var num_tags = tags[tag_key]["num_tags"];
        var span_contents = num_tags;
        if (tags[tag_key].hasOwnProperty("weight")) {
            var weight = tags[tag_key]["weight"];
            span_contents = "<strong>" + (weight > 0 ? "+" : "") + weight + "</strong> / " + num_tags;
        }
        var $tag_button = $("<a data-tag='" + tag_key + "' data-num_tags='" + num_tags + "'>" + tag_key + "<span>" + span_contents + "</span></a>");
        $tag_button.appendTo($tagContainer);
    }
};

var tagEvents = function() {
    $(".content .html_formatter").on("mouseover.standalone", " > span.tag", function() {
        var tag_keys = $(this).attr("data-key").split();
        if (typeof $(this).attr("title") === "undefined") {
            $(this).attr("title", $(this).attr("data-key"));
        }
        for (var i = 0; i < tag_keys.length; i++) {
            $(".sidebar .tags a[data-tag = '" + tag_keys[i] + "']").trigger("mouseover.standalone");
        }
    });
    $(".content .html_formatter").on("mouseout.standalone", " > span.tag", function() {
        var tag_keys = $(this).attr("data-key").split();
        for (var i = 0; i < tag_keys.length; i++) {
            $(".sidebar .tags a[data-tag = '" + tag_keys[i] + "']").trigger("mouseout.standalone");
        }
    });
    $(".content .html_formatter").on("click.standalone", " > span.tag", function() {
        // Disabled when we're in read-only mode.
        if (read_only_mode) {
            return;
        }
        var tag_keys = $(this).attr("data-key").split();
        for (var i = 0; i < tag_keys.length; i++) {
            $(".sidebar .tags a[data-tag = '" + tag_keys[i] + "']").trigger("click.standalone");
            if (i == 0) {
                $(".sidebar").clearQueue().animate({
                    scrollTop: $(".sidebar .tags a[data-tag = '" + tag_keys[i] + "']").get(0).offsetTop
                }, 500);
            }
        }
    });

    $(".content").on("scroll.standalone", function() {
        if (scroll_lock) {
            return;
        }
        scroll_lock = true;
        var scroll_pos = $(".content").scrollTop();
        if ($next.offset().top < 0 && current_page_index < pages.length - 1) {
            var prev_height = $prev.outerHeight();
            loadNextPage();
            $(".content").scrollTop(scroll_pos - prev_height);
        }
        else if ($curr.offset().top > 0 && current_page_index > 0) {
            loadPrevPage();
            var prev_height = $prev.outerHeight();
            $(".content").scrollTop(scroll_pos + prev_height);
        }
        setTimeout(function(){ scroll_lock = false; }, 0);
    });
};

var loadTags = function(filename, callback) {
    if (typeof filename === "undefined" || filename === null) {
        filename = "tags.json";
    }
    $.getJSON(filename, function(data) {
        tags = data;
        callback();
    });
};

var loadPageFilenames = function(filename, callback) {
    if (typeof filename === "undefined" || filename === null) {
        filename = "pages.json";
    }
    $.getJSON(filename, function(data) {
        pages = data;
        pages_contains_filenames = true;
        callback();
    });
};

var preInit = function() {
    if (typeof pages === "undefined" || pages === null) {
        loadPageFilenames(null, preInit);
    } else if (typeof tags === "undefined" || tags === null) {
        loadTags(null, preInit);
    } else {
        init();
    }
};

var init = function() {
    current_page_index = 0;
    console.log("Initializing...");
    initTags();
    loadPage();
    attachEvents();
};

var attachEvents = function() {

    $(".sidebar").on("mouseover.standalone", ".tags a", enableTagHighlight);
    $(".sidebar").on("mouseout.standalone", ".tags a", disableTagHighlight);
    $(".sidebar").on("click.standalone", ".tags a", toggleTagPersistentHighlight);
    $(".header .reset-tag-visibility").on("click.standalone", function() {
        if (read_only_mode) {
            return;
        }
        $(".sidebar .tags a.active").each(disableTagPersistentHighlight);
        initTags();
    });

    $("body").on("click.standalone", ".display-help", function(e) {
        e.preventDefault();
        showModal();
    });

    $("#modal").on("click.standalone", ".modal-close", function(e) {
        e.preventDefault();
        hideModal();
    });

    $("#modal").on("click.standalone", ".modal-send-feedback", updateFeedbackLink);
};

var updateFeedbackLink = function() {
    var current_href = $(this).attr("href").replace(/&body=.*$/, "");
    var body_contents = {};

    if (navigator.userAgent) {
        body_contents["User Agent"] = navigator.userAgent;
    }
    var processing_id = $("#processing_id").text();
    var processing_id_uri_match = current_href.match(/%20\(Processing%20ID:%20[^\)]+\)/);
    if (processing_id_uri_match.length == 1 && processing_id != "") {
        current_href = current_href.replace(processing_id_uri_match[0], "");
        body_contents["Processing ID"] = processing_id;
    }

    var uri_params_string = getURIParamsString();
    if (uri_params_string !== null && uri_params_string != "") {
        body_contents["URI Parameters"] = uri_params_string;
    }

    var body_string = "\n\n";

    for (line in body_contents) {
        if (! body_contents.hasOwnProperty(line)) {
            continue;
        }
        body_string += line + ": " + body_contents[line] + "\n";
    }
    body_string = body_string.replace(/ /, "%20").replace(/&/g, "%26").replace(/=/g, "%3D").replace(/\n/g, "%0D%0A");
    $(this).attr("href", current_href + "&body=" + body_string);
};

var showModal = function() {
    var $debug = $("#modal_debug");
    if (! $debug.get(0)) {
       $debug = $("<div id='modal_debug'></div>");
        $("#modal .message-body").append($debug);
    }
    $debug.html("");
    var $debug_heading = $("<h3>[Debug] URI Parameters</h3>");
    $debug.append($debug_heading);
    if (read_only_mode) {
        $debug.append("<p><strong>Read-Only Mode Enabled.</strong></p>");
    }
    else if (ignored_read_only_mode) {
        $debug.append("<p><strong>Ignoring Read-Only Mode</strong>: no valid tag parameters provided.</p>");
    }
    var $tag_params_list = $("<ul></ul>");
    for (tag_key in tags) {
        if (! tags.hasOwnProperty(tag_key) || ! tags[tag_key].hasOwnProperty("in_uri_params")) {
            continue;
        }
        var $list_item = $("<li></li>");
        var list_item_html = [
            "<strong>" + tag_key + "</strong>"
        ];
        var color = "#00aaff";
        var color_string = "<em>No Custom Color</em>";
        if (tags[tag_key].hasOwnProperty("color")) {
            var color = tags[tag_key]["color"];
            var color_string = color;
        }
        list_item_html.push("<span style='background-color:" + color + "; border-radius: 4px'>" + color_string + "</span>");

        if (tags[tag_key].hasOwnProperty("weight")) {
            var weight = tags[tag_key]["weight"];
            list_item_html.push((weight > 0 ? "+" : "") + weight + " Weight");
        }
        else {
            list_item_html.push("<em>No Weight</em>");
        }
        $list_item.html(list_item_html.join(" &middot; "));
        $tag_params_list.append($list_item);
    }
    if ($tag_params_list.html() != "") {
        $debug.append("<p>Recognized these tag parameters:</p>");
        $debug.append($tag_params_list);
    } else if (getURIParamsString() === null) {
        $debug.append("<p><em>No URI parameters were provided.</em></p>");
    } else if (read_only_mode || ignored_read_only_mode) {
        $debug.append("<p><em>Didn't recognize any tag-specific URI parameters (or no tag-specific parameters were provided).</em></p>");
    } else {
        $debug.append("<p><em>Didn't recognize any URI parameters.</em></p>");
    }
    $("#modal").fadeIn(500);
};

var hideModal = function() {
    $("#modal").fadeOut(500);
};

var loadPage = function(page_index) {
    console.log("loading page", page_index);
    if (typeof pages === "undefined" || pages === null) {
        throw "Cannot change pages; no page data available.";
    }
    if (typeof page_index === "undefined") {
        if (typeof current_page_index === "undefined") {
            throw "Cannot change pages; no page index provided.";
        }
        else {
            page_index = current_page_index;
        }
    }
    if (page_index < 0 || page_index >= pages.length) {
        throw "Cannot change pages; page index out of range.";
    }
    if (pages_contains_filenames) {
        $.get(pages[page_index], function(data) {
            loadPageCallback(page_index, data);
        });
    }
    else {
        loadPageCallback(page_index, pages);
    }
};

var loadPrevPage = function() {
    loadPage(current_page_index - 1);
};

var loadNextPage = function() {
    loadPage(current_page_index + 1);
};

var loadPageWindow = function(page_index, page_data) {
    if (page_index > 0) {
        $prev.html(page_data[page_index - 1]);
    } else {
        $prev.empty();
    }
    $curr.html(page_data[page_index]);
    if (page_index < page_data.length - 1) {
        $next.html(page_data[page_index + 1]);
    } else {
        $next.empty();
    }
};

var loadPageCallback = function(new_page_index, page_data) {
    if (new_page_index < 0 || new_page_index >= pages.length) {
        throw "New page index is invalid!";
    }
    loadPageWindow(new_page_index, page_data);
    current_page_index = new_page_index;
    tagEvents();
    $(".sidebar .tags a.highlight").trigger("mouseover.standalone");
    $(".sidebar .tags a.active").each(enableTagPersistentHighlight);
};

var addColor = function(tag_key) {
    for (var i = 0; i < colors.length; i++) {
        if (colors[i][1] === false) {
            tags[tag_key]["color"] = colors[i][0];
            colors[i][1] = tag_key;
            tag_keys_with_colors.push(tag_key);
            initTagColorsCSS(tag_keys_with_colors);
            break;
        }
    }
};

var removeColor = function(tag_key) {
    for (var i = 0; i < colors.length; i++) {
        if (colors[i][1] === tag_key) {
            delete tags[tag_key]["color"];
            colors[i][1] = false;
            tag_keys_with_colors.splice(tag_keys_with_colors.indexOf(tag_key), 1);
            initTagColorsCSS(tag_keys_with_colors);
            break;
        }
    }
};

var enableTagHighlight = function() {
    $(this).addClass("highlight");
    var tag_key = $(this).attr("data-tag");
    $(".html_formatter > span.tag[data-key = '" + tag_key + "']").addClass("highlight");
};

var disableTagHighlight = function() {
    $(this).removeClass("highlight");
    var tag_key = $(this).attr("data-tag");
    $(".html_formatter > span.tag[data-key = '" + tag_key + "']").removeClass("highlight");
};

var enableTagPersistentHighlight = function() {
    var tag_key = $(this).attr("data-tag");
    // only update a tag color if it doesn't has one
    if (tags[tag_key]["color"] === false) {
        if (tag_keys_in_uri_params.indexOf(tag_key) === -1) {
            addColor(tag_key);
        }
    }
    var $tags = $(".html_formatter > span.tag[data-key = '" + tag_key + "']");
    $(this).add($tags).addClass("active");
};

var disableTagPersistentHighlight = function() {
    // Disabled when we're in read-only mode.
    if (read_only_mode) {
        return;
    }
    var tag_key = $(this).attr("data-tag");
    if (tag_keys_in_uri_params.indexOf(tag_key) === -1) {
        removeColor(tag_key);
    }
    var $tags = $(".html_formatter > span.tag[data-key = '" + tag_key + "']");
    $(this).add($tags).removeClass("active");
};

var toggleTagPersistentHighlight = function() {
    // Disabled when we're in read-only mode.
    if (read_only_mode) {
        return;
    }
    var tag_key = $(this).attr("data-tag");
    var $tags = $(".html_formatter > span.tag[data-key = '" + tag_key + "']");
    if ($(this).hasClass("active")) {
        if (tag_keys_in_uri_params.indexOf(tag_key) === -1) {
            removeColor(tag_key);
        }
        $(this).add($tags).removeClass("active");
    }
    else {
        if (tag_keys_in_uri_params.indexOf(tag_key) === -1) {
            addColor(tag_key);
        }
        $(this).add($tags).addClass("active");
    }
};

var initTags = function() {

    var handleTagParams = function(uri_param) {
        // Split &-delimited params into [tag_key]=[color][+/- weight], where
        // + or - represents the weight's sign and the delimiter of interest
        // between the color and the weight value.
        var tag_params = uri_param.match(/^[^=]*|[+-][\de+-\.]+$|(?!=)[^+-]+/g);
        var tag_key = null;
        var tag_color = null;
        var tag_weight = null;
        if (tag_params.length > 0) {
            tag_key = tag_params[0];
        }
        if (tag_params.length > 1) {
            tag_color = tag_params[1];
        }
        if (tag_params.length > 2) {
            tag_weight = parseFloat(tag_params[2]);
        }
        // Record information.
        if (tag_key !== null && tags.hasOwnProperty(tag_key)) {
            tag_keys_in_uri_params.push(tag_key);
            tags[tag_key]["in_uri_params"] = true;
            if (tag_color !== null) {
                // Correct for mangling of HTML colors with pound signs.
                if (tag_color.substring(0,3) == "%23") {
                    tag_color = "#" + tag_color.substring(3);
                }
                tags[tag_key]["color"] = tag_color;
                tag_keys_with_colors.push(tag_key);
            }
            if (tag_weight !== null && ! isNaN(tag_weight)) {
                tags[tag_key]["weight"] = tag_weight;
                tag_keys_with_weights.push(tag_key);
            }
        }
    };

    for (var i = 0; i < colors.length; i++) {
        var tag_key = colors[i][1];
        if (tag_key !== false) {
            delete tags[tag_key]["color"];
            colors[i][1] = false;
        }
    }
    tag_keys_in_uri_params = [];
    tag_keys_with_weights = [];
    tag_keys_with_colors = [];

    /* Lights, camera, action. */
    var uri_params = getURIParams();
    // Bail out if we didn't get any URI parameters.
    if (uri_params === null) {
        uri_params = [];
    }
    var potentially_enable_read_only = false;

    for (var i = 0; i < uri_params.length; i++) {
        var uri_param = uri_params[i];
        if (uri_param == "readonly") {
            potentially_enable_read_only = true;
        }
        else {
            handleTagParams(uri_param);
        }
    }

    // Should we enable read-only mode?
    // Only enable read-only if there were actually tags in uri_params.
    // Otherwise we get an empty sidebar, which is completely useless.
    if (potentially_enable_read_only) {
        if (tag_keys_in_uri_params.length > 0) {
            read_only_mode = true;
            $("body").addClass("read-only");
            $("title").append(" (Read-Only Mode)");
        }
        else {
            ignored_read_only_mode = true;
        }
    }

    initTagColorsCSS(tag_keys_with_colors);
    initTagButtons();

    for (var tag_key in tags) {
        if (! tags.hasOwnProperty(tag_key)) {
            continue;
        }
        var $tag_button_in_sidebar = $(".sidebar .tags a[data-tag = '" + tag_key + "']");
        /* Enable this tag's persistent highlight if it appeared in uri_params. */
        if (tag_keys_in_uri_params.indexOf(tag_key) > -1) {
            $tag_button_in_sidebar.each(enableTagPersistentHighlight);
        }
        /* If we're in read-only mode, hide tag buttons that didn't appear in uri_params. */
        else if (read_only_mode) {
            $tag_button_in_sidebar.hide();
        }
    }
};

var getURIParamsString = function() {
    var uri_question_mark_index = window.location.href.indexOf("?");
    if (uri_question_mark_index > -1) {
        uri_params_string = window.location.href.substr(uri_question_mark_index + 1);
        if (uri_params_string != "") {
            return uri_params_string;
        }
    }
    return null;
};

var getURIParams = function() {
    var uri_params_string = getURIParamsString();
    if (uri_params_string !== null && uri_params_string != "") {
        return uri_params_string.split("&");
    }
    return null;
};

var initTagColorsCSS = function(tag_keys_with_colors) {
    $("#standaloneTagColors").remove();
    var styles = "";
    for (var i = 0; i < tag_keys_with_colors.length; i++) {
        var tag_key = tag_keys_with_colors[i];
        if (! tags.hasOwnProperty(tag_key)) continue;
        if (tags[tag_key].hasOwnProperty("color")) {
            styles += ".sidebar .tags a[data-tag = '" + tag_key + "'] span { background-color: " + tags[tag_key]["color"] + "; color: #000; } .sidebar .tags a[data-tag = '" + tag_key + "'].active, .content .html_formatter > span.tag[data-key = '" + tag_key + "'].active { background: " + tags[tag_key]["color"] + "; }";
        }
    }
    var $styleElement = "<style id='standaloneTagColors' type='text/css'>" + styles + "</style>";
    $("head").append($styleElement);
};

preInit();
