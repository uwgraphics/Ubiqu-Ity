/**
 * Created with PyCharm.
 * User: ealexand
 * Date: 3/12/13
 * Time: 5:50 PM
 * To change this template use File | Settings | File Templates.
 */

//var loadTextLineGraphs = function() {
//    $(".meso_container .meso_view").each(loadTextLineGraph());
//};

var meso_loadTextLineGraph = function() {
    var that = this;
    $(".content", that).addClass("withLoadingIndicator");
    var text_name = $(this).attr("data-text-name");
    if (text_name === undefined || text_name == "") {
        throw ".meso_view missing a valid 'data-text-name' attribute."
    }
    var pixel_size = $(that).height();
    var line_graph_url = flask_util.url_for(
        "text_get_topic_model_line_graph",
        {
            corpus_name: corpus_name,
            text_name: text_name,
            pixel_size: pixel_size
        }
    );
    $.get(line_graph_url, function(response) {
        // Why not this?
        // var $response_container = $(response);
        var $response_container = $("<div></div>").html(response);
        var $response_svg = $("svg", $response_container);
        var text_name = $response_svg.attr("data-text-name");
        if (text_name === undefined || text_name == "") {
            throw ".topic_model_line_graph missing a valid 'data-text-name' attribute."
        }
        // Replace the HTML content of that element's ".content" with the SVG.
        $(".meso_container .meso_view[data-text-name='" + text_name + "'] .content").html($response_svg).removeClass("withLoadingIndicator");
        // Attach events.
        meso_attachLineGraphEventsToElement($response_svg.get(0));
    });
};

/* Crap, global namespacing (or lack thereof) is now becoming an issue. */
var meso_attachLineGraphEventsToElement = function(el) {
    // call TextViewer.js's attach function.
    attachLineGraphEventsToElement(el);
};

// Attach event listeners / execute other initialization code.
(function() {
    $(".meso_container .meso_view").each(meso_loadTextLineGraph);
}());
