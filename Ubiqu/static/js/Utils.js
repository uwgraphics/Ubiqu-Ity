/**
 * Created with PyCharm.
 * User: ealexand
 * Date: 3/5/13
 * Time: 3:43 PM
 * To change this template use File | Settings | File Templates.
 */

// TOPICVIEW VARS
var utilsNS = {};
utilsNS.barGirth = 10;
utilsNS.barLength = 50;
utilsNS.maxBarWidth = 50;
utilsNS.barHeight = 10;
utilsNS.barBuffer = 3;
utilsNS.barXoffset = 100;
utilsNS.barYoffset = 0;
utilsNS.w = 300;
utilsNS.h = 300;
utilsNS.barFill = 'red';
utilsNS.barBorder = 'black';
utilsNS.barFillOpacity = .6;
utilsNS.numWords = 20;

var genTopicView = function(corpusName, topicNum, containerID, topicName) {
    if (topicName === undefined) {
        topicName = 'Topic ' + topicNum;
    }
    d3.select(containerID).html('<h4>Topic: ' + topicName + '</h4>');

    var $TOPIC_URL = flask_util.url_for('corpus_get_topic',
        {corpus_name:corpusName,
            topic_num: topicNum === 0 ? '0' : topicNum, // Cheap hack--I think flask_util.url_for can't deal with 0 as a parameter
            num_words:utilsNS.numWords});
    d3.json($TOPIC_URL, function(json) {
        if (json == null) {
            d3.select('#topicView').append('div')
                .attr('class', 'alert alert-block')
                .html('Topic data not found.');
        } else {
            var wordList = json.wordList;
            var propList = json.propList;
            makeBarGraph(containerID, wordList, propList, false);
        }
    });
};

var genWordView = function(corpusName, textName, word, wordEl) {
    // Chances are this is going into a popover element associated with wordEl.
    var containerPopover = $(wordEl).data().popover.$tip.get(0);

    var $WORD_TOPICS_URL =
        flask_util.url_for('text_get_topics_for_word', {corpus_name:corpusName, text_name: textName, word:word});
    d3.json($WORD_TOPICS_URL, function(json) {
        var word_props = json[word].slice(0, utilsNS.numWords);
        var labelData = new Array(word_props.length);
        var barData = new Array(word_props.length);
        for (var i = 0; i < word_props.length; i++) {
            labelData[i] = word_props[i][0];
            barData[i] = word_props[i][1];
        }
        // Get the D3 selection containing the DOM tree that makeBarGraph() created.
        var barGraphEl = makeBarGraph(null, labelData, barData, false);
        // Modify the wordEl popover's HTML content.
        if (containerPopover) {
            $(wordEl).data().popover.options.content = barGraphEl.html();
            // Call popover("show") to update the popover's content, position, and size.
            $(wordEl).popover("show");
        }
    });
};

var makeBarGraph = function(containerID, labels, data, isVertical, clickFxn, mouseoverFxn, mouseoutFxn, colorFxn) {
    var barScale = d3.scale.linear()
        .domain([0, Math.max.apply(null, data)])
        .range([0, utilsNS.barLength]);

    var viewContainer;

    if (containerID === null) {
        viewContainer = d3.select(document.createElement("div"));
    }
    else {
        viewContainer = d3.select(containerID);
    }

    viewContainer.classed("barGraphContainer", true);

    // Clear the view's contents and append an <svg> element with a fixed width.
    var view = viewContainer.html('')
        .append('svg:svg')
        .attr("width", 16 * 2 + (utilsNS.barGirth + utilsNS.barBuffer) * data.length + "px")
        .attr("height", (utilsNS.maxBarWidth + 2*32) + "px");

    var label = view.selectAll('.label')
        .data(labels);
    label.enter().append('svg:text')
        .attr('class', 'label')
        .text(function(d) { return d; });
    label.exit().remove();

    var bar = view.selectAll('.bar')
        .data(data);
    bar.enter().append('svg:rect')
        .attr("data-key", function(d,i) { return "topic_" + labels[i]; })
        .attr('class', 'bar')
        .style('stroke', utilsNS.barBorder)
        /*.on('click', clickFxn)
        .on('mouseover', mouseoverFxn)
        .on('mouseout', mouseoutFxn)*/;
    bar.exit().remove();

    if (isVertical) {
        label
            .attr('x', utilsNS.barXoffset - utilsNS.barBuffer)
            .attr('y', function(d,i) { return utilsNS.barYoffset + (i + 1)*(utilsNS.barBuffer + utilsNS.barHeight); })
            .attr('text-anchor', 'end')
            .attr('alignment-baseline', 'middle');
        bar
            .attr('x', utilsNS.barXoffset + utilsNS.barBuffer)
            .attr('y', function(d,i) { return (i + 1)*(utilsNS.barBuffer + utilsNS.barGirth) - .5*(utilsNS.barGirth); })
            .attr('width', function(d) { return barScale(d); })
            .attr('height', utilsNS.barGirth);
    } else {
        label
            .attr('x', function(d,i) { return (i + 1)*(utilsNS.barBuffer + utilsNS.barGirth) })
            .attr('y', 2*utilsNS.barBuffer + utilsNS.barLength)
            .attr('text-anchor', 'start')
            .attr('alignment-baseline', 'middle')
            .attr('transform', function() {
                var tmp = d3.select(this);
                return 'rotate(60 ' + tmp.attr('x') + ' ' + tmp.attr('y') + ')';
            });
        bar
            .attr('x', function(d,i) { return (i + 1)*(utilsNS.barBuffer + utilsNS.barGirth) - .5*(utilsNS.barGirth); })
            .attr('y', function(d) { return utilsNS.barBuffer + utilsNS.barLength - barScale(d); })
            .attr('width', utilsNS.barGirth)
            .attr('height', function(d) { return barScale(d); });
    }
    // Retun the D3 selection containing the view.
    return viewContainer;
};

var sortInnerShapes = function() {
    d3.selectAll('.innerShape').sort(function(a,b) {
        if ('q' in a && !('q' in b)) {
            return -1;
        } else if (!('q' in a) && 'q' in b) {
            return 1;
        } else {
            return 0;
        }
    });
};