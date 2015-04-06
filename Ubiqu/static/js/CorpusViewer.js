var state = new Object(); // This might need an init function of its own.
state.drawByQuartiles = true;
state.colorEncoding = 'cat';
state.signEncoding = 'none';
state.sortOrderVar = 1; // TODO: Add this to settings menu
state.colorByRows = true;
var transdur = 1000; // Duration of transitions
var gridcolor = 'lightgray';
var gridWidth = 1;
var colors = new Object();
colors.topics = [];
colors.cat = ['#E41A1C', '#377EB8', '#4DAF4A', '#984EA3', '#FF7F00', '#FFFF33', '#A65628', '#F781BF', '#999999']; // ColorBrewer 9-class Set 1 Qualitative
colors.div = ['#B2182B', '#D6604D', '#F4A582', '#FDDBC7', '#F7F7F7', '#D1E5F0', '#92C5DE', '#4393C3', '#2166AC']; // ColorBrewer 11-class Red-Blue Diverging (top and bottom removed)
colors.seq = ['#F7FCF5', '#E5F5E0', '#C7E9C0', '#A1D99B', '#74C476', '#41AB5D', '#238B45', '#006D2C', '#00441B']; // ColorBrewer 9-class Greens Sequential
var defaultColor = '#FFFF33';

var matrixSeparation = 20; //TODO: Make this dynamic
var aggSizeFactor = 3;

// matrixView VARS
var mvNS = new Object();
mvNS.minW = $('#matrixView').parent().width()-25;
mvNS.minH = $('#matrixView').parent().height()-25;
mvNS.buffer = 10;
mvNS.minR = 2;
mvNS.maxR = matrixSeparation / 2;
mvNS.highlightBarHeight = matrixSeparation - 2;
mvNS.minFill = .2;
mvNS.midFill = .6;
mvNS.maxFill = .9;
mvNS.rScale = d3.scale.linear()
    .domain([0,1])
    .range([mvNS.minR, mvNS.maxR]);
mvNS.areaScale = d3.scale.linear()
    .domain([0,1])
    .range([Math.pow(mvNS.minR, 2), Math.pow(mvNS.maxR, 2)]); // Notice: not including Pi because we'll just factor it out

// DOCVIEW VARS
var dvNS = new Object(); // Document View Namespace
dvNS.labelBuffer = 30;
dvNS.barFill = 'red';
dvNS.barBorder = 'black';
dvNS.barFillOpacity = .6;
dvNS.barBuffer = 10;
dvNS.chartBuffer = 10;
dvNS.titleBuffer = 10;
dvNS.minBarWidth = 15;

// TOPICVIEW VARS
var tvNS = new Object();
tvNS.maxBarWidth = 50;
tvNS.barHeight = 10;
tvNS.barBuffer = 3;
tvNS.barXoffset = 100;
tvNS.barYoffset = 20;
tvNS.w = 300;
tvNS.h = 300;
tvNS.barFill = 'red';
tvNS.barBorder = 'black';
tvNS.barFillOpacity = .6;
tvNS.numWords = 20;

var matrixView, docView, topicView;

var initialize = function() {
    $("#main_content").addClass("withLoadingIndicator");
    initContextMenus();
    initColorPickers();
    //initSidebarFunctions(); // This needs to happen after the data has been pulled in.
    initMatrixView();
};

var initMatrixView = function() {
    matrixView = d3.select('#matrixView').html('').append('svg:svg')
        .attr('width', mvNS.w)
        .attr('height', mvNS.h)
};

var initSettings = function() {
    var docLabelSelect = $('#metadataDocLabelSelect');
    docLabelSelect.hide();
    // Fill the metadata select dropdown
    var metadataName;
    for (var i = 0; i < state.metadataNames.length; i++) {
        metadataName = state.metadataNames[i];
        d3.select('#metadataDocLabelSelect').append('option')
            .property('value', metadataName)
            .property('name', metadataName)
            .text(metadataName);
    }
    // Turn on functionality
    $('input[name="docLabelsRadios"]').change(function() {
        if ($(this).attr('id') == 'autoDocLabels') {
            docLabelSelect.hide();
            for (var i = 0; i < state.rowList.length; i++) {
                state.rowList[i] = 'Document ' + i;
            }
        } else if ($(this).attr('id') == 'metadataDocLabels') {
            docLabelSelect.show();
            var nameField = docLabelSelect.val();
            for (var i = 0; i < state.rowList.length; i++) {
                state.rowList[i] = state.metadata[i][nameField];
            }
        }
        if (state.aggregatingBy == undefined) {
            d3.selectAll('.rowLabel').text(function(d) { return state.rowList[d]; });
        }
        state.docLabelsChanged = true;
    });
    docLabelSelect.change(function() {
        var nameField = docLabelSelect.val();
        for (var i = 0; i < state.rowList.length; i++) {
            state.rowList[i] = state.metadata[i][nameField];
        }
        if (state.aggregatingBy == undefined) {
            d3.selectAll('.rowLabel').text(function(d) { return state.rowList[d]; });
        }
        state.docLabelsChanged = true;
    });
    $('#settingsModal').on('hide', function() {
        if (state.docLabelsChanged) {
            updateMatrixView();
            state.docLabelsChanged = false;
        }
    })
};

var initContextMenus = function() {
    d3.select('#sortByRow')
        .on('click', function() {
            sortColsBy([state.selectedRow]);
            $('#rowContextMenu').hide();
        });

    var rowColorDropdown = d3.select('#rowColorDropdown');
    var currColor;
    for (var i = 0; i < colors.cat.length; i++) {
        currColor = colors.cat[i];
        rowColorDropdown.append('li').append('a')
            .attr('tabindex', '-1')
            .attr('href', '#')
            .style('color', currColor)
            .text(currColor)
            .on('click', function() {
                colorRows([state.selectedRow], d3.select(this).text());
                $('#rowContextMenu').hide();
            });
    }

    var colColorDropdown = d3.select('#colColorDropdown');
    var currColor;
    for (var i = 0; i < colors.cat.length; i++) {
        currColor = colors.cat[i];
        colColorDropdown.append('li').append('a')
            .attr('tabindex', '-1')
            .attr('href', '#')
            .style('color', currColor)
            .text(currColor)
            .on('click', function() {
                colorCols([state.selectedCol], d3.select(this).text());
                $('#colContextMenu').hide();
            });
    }

    d3.select('#sortByDistFromRow')
        .on('click', function() {
            sortRowsByDistanceFrom(state.selectedRow);
            $('#rowContextMenu').hide();
        });

    d3.select('#hideRow')
        .on('click', function() {
            hideRows([state.selectedRow]);
            $('#rowContextMenu').hide();
        });

    d3.select('#openGroup')
        .on('click', function() {
            // TODO: only works if we're aggregating
            hideRowsNotIn([state.selectedRow]);
            state.aggregatingBy = undefined;

            // Set currData to just include the selected aggregate and then unaggregate
            setTimeout(function() {
                state.currRowOrder = state.aggregates[state.selectedRow];
                state.currData = [];
                var currDoc;
                for (var i = 0; i < state.currRowOrder.length; i++) {
                    currDoc = state.theta[state.currRowOrder[i]];
                    for (var topicID in currDoc) {
                        topicID = parseInt(topicID);
                        if (state.currColOrder.indexOf(topicID) != -1) {
                            state.currData.push({
                                col: topicID,
                                row: state.currRowOrder[i],
                                prop: currDoc[topicID]
                            });
                        }
                    }
                }
                unaggregate();
            }, transdur);
            // This may be faster, but isn't animated as well:
            //setTimeout(function() {hideRowsNotIn(state.aggregates[state.selectedRow]);}, transdur);

            $('#rowContextMenu').hide();
        });

    d3.select('#openGroupInMeso')
        .on('click', function() {
            openDocsInMesoViewer(state.aggregates[state.selectedRow]);
        });

    d3.select('#openInTextViewer')
        .on('click', function() {
            openDocInTextViewer(state.selectedRow);
            $('#rowContextMenu').hide();
        });

    d3.select('#sortByCol')
        .on('click', function() {
            sortRowsBy([state.selectedCol]);
            $('#colContextMenu').hide();
        });

    d3.select('#hideCol')
        .on('click', function() {
            hideCols([state.selectedCol]);
            $('#colContextMenu').hide();
        });

    d3.select('#renameCol')
        .on('click', function() {
            $('#colContextMenu').hide();
        });

    d3.select('#renameTopicSubmit')
        .on('click', function() {
            var newName = $('#newTopicName').val();
            if (newName != '') {
                state.colList[state.selectedCol] = newName;
                matrixView.selectAll('.colLabel').text(function(d) { return state.colList[d]; });
                renderTopicView(state.selectedCol);
            }
            $('#renameTopicModal').modal('hide');
            $('#newTopicName').val('');
        });

    d3.select('#renameTopicCancel,#renameTopicDismiss')
        .on('click', function() {
            $('#newTopicName').val('');
        });
};

var initColorPickers = function() {
    $('#colorSelection').popover({ html:true, content:'<div id="rowColorPickerFloat"></div>', placement:'top'});

    var bgColor = "lightgrey";
    var cpWidth = 45;
    var cpHeight = 45;
    var cpBuffer = 2;
    var colorsPerRow = 3;
    var numRows = Math.ceil(colors.cat.length / colorsPerRow);
    var colorWidth = (cpWidth / colorsPerRow) - 2*cpBuffer;
    var colorHeight = (cpHeight / numRows) - 2*cpBuffer;

    d3.select('#colorSelection')
        .on('click', function() {
            d3.select("#rowColorPickerFloat")
                .append('svg:svg')
                .attr('width', cpWidth)
                .attr('height', cpHeight)
                .selectAll('rect').data(colors.cat)
                .enter().append('svg:rect')
                .attr('x', function(d, i) { return cpBuffer + (i % colorsPerRow)*(cpWidth / colorsPerRow); })
                .attr('y', function(d, i) { return cpBuffer + Math.floor(i / numRows)*(cpHeight / numRows); })
                .attr('width', colorWidth)
                .attr('height', colorHeight)
                .style('stroke', 'black')
                .style('fill', function(d) { return d; })
                .on('click', function(d) {
                    //colorRows([state.selectedRow], d);
                    colorRows(state.selectedRows, d);
                    selectRow(state.selectedRow);
                    $('#colorSelection').popover('hide');
                });
        });

    $('#topicColorSelection').popover({ html:true, content:'<div id="colColorPickerFloat"></div>', placement:'top'});

    var bgColor = "lightgrey";
    var cpWidth = 45;
    var cpHeight = 45;
    var cpBuffer = 2;
    var colorsPerRow = 3;
    var numRows = Math.ceil(colors.cat.length / colorsPerRow);
    var colorWidth = (cpWidth / colorsPerRow) - 2*cpBuffer;
    var colorHeight = (cpHeight / numRows) - 2*cpBuffer;

    d3.select('#topicColorSelection')
        .on('click', function() {
            d3.select("#colColorPickerFloat")
                .append('svg:svg')
                .attr('width', cpWidth)
                .attr('height', cpHeight)
                .selectAll('rect').data(colors.cat)
                .enter().append('svg:rect')
                .attr('x', function(d, i) { return cpBuffer + (i % colorsPerRow)*(cpWidth / colorsPerRow); })
                .attr('y', function(d, i) { return cpBuffer + Math.floor(i / numRows)*(cpHeight / numRows); })
                .attr('width', colorWidth)
                .attr('height', colorHeight)
                .style('stroke', 'black')
                .style('fill', function(d) { return d; })
                .on('click', function(d) {
                    //colorRows([state.selectedRow], d);
                    if (state.selectedCols != undefined && state.selectedCols.length != 0) {
                        colorCols(state.selectedCols, d);
                        selectCol(state.selectedCol);
                    }
                    $('#topicColorSelection').popover('hide');
                });
        });
};

var initSidebarFunctions = function() {
    // Above matrixView
    d3.select('#hideEmptyTopics')
        .on('click', function() {
            hideEmptyCols();
        });
    d3.select('#resetColors')
        .on('click', function() {
            resetColors();
        });
    d3.select('#resetOrders')
        .on('click', function() {
            resetOrders();
        });

    // "Close" buttons for docView and topicView
    d3.select('#hideSelectedTopic')
        .on('click', function() {
            if (state.selectedCol != undefined) {
                hideCols([state.selectedCol]);
                d3.select('#topicMetadataTab').html('No topic selected.');
                d3.select('#topicView').html('No topic selected.');
            }
        });
    d3.select('#hideSelectedDoc')
        .on('click', function() {
            if (state.selectedRow != undefined) {
                hideRows([state.selectedRow]);
                d3.select('#docMetadataTab').html('No document selected.');
                d3.select('#docTopicLayoutTab').html('No document selected.');
                d3.select('#docTopicCountsTab').html('No document selected.');
            }
        });

    // Topic Sorting
    var topicSortSelect = d3.select('#topicSortSelect');
    var topicMetadataName;
    for (var i = 0; i < state.topicMetadataNames.length; i++) {
        topicMetadataName = state.topicMetadataNames[i];
        topicSortSelect.append('option')
            .property('value', topicMetadataName)
            .property('name', topicMetadataName)
            .text(topicMetadataName);
    }
    topicSortSelect.on('change', function() {
        var fieldName = d3.select(this).property('value');
        if (state.topicMetadataNames.indexOf(fieldName) == -1) {
            state.currColOrder.sort(function(a,b) {return a-b;});
            updateMatrixView();
        } else {
            sortColsByMetadata(fieldName);
        }
    });

    // Topic Selection
    // TODO: Include advanced select for topics
    /*
    buildMetadataForm('topicAdvancedSelectBody');
    d3.select('#topicAdvancedSelectSubmit')
        .on('click', function() {
            var form = getObjectFromForm('advancedSelectBody');
            var sel = getSelectionFromForm(form);
            state.selectedRows = sel;
            updateRowSelectDiv();
            //$('#advancedSelectBody .collapse').collapse('hide');
            $('#advancedSelectBody input').val('');
            $('#advancedSelectBody select').val('');
            $('#advancedSelectModal').modal('hide');
        });*/
    d3.select('#moveSelectionToLeft')
        .on('click', function() {
            moveColsToLeft(state.selectedCols);
        });
    d3.select('#sortDocsBySelection')
        .on('click', function() {
            sortRowsBy(state.selectedCols);
        });
    d3.select('#clearColSelection')
        .on('click', function() {
            state.selectedCols = [];
            updateColSelectDiv();
        });
    d3.select('#hideTopicSelection')
        .on('click', function() {
            hideCols(state.selectedCols);
            state.selectedCols = [];
            updateColSelectDiv();
        });
    d3.select('#hideAllTopicsButSelection')
        .on('click', function() {
            hideColsNotIn(state.selectedCols)
        });

    // Doc Sorting
    var sortSelect = d3.select('#sortSelect');
    var metadataName;
    for (var i = 0; i < state.metadataNames.length; i++) {
        metadataName = state.metadataNames[i];
        sortSelect.append('option')
            .property('value', metadataName)
            .property('name', metadataName)
            .text(metadataName);
    }
    sortSelect.on('change', function() {
        var fieldName = d3.select(this).property('value');
        if (state.metadataNames.indexOf(fieldName) == -1) {
            state.currRowOrder.sort(function(a,b) {return a-b;});
            updateMatrixView();
        } else {
            sortRowsByMetadata(fieldName);
        }
    });

    // Aggregating
    $('#clearAggDiv').hide();
    var aggSelect = d3.select('#aggregateSelect');
    var metadataName;
    var metadataType;
    for (var i = 0; i < state.metadataNames.length; i++) {
        metadataName = state.metadataNames[i];
        metadataType = state.metadataTypes[i];
        if (metadataType != 'str') {
            aggSelect.append('option')
                .property('value', metadataName)
                .property('name', metadataName)
                .text(metadataName);
        }
    }
    // TODO: we need reset the aggregation select field if they cancel
    aggSelect.on('change', function() {
        if (state.aggregatingBy != undefined) {
            unaggregate();
        }
        var fieldName = d3.select(this).property('value');
        if (fieldName == 'None') {
            unaggregate();
        } else {
            var fieldType = state.metadataTypes[state.metadataNames.indexOf(fieldName)];
            // If fieldType is integer, we need to get group threshold
            if (fieldType == 'int') {
                state.tempField = fieldName;
                $('#aggIntModal').modal('show');
            } else {
                aggregateBy(fieldName);
            }
        }
    });
    $('#aggIntSubmit').on('click', function() {
        $('#aggIntModal').modal('hide');
        aggregateBy(state.tempField, parseInt($('#aggChunkSize').val()), parseInt($('#aggStartingFrom').val()));
        state.tempField = undefined;
    });
    $('#clearAggregation').on('click', function() {
        unaggregate();
    });

    // Filtering // TODO: make the accordions collapse when modal closes
    buildMetadataForm('addFilterBody');
    d3.select('#addFilterSubmit')
        .on('click', function() {
            var form = getObjectFromForm('addFilterBody');
            var sel = getSelectionFromForm(form);
            createFilter(sel, form);
            $('#addFilterModal').modal('hide');
            //$('#addFilterBody .collapse').collapse('hide');
            $('#addFilterBody input').val('');
            $('#addFilterBody select').val('');
        });

    // Selection // TODO: make the accordions collapse when modal closes
    buildMetadataForm('advancedSelectBody');
    d3.select('#advancedSelectSubmit')
        .on('click', function() {
            var form = getObjectFromForm('advancedSelectBody');
            var sel = getSelectionFromForm(form);
            state.selectedRows = sel;
            updateRowSelectDiv();
            //$('#advancedSelectBody .collapse').collapse('hide');
            $('#advancedSelectBody input').val('');
            $('#advancedSelectBody select').val('');
            $('#advancedSelectModal').modal('hide');
        });
    d3.select('#moveSelectionToTop')
        .on('click', function() {
            moveRowsToTop(state.selectedRows);
        });
    d3.select('#sortBySelection')
        .on('click', function() {
            sortColsBy(state.selectedRows);
        });
    d3.select('#clearRowSelection')
        .on('click', function() {
            state.selectedRows = [];
            updateRowSelectDiv();
        });
    d3.select('#hideSelection')
        .on('click', function() {
            hideRows(state.selectedRows);
            state.selectedRows = [];
            updateRowSelectDiv();
        });
    d3.select('#hideAllButSelection')
        .on('click', function() {
            hideRowsNotIn(state.selectedRows)
        });
    d3.select('#openSelectionInMeso')
        .on('click', function() {
            openDocsInMesoViewer(state.selectedRows);
        });

    // Toggling
    d3.select('#toggleColorByColBtn')
        .on('click', function() {
            event.preventDefault();
            toggleColorBy('cols');
        });

    d3.select('#toggleColorByRowBtn')
        .on('click', function() {
            event.preventDefault();
            toggleColorBy('rows');
        });
};

var aggregateBy = function(fieldName, chunkSize, startingFrom) {
    $('#clearAggDiv').show();
    $('#sortSelect').val('None'); // Sorting doesn't really make sense after aggregating
    $('#openGroup').parent().removeClass('disabled'); // Enable option to drill down into a group
    $('#openGroupInMeso').parent().removeClass('disabled');
    $('#openInTextViewer').parent().addClass('disabled');
    state.aggregatingBy = fieldName;
    state.aggList = [];
    state.aggregates = [];
    state.docToAgg = new Array(state.rowList.length); // This will later let us match docs to their new agg
    // Categorical aggregation
    if (chunkSize == undefined) {
        var currMeta, fieldNameIndex;
        for (var docNum = 0; docNum < state.metadata.length; docNum++) {
            currMeta = state.metadata[docNum];
            fieldNameIndex = state.aggList.indexOf(currMeta[fieldName]);
            if (fieldNameIndex == -1) {
                state.docToAgg[docNum] = state.aggList.length;
                state.aggList.push(currMeta[fieldName])
                state.aggregates.push([docNum])
            } else {
                state.docToAgg[docNum] = fieldNameIndex;
                state.aggregates[fieldNameIndex].push(docNum);
            }
        }
    }
    // Numerical aggregation
    else {
        // Store docs in a sparse array of chunks
        var currMeta, currField, currMin, chunkIndex;
        var tmpAggs = [];
        var tmpAggList = [];
        var preAgg = [];
        for (var docNum = 0; docNum < state.metadata.length; docNum++) {
            currMeta = state.metadata[docNum];
            currField = parseInt(currMeta[fieldName]);
            if (currField - startingFrom < 0) {
                preAgg.push(docNum);
            } else {
                currMin = currField - ((currField - startingFrom) % chunkSize);
                chunkIndex = Math.floor((currField - startingFrom) / chunkSize);
                if (tmpAggs[chunkIndex] == undefined) {
                    tmpAggList[chunkIndex] = fieldName + ': ' + currMin + '-' + (currMin + chunkSize - 1);
                    tmpAggs[chunkIndex] = [docNum];
                } else {
                    tmpAggs[chunkIndex].push(docNum);
                }
            }
        }
        // Flatten out undefined chunks
        if (preAgg.length > 0) {
            state.aggregates.push(preAgg);
            state.aggList.push(fieldName + ': <' + startingFrom);
        }
        for (var i = 0; i < tmpAggList.length; i++) {
            if (tmpAggList[i] != undefined) {
                state.aggregates.push(tmpAggs[i]);
                state.aggList.push(tmpAggList[i]);
            }
        }
        // Instantiate docToAgg
        for (var i = 0; i < state.aggregates.length; i++) {
            for (j = 0; j < state.aggregates[i].length; j++) {
                state.docToAgg[state.aggregates[i][j]] = i;
            }
        }
    }
    // Now have aggregates, combine their data.
    state.aggData = [];
    state.aggTheta = []; // This is an association of doc to {topicID -> prop} objects
    state.aggColors = new Array(state.aggregates.length);
    state.aggsColored = new Array(state.aggregates.length);
    state.aggIQRs = [];
    var currTopicProps, currDoc, currAggPropTotal, currProp, currDocTopicProp;
    for (var aggIndex = 0; aggIndex < state.aggregates.length; aggIndex++) {
        // Combine aggregates
        state.aggTheta.push({});
        state.aggIQRs.push({});
        currAggPropTotal = 0.0;
        currTopicProps = {};
        for (var i = 0; i < state.aggregates[aggIndex].length; i++) {
            currDoc = state.aggregates[aggIndex][i];
            for (var topicID in state.theta[currDoc]) {
                currDocTopicProp = state.theta[currDoc][topicID];
                if (currTopicProps[topicID] == undefined) {
                    currTopicProps[topicID] = currDocTopicProp;
                } else {
                    currTopicProps[topicID] += currDocTopicProp;
                }
                if (state.aggIQRs[aggIndex][topicID] == undefined) {
                    state.aggIQRs[aggIndex][topicID] = [currDocTopicProp];
                } else {
                    state.aggIQRs[aggIndex][topicID].push(currDocTopicProp)
                }
                currAggPropTotal += currDocTopicProp;
            }
            if (state.rowsColored.indexOf(currDoc) != -1) {
                if (state.aggColors[aggIndex] == undefined) {
                    state.aggsColored[aggIndex] = true;
                    state.aggColors[aggIndex] = state.rowColors[currDoc];
                } else if (state.aggsColored[aggIndex] && state.aggColors[aggIndex] != state.rowColors[currDoc]) {
                    state.aggsColored[aggIndex] = false;
                    state.aggColors[aggIndex] = defaultColor;
                }
            }
        }
        // Turn into data-points (normalizing along the way)
        for (var topicID in currTopicProps) {
            currProp = currTopicProps[topicID]/currAggPropTotal; //TODO: normalize or no?
            //currProp = currTopicProps[topicID];
            if (state.currColOrder.indexOf(parseInt(topicID)) != -1) {
                state.aggData.push({'col':parseInt(topicID),
                    'row':aggIndex,
                    'prop':currProp});
            }
            state.aggTheta[aggIndex][topicID] = currProp;
        }
    }
    for (var i = 0; i < state.aggColors.length; i++) {
        if (state.aggColors[i] == undefined) {
            state.aggColors[i] = defaultColor;
        }
    }

    state.currAggOrder = new Array(state.aggList.length);
    for (var i = 0; i < state.aggList.length; i++) {
        state.currAggOrder[i] = i;
    }

    // Now have data, display it.
    // First, lose or move old stuff
    setWidthsHeightsScales();
    drawGrid();

    d3.selectAll('.rowLabel').remove();
    d3.selectAll('.rowHighlightBar')
        .transition()
        .duration(transdur)
        .attr('y', function(d) { return state.y(state.docToAgg[d]) - mvNS.highlightBarHeight/2; })
        .remove();
    d3.selectAll('.innerShape')
        .transition()
        .duration(transdur)
        .attr('cx', getCircleX)
        .attr('cy', function(d) { return state.y(state.docToAgg[d.row]); })
        .transition()
        .duration(transdur)
        .attr('r', 0)
        .remove();
    repositionLabels();

    // Next, add the new stuff
    var aggLabels = matrixView.selectAll('.aggLabel')
        .data(state.currAggOrder);
    aggLabels.enter().append('svg:text')
        .attr('class', 'rowLabel aggLabel')
        .attr('x', mvNS.rowLabelWidth)
        .attr('y', function(d) { return state.y(state.currAggOrder.indexOf(d)); })
        .attr("text-anchor", "end")
        .attr('cursor', 'pointer')
        .on('mouseover', function(d) {
            brushRow(d);
            /*if (d3.select('#metadataTooltipCheckbox').filter(':checked')[0].length == 1) {
                d3.select('#metadataTooltip')
                    .html(getMetadataString(d))
                    .style('visibility', 'visible')
                    .style('top', event.pageY+'px')
                    .style('left', (event.pageX + 5) + 'px');
            }*/
        })
        .on('mouseout', function(d) {
            unbrushRow(d);
            /*d3.select('#metadataTooltip')
                .style('visibility', 'hidden')
                .html('');*/
        })
        .on('contextmenu', function(d) {
            selectRow(d);
            event.preventDefault();
            d3.select('#rowContextMenu')
                .style('top', event.pageY+'px')
                .style('left', event.pageX+'px');
            $('#rowContextMenu').show();
        })
        .on('click', function(d) { //TODO: selecting row displays metadata of some sort
            selectRow(d);
        })
        .on('dblclick', function(d) { sortColsBy(state.aggregates[d]); })
        .call(d3.behavior.drag()
            .on('dragstart', function(d) {
                // If I want to do any sort of highlighting of the dragged thing, probably do it here.
            })
            .on('drag', function(d) {
                var newY = Math.max(state.y(-1), Math.min(state.y(state.aggList.length), d3.event.y));
                d3.select(this)
                    .attr('y', newY);
            })
            .on('dragend', function(d) {
                // Undo any highlighting here.

                // Find closest position to where the row is dropped and stick it there in the order.
                var newY = d3.select(this).attr('y');
                var newI = getRowIndexByY(newY);
                var oldI = state.currAggOrder.indexOf(d);
                if (newI < oldI) {
                    state.currAggOrder.splice(newI, 0, state.currAggOrder.splice(oldI, 1)[0]);
                    $('#sortSelect').val('None');
                } else if (newI > oldI) {
                    state.currAggOrder.splice(newI, 0, state.currAggOrder[oldI]);
                    state.currAggOrder.splice(oldI, 1);
                    $('#sortSelect').val('None');
                }
                repositionData();
                repositionLabels();
            })
        )
        .transition()
        .delay(transdur)
        .text(function(d) { return state.aggList[d]; });

    var rowHighlightBar = matrixView.selectAll('.aggHighlightBar')
        .data(state.currAggOrder, String);
    rowHighlightBar.enter().append('svg:rect')
        .attr('class', 'rowHighlightBar catColor aggHighlightBar')
        .attr('x', state.x(-1))
        .attr('width', state.x.range()[1] - state.x.range()[0])
        .attr('y', function(d) { return state.y(d) - mvNS.highlightBarHeight/2; })
        .attr('height', mvNS.highlightBarHeight)
        .style('fill', function(d) { return state.aggColors[d]; })
        .style('fill-opacity', function(d) { return state.aggsColored[d] ? mvNS.minFill : 0; })
        .on('mouseover', function(d) {
            brushRow(d);
        })
        .on('mouseout', function(d) {
            unbrushRow(d);
        })
        .on('click', function(d) {
            //toggleRowSelect(d);
            selectRow(d);
        });
    rowHighlightBar.transition()
        .duration(transdur)
        .attr('y', function(d) { return state.y(state.currAggOrder.indexOf(d)) - mvNS.highlightBarHeight/2; })
        .attr('width', state.x(state.currColOrder.length) - state.x.range()[0]);
    //rowHighlightBar.exit().remove();

    var aggShapes = matrixView.selectAll('.aggShape')
        .data(state.aggData);
    aggShapes.enter().append('svg:circle')
        .attr('class','innerShape aggShape')
        .attr('r', 0)
        //.attr('r', getR)
        .attr('cx', getCircleX)
        .attr('cy', getCircleY)
        .style('stroke', 'black')
        .style('fill-opacity', .6)
        .style('fill', function(d) { return state.aggColors[d.row]; })
        //.style('fill', defaultColor)// TODO: during aggregation, combine colors
        .on('mouseover', function(d) {
            brushRow(d.row);
            brushCol(d.col);
            showTooltip(d.prop);
        })
        .on('mouseout', function(d) {
            unbrushRow(d.row);
            unbrushCol(d.col);
            //hideTooltip();
        })
        .on('click', function(d) {
            selectRow(d.row);
            //selectCol(d.col);
        })
        .transition()
        .duration(transdur)
        .delay(transdur)
        .attr('r', getR);

    // Do this after everything else cause it's less important
    // Replace all the lists in aggIQRs with IQR objects // TODO: move this after the transition?
    var currPropList, q1, q2, q3, l;
    var quartileData = [];
    for (var i = 0; i < state.aggIQRs.length; i++) {
        for (var topicID in state.aggIQRs[i]) {
            currPropList = state.aggIQRs[i][topicID];
            l = currPropList.length;
            currPropList.sort(function(a,b){return a-b;});
            if (l % 2 == 0) {
                q2 = (currPropList[l/2] + currPropList[l/2 + 1])/2;
                if (l % 4 == 0) {
                    q1 = (currPropList[l/4] + currPropList[l/4 + 1])/2;
                    q3 = (currPropList[3*l/4] + currPropList[3*l/4 + 1])/2;
                } else {
                    q1 = currPropList[Math.floor(l/4)];
                    q3 = currPropList[Math.floor(3*l/4)];
                }
            } else {
                q2 = currPropList[Math.floor(l/2)];
                if ((l - 1) % 4 == 0) {
                    q1 = (currPropList[(l-1)/4] + currPropList[(l-1)/4 + 1])/2;
                    q3 = (currPropList[Math.floor(3*l/4)] + currPropList[Math.floor(3*l/4 + 1)])/2;
                } else {
                    q1 = currPropList[Math.floor((l-1)/4)];
                    q3 = currPropList[Math.floor(3*l/4)];
                }
            }
            state.aggIQRs[i][topicID] = {'q1': q1, 'q2': q2, 'q3': q3};
            quartileData.push({'col':parseInt(topicID), 'row':i, 'prop': q1, 'type': 'q'});
            quartileData.push({'col':parseInt(topicID), 'row':i, 'prop': q2, 'type': 'q'});
            quartileData.push({'col':parseInt(topicID), 'row':i, 'prop': q3, 'type': 'q'});
        }
    }
    var qShapes = matrixView.selectAll('.qShape')
        .data(quartileData);
    qShapes.enter().append('svg:circle')
        .attr('class','innerShape qShape')
        .attr('r', 0)
        //.attr('r', getR)
        .attr('cx', getCircleX)
        .attr('cy', getCircleY)
        .style('stroke', 'gray')
        .style('fill-opacity', 0)
        // For now, no fill or mousing
        .transition()
        .duration(transdur)
        .delay(transdur)
        .attr('r', getR);
}

var unaggregate = function() {
    state.aggregatingBy = undefined;
    $('#clearAggDiv').hide();
    $('#openGroup').parent().addClass('disabled');
    $('#openGroupInMeso').parent().addClass('disabled');
    $('#openInTextViewer').parent().removeClass('disabled');
    $('#aggregateSelect').val('None');
    d3.selectAll('.aggLabel').remove();
    d3.selectAll('.qShape').remove();
    d3.selectAll('.aggShape')
        .transition()
        .duration(transdur)
        .attr('r', 0)
        .remove();
    d3.selectAll('.aggHighlightBar')
        //.transition()
        //.delay(transdur)
        .remove();

    var oldYScale = state.y;

    var innerShape = matrixView.selectAll('.fullData')
        .data(state.currData);
    innerShape.enter().append('svg:circle')
        .attr('class','innerShape fullData')
        .attr('r', 0)
        .attr('cx', getCircleX)
        .attr('cy', function(d) {
            return oldYScale(state.currAggOrder.indexOf(state.docToAgg[d.row]));
        })
        //.attr('cy', getCircleY)
        .style('stroke', 'black')
        .style('fill-opacity', .6)
        .style('fill', function(d) { return state.rowColors[d.row]; })
        .on('mouseover', function(d) {
             brushRow(d.row);
             brushCol(d.col);
             showTooltip(d.prop);
         })
         .on('mouseout', function(d) {
             unbrushRow(d.row);
             unbrushCol(d.col);
             hideTooltip();
         })
         .on('click', function(d) {
             selectRow(d.row);
             selectCol(d.col);
         })
        .transition()
        .duration(transdur)
        .attr('r', getR);

    setWidthsHeightsScales();
    setTimeout(function() { drawGrid(); }, transdur);

    innerShape.transition()
        .duration(transdur)
        .delay(transdur)
        .attr('cy', getCircleY);

    setTimeout(function() {
        updateMatrixView();
        matrixView.selectAll('.innerShape').attr('r',getR);
    }, 2*transdur);
};

var createFilter = function(sel, form) {
    // Init filters list if needed
    if (state.filters == undefined) {
        state.filters = {};
        state.filterCount = 0; // This keeps an index for EVERY filter created in a session.
    }
    // Generate filter names
    var shortName = '';
    var longName = '';
    for (var fieldName in form) {
        if (form[fieldName] != '') {
            shortName += fieldName + ';';
            longName += fieldName + ': ' + form[fieldName] + '<br />';
        }
    }
    // Add filter
    state.filters[state.filterCount] = sel;
    // Create a visual representation of the filter
    var filter = d3.select('#filterWell')
        .append('div')
        .attr('id', 'filter' + state.filterCount)
        .attr('filterIndex', state.filterCount)
        .attr('class', 'alert fade in');
    filter.append('button')
        .attr('type', 'button')
        .attr('class', 'close')
        .attr('data-dismiss', 'alert')
        .text('×');
    filter.append('strong')
        .text(shortName);
    $('#filter' + state.filterCount)
        .tooltip({html:true, placement:'top', title:longName});
    // Bind removeFilter to the close button
    $('#filter' + state.filterCount).bind('close', function() {
        removeFilter($(this).attr('filterIndex'));
        $('.tooltip').hide();

    });
    // Hide rows being filtered out
    hideRowsNotIn(sel);
    state.filterCount++;
};

var removeFilter = function(filterIndex) {
    if (state.filters[filterIndex] != undefined) {
        // Remove filter from the state.filters list
        var sel = state.filters[filterIndex];
        delete state.filters[filterIndex];
        // Find the rows that will be shown as per the current filters
        var rowsToShow = new Array(state.rowList.length);
        for (var i = 0; i < state.rowList.length; i++) {
            rowsToShow[i] = i;
        }
        var i = 0;
        while (i < rowsToShow.length) {
            for (var filterNum in state.filters) {
                if (state.filters[filterNum].indexOf(rowsToShow[i]) == -1) {
                    rowsToShow.splice(i, 1);
                    i--;
                    break;
                }
            }
            i++;
        }
        // Show only those rows
        state.currData = state.data.slice(0);

        // Fix row order
        state.currRowOrder = rowsToShow;
        state.selectedRows = [];
        updateRowSelectDiv();

        hideRowsNotIn(rowsToShow);
    }
};

var buildMetadataForm = function(formID) {
    var adSelBody = d3.select('#' + formID);
    var currName, currType, accGrp, accInner;
    var catLists = new Object(); // This object will store a list of all the options of each category
    // Fill the accordion groups for each metadata field
    for (var i = 0; i < state.metadataNames.length; i++) {
        currName = state.metadataNames[i];
        currType = state.metadataTypes[i];
        accGrp = adSelBody.append('div').attr('class', 'accordion-group');
        accGrp.append('div')
            .attr('class', 'accordion-heading')
            .append('a')
            .attr('class', 'accordion-toggle')
            .attr('data-toggle', 'collapse')
            .attr('href', '#' + currName + '_collapse_' + formID)
            .text(currName);
        accGrp.append('div')
            .attr('id', currName + '_collapse_' + formID)
            .attr('class', 'accordion-body collapse')
            .append('div')
            .attr('class', 'accordion-inner');
        accInner = accGrp.select('.accordion-inner');
        if (currType == 'str') {
            accInner.html(currName + ' contains ')
                .append('input')
                .attr('type', 'text')
                .attr('class', 'str')
                .attr('name', currName);
        } else if (currType == 'int') {
            accInner.html(currName + ' is between <input type="text" class="int input-small" name="min'
                + currName + '" /> and <input type="text" class="int input-small" name="max'
                + currName + '" />');
        } else if (currType == 'cat') {
            accInner.html(currName + ' is ')
                .append('select')
                .attr('id', currName + '_select_' + formID)
                .attr('name', currName)
                .append('option')
                .attr('value', '');
            // Create an empty catList for this category...
            catLists[currName] = [];
        }
    }
    // Loop through metadata, filling catLists...
    var currDoc;
    for (var i = 0; i < state.metadata.length; i++) {
        currDoc = state.metadata[i];
        for (var catName in catLists) {
            if (catLists[catName].indexOf(currDoc[catName]) == -1) {
                catLists[catName].push(currDoc[catName]);
            }
        }
    }
    // Finally, use catLists to fill the cat select tags.
    var selectTag, catOption;
    for (var catName in catLists) {
        selectTag = d3.select('#' + catName + '_select_' + formID);
        for (var i = 0; i < catLists[catName].length; i++) {
            catOption = catLists[catName][i];
            selectTag.append('option')
                .attr('value', catOption)
                .attr('name', catOption)
                .text(catOption);
        }
    }
};

// TODO: this may do some weird things for selections when stuff is hidden vs. not
var getSelectionFromForm = function(form) {
    //var sel = state.currRowOrder.slice(0);
    // Rather than just getting documents that are visible, get all (easier for overlapping filters).
    var sel = new Array(state.rowList.length);
    for (var i = 0; i < state.rowList.length; i++) {
        sel[i] = i;
    }
    var currName, currType, minVal, maxVal;
    for (var i = 0; i < state.metadataNames.length; i++) {
        currName = state.metadataNames[i];
        currType = state.metadataTypes[i];

        if (currType == 'str' || currType == 'cat') {
            if (form[currName] == '') {
                continue;
            }
            sel = selectByStringField(currName, form[currName], sel);
        } else if (currType == 'int') {
            minVal = form['min' + currName] == '' ? -Infinity : parseInt(form['min' + currName]);
            maxVal = form['max' + currName] == '' ? Infinity : parseInt(form['max' + currName]);
            if (minVal == '' && maxVal == '') {
                continue;
            }
            sel = selectByIntField(currName, minVal, maxVal, sel);
        }
    }
    return sel;
};

var selectByStringField = function(fieldName, fieldValue, currSelection) {
    // If no currSelection provided, default to entire corpus
    if (currSelection == undefined) {
        currSelection = state.currRowOrder.slice(0);
    }

    // Now filter by fieldValue
    var newSelection = [];
    for (var i = 0; i < currSelection.length; i++) {
        // If metadata doesn't exist for this entry, then filter it out.
        if (currSelection[i] > state.metadata.length - 1 || Object.keys(state.metadata[currSelection[i]]).length == 0) {
            currSelection.splice(i,1);
            i--;
        } else {
            if (state.metadata[currSelection[i]][fieldName] == undefined ||
                state.metadata[currSelection[i]][fieldName].toLowerCase().indexOf(fieldValue.toLowerCase()) == -1) {
                currSelection.splice(i,1);
                i--; // ...since we removed one, move index back 1
            }
        }
    }

    return currSelection;
};

var selectByIntField = function(fieldName, minVal, maxVal, currSelection) {
    // If no currSelection provided, default to entire corpus
    if (currSelection == undefined) {
        currSelection = state.currRowOrder.slice(0);
    }
    // Not sure I'll need these year defaults, but doesn't hurt
    if (maxVal == undefined) {
        maxVal = Infinity;
    }
    if (minVal == undefined) {
        minVal = -Infinity;
    }

    // Now filter out docs not in range
    var currVal;
    for (var i = 0; i < currSelection.length; i++) {
        // If metadata doesn't exist for this entry, then filter it out.
        if (currSelection[i] > state.metadata.length - 1 || Object.keys(state.metadata[currSelection[i]]).length == 0) {
            currSelection.splice(i,1);
            i--;
        } else {
            currVal = state.metadata[currSelection[i]][fieldName];
            if (currVal < minVal || currVal > maxVal) {
                currSelection.splice(i,1);
                i--;
            }
        }
    }

    return currSelection;
};

var getObjectFromForm = function(formID) {
    var tempObject = new Object();
    var $this;
    d3.selectAll('#' + formID + ' input').each(function() {
        $this = d3.select(this);
        if ($this.property('type') != 'submit') {
            tempObject[$this.property('name')] = $this.property('value');
        }
    });
    d3.selectAll('#' + formID + ' select').each(function() {
        $this = d3.select(this);
        tempObject[$this.property('name')] = $this.property('value');
    });
    return tempObject;
};

var sortRowsByMetadata = function(fieldName) {
    var fieldNum = state.metadataNames.indexOf(fieldName);
    if (fieldNum == -1) {
        return;
    }

    var fieldType = state.metadataTypes[fieldNum];
    if (fieldType == 'str' || fieldType == 'cat' || fieldType == 'int') {
        state.currRowOrder.sort(function(d1, d2) {
            if (fieldName in state.metadata[d1] && state.metadata[d1] != '') {
                if (fieldName in state.metadata[d2] && state.metadata[d2] != '') {
                    var d1Val = state.metadata[d1][fieldName];
                    var d2Val = state.metadata[d2][fieldName];
                    if (fieldType == 'str' || fieldType == 'cat') {
                        if (d1Val > d2Val) {
                            return 1 * state.sortOrderVar;
                        } else if (d2Val > d1Val) {
                            return -1 * state.sortOrderVar;
                        }
                        return 0;
                    } else if (fieldType == 'int') {
                        return parseInt(d1Val) - parseInt(d2Val);
                    }
                } else {
                    return -1;
                }
            } else {
                if (fieldName in state.metadata[d2] && state.metadata[d2] != '') {
                    return 1;
                } else {
                    return 0;
                }
            }
        });
        repositionData();
        repositionLabels(true);
    }
};

var sortColsByMetadata = function(fieldName) {
    var fieldNum = state.topicMetadataNames.indexOf(fieldName);
    if (fieldNum == -1) {
        return;
    }
    // Sorting in descending order, seems more useful that way
    state.currColOrder.sort(function(t1, t2) {
        if (state.topicMetadata[t1] != undefined && fieldName in state.topicMetadata[t1] && state.topicMetadata[t1] != '') {
            if (state.topicMetadata[t2] != undefined && fieldName in state.topicMetadata[t2] && state.topicMetadata[t2] != '') {
                var t1Val = state.topicMetadata[t1][fieldName];
                var t2Val = state.topicMetadata[t2][fieldName];
                //return parseFloat(t1Val) - parseFloat(t2Val);
                return parseFloat(t2Val) - parseFloat(t1Val);
            } else {
                //return -1;
                return 1;
            }
        } else {
            if (state.topicMetadata[t2] != undefined && fieldName in state.topicMetadata[t2] && state.topicMetadata[t2] != '') {
                //return 1;
                return -1;
            } else {
                return 0;
            }
        }
    });
    repositionData();
    repositionLabels(true); // TODO: need to indicate this is different from row resort so select goes back to None
};

var showTooltip = function(val) {
    d3.select('#dataTooltip')
        .text(val)
        .style('visibility', 'visible')
        .style('top', event.pageY+10+'px')
        .style('left', event.pageX+10+'px');
};

var hideTooltip = function() {
    d3.select('#dataTooltip').style('visibility','hidden');
};

var moveRowsToTop = function(selection) {
    if (selection != undefined && selection.length != 0) {
        var indices = new Array(selection.length);
        for (var i = 0; i < selection.length; i++) {
            indices[i] = state.currRowOrder.indexOf(selection[i]);
        }
        indices.sort(function(a,b) {return a-b;});
        for (var i = 0; i < indices.length; i++) {
            state.currRowOrder.splice(i, 0, state.currRowOrder.splice(indices[i], 1)[0]);
        }
        repositionData();
        repositionLabels();
    }
};

var moveColsToLeft = function(selection) {
    if (selection != undefined && selection.length != 0) {
        var indices = new Array(selection.length);
        for (var i = 0; i < selection.length; i++) {
            indices[i] = state.currColOrder.indexOf(selection[i]);
        }
        indices.sort(function(a,b) {return a-b;});
        for (var i = 0; i < indices.length; i++) {
            state.currColOrder.splice(i, 0, state.currColOrder.splice(indices[i], 1)[0]);
        }
        repositionData();
        repositionLabels();
        $('#topicSortSelect').val('');
    }
};

// This function sorts the rows by a selection (list) of cols
var sortRowsBy = function(selection) {
    if (selection == undefined || selection.length == 0) {
        return;
    }

    $('#sortSelect').val('None');
    //var sortOrderVar = d3.select('#ascendingOrderCheckbox').filter(':checked')[0].length == 1 ? 1 : -1;
    var sortOrderVar = 1;
    var listToSort = state.aggregatingBy == undefined ? state.currRowOrder : state.currAggOrder;
    var thetaToUse = state.aggregatingBy == undefined ? state.theta: state.aggTheta;
    listToSort.sort(function(d1,d2) {
        var d1Score = 0;
        var d2Score = 0;
        var t;
        for (var i = 0; i < selection.length; i++) {
            t = selection[i];
            if (thetaToUse[d1][t] != undefined) {
                d1Score += thetaToUse[d1][t];
            }
            if (thetaToUse[d2][t] != undefined) {
                d2Score += thetaToUse[d2][t];
            }
        }
        return sortOrderVar*(d2Score - d1Score);
    });
    repositionData();
    repositionLabels();
};

var addColSortFxn = function(fxnName, fxn) {
    d3.select('#topicSortSelect').append('option')
        .property('value', fxnName)
        .property('name', fxnName)
        .text(fxnName);
    state.colSortFxns[fxnName] = fxn;
}

var sortColsByFxn = function(fxn) {
    state.currColOrder.sort(fxn);
    repositionData();
    repositionLabels();
}

var sortColsBy = function(selection) {
    if (selection == undefined || selection.length == 0) {
        return;
    }

    state.currColOrder.sort(function(t1,t2) {
        var t1Score = 0;
        var t2Score = 0;
        var d;
        for (var i = 0; i < selection.length; i++) {
            d = selection[i];
            if (state.theta[d][t1] != undefined) {
                t1Score += state.theta[d][t1];
            }
            if (state.theta[d][t2] != undefined) {
                t2Score += state.theta[d][t2];
            }
        }
        return t2Score - t1Score;
    });
    repositionData();
    repositionLabels();
    $('#topicSortSelect').val('');
};

var sortRowsByDistanceFrom = function(rowNum) {
    if (rowNum < 0 || rowNum > state.rowList.length) {
        return;
    }
    $('#sortSelect').val('None');

    //var sortOrderVar = d3.select('#ascendingOrderCheckbox').filter(':checked')[0].length == 1 ? 1 : -1;
    var sortOrderVar = 1;

    var similarity = function(d1, d2) {
        var v1 = toArray(d1);
        var v2 = toArray(d2);
        return dot(v1,v2) / (len(v1) * len(v2));
    };
    var dot = function(v1, v2) {
        if (v1.length != v2.length) {
            throw "Dot product lengths do not match";
        }
        var sum = 0;
        for (var i = 0; i < v1.length; i++) {
            sum += v1[i] * v2[i];
        }
        return sum;
    };
    var len = function(v1) {
        var sumSquares = 0;
        for (var i = 0; i < v1.length; i++) {
            sumSquares += v1[i] * v1[i];
        }
        return Math.sqrt(sumSquares);
    };
    var toArray = function(rowNum) {
        var rowObj = state.theta[rowNum];
        var returnArray = new Array(state.colList.length);
        for (var i = 0; i < state.colList.length; i++) {
            if (i in rowObj) {
                returnArray[i] = rowObj[i];
            } else {
                returnArray[i] = 0;
            }
        }
        return returnArray;
    };

    state.currRowOrder.sort(function(a,b) {
        return sortOrderVar * (similarity(rowNum, b) - similarity(rowNum, a));
    });
    repositionData();
    repositionLabels();
};

// TODO: doesn't work yet because THETA is designed just to work for docs, not for topics (see first line of toArray function)
var sortColsByDistanceFrom = function(colNum) {
    if (colNum < 0 || colNum > state.colList.length) {
        return;
    }

    //var sortOrderVar = d3.select('#ascendingOrderCheckbox').filter(':checked')[0].length == 1 ? 1 : -1;
    var sortOrderVar = 1;

    var similarity = function(c1, c2) {
        var v1 = toArray(c1);
        var v2 = toArray(c2);
        return dot(v1,v2) / (len(v1) * len(v2));
    };
    var dot = function(v1, v2) {
        if (v1.length != v2.length) {
            throw "Dot product lengths do not match";
        }
        var sum = 0;
        for (var i = 0; i < v1.length; i++) {
            sum += v1[i] * v2[i];
        }
        return sum;
    };
    var len = function(v1) {
        var sumSquares = 0;
        for (var i = 0; i < v1.length; i++) {
            sumSquares += v1[i] * v1[i];
        }
        return Math.sqrt(sumSquares);
    };
    var toArray = function(colNum) {
        var colObj = state.theta[colNum]; //TODO : this is the part that breaks
        var returnArray = new Array(state.colList.length);
        for (var i = 0; i < state.colList.length; i++) {
            if (i in colObj) {
                returnArray[i] = colObj[i];
            } else {
                returnArray[i] = 0;
            }
        }
        return returnArray;
    };

    state.currColOrder.sort(function(a,b) {
        return sortOrderVar * (similarity(colNum, b) - similarity(colNum, a));
    });
    repositionData();
    repositionLabels();
    $('#topicSortSelect').val('');
};

var toggleColorBy = function(rowsOrCols) {
    if (rowsOrCols == 'rows') {
        d3.select('#toggleColorByRowBtn').classed('active', true);
        d3.select('#toggleColorByColBtn').classed('active', false);
        if (state.colorByRows != true) {
            state.colorByRows = true;
            matrixView.selectAll('.innerShape')
                .style('fill', defaultColor);
            matrixView.selectAll('.outerShape')
                .style('fill', defaultColor);
            matrixView.selectAll('.colHighlightBar')
                .style('fill', defaultColor)
                .style('fill-opacity', 0);

            var currRow;
            for (var i = 0; i < state.rowsColored.length; i++) {
                currRow = state.rowsColored[i];
                colorRows([currRow], state.rowColors[currRow]);
            }
        }
    } else if (rowsOrCols == 'cols') {
        d3.select('#toggleColorByColBtn').classed('active', true);
        d3.select('#toggleColorByRowBtn').classed('active', false);
        if (state.colorByRows != false) {
            state.colorByRows = false;
            matrixView.selectAll('.innerShape')
                .style('fill', defaultColor);
            matrixView.selectAll('.outerShape')
                .style('fill', defaultColor);
            matrixView.selectAll('.rowHighlightBar')
                .style('fill', defaultColor)
                .style('fill-opacity', 0);

            var currCol;
            for (var i = 0; i < state.colsColored.length; i++) {
                currCol = state.colsColored[i];
                colorCols([currCol], state.colColors[currCol]);
            }
        }
    }
}

var colorRows = function(selection, color) {
    if (state.colorByRows == false) {
        toggleColorBy('rows');
    }

    matrixView.selectAll('.innerShape').select(function(d) { return selection.indexOf(d.row) != -1 ? this : null; })
        .style('fill', color);
    matrixView.selectAll('.rowHighlightBar').select(function(d) { return selection.indexOf(d) != -1 ? this : null; })
        .style('fill', color)
        .style('fill-opacity', mvNS.minFill);
    if (state.aggregatingBy == undefined) {
        for (var i = 0; i < selection.length; i++) {
            state.rowColors[selection[i]] = color;
            if (state.rowsColored.indexOf(selection[i]) == -1) {
                state.rowsColored.push(selection[i]);
            }
        }
    } else {
        for (var i = 0; i < selection.length; i++) {
            state.aggColors[selection[i]] = color;
            state.aggsColored[selection[i]] = true;
            for (var j = 0; j < state.aggregates[selection[i]].length; j++) {
                state.rowColors[state.aggregates[selection[i]][j]] = color;
                state.rowsColored[state.aggregates[selection[i]][j]] = true;
                if (state.rowsColored.indexOf(selection[i]) != -1) {
                    state.rowsColored.splice(state.rowsColored.indexOf(selection[i]), 1);
                }
            }
        }
    }
};

var colorCols = function(selection, color) {
    if (state.colorByRows == true) {
        toggleColorBy('cols');
    }

    matrixView.selectAll('.innerShape').select(function(d) { return selection.indexOf(d.col) != -1 ? this : null; })
        .style('fill', color);
    matrixView.selectAll('.colHighlightBar').select(function(d) { return selection.indexOf(d) != -1 ? this : null; })
        .style('fill', color)
        .style('fill-opacity', mvNS.minFill);
    for (var i = 0; i < selection.length; i++) {
        state.colColors[selection[i]] = color;
        if (state.colsColored.indexOf(selection[i]) == -1) {
            state.colsColored.push(selection[i]);
        }
    }
};

var uncolorCols = function(selection) {
    if (state.colorByRows == false) {
        matrixView.selectAll('.innerShape').select(function(d) { return selection.indexOf(d.col) != -1 ? this : null; })
            .style('fill', defaultColor);
        matrixView.selectAll('.colHighlightBar').select(function(d) { return selection.indexOf(d) != -1 ? this : null; })
            .style('fill', defaultColor)
            .style('fill-opacity', 0);
    }
    for (var i = 0; i < selection.length; i++) {
        state.colColors[selection[i]] = defaultColor;
        if (state.colsColored.indexOf(selection[i]) != -1) {
            state.colsColored.splice(state.colsColored.indexOf(selection[i]),1);
        }
    }
}

var applyColorEncoding = function(encodingName) {
    if (encodingName == 'cat' || encodingName == 'div' || encodingName == 'seq') {
        state.colorEncoding = encodingName;

        d3.selectAll('.catColor').style('visibility', 'hidden');
        d3.selectAll('.divColor').style('visibility', 'hidden');
        d3.selectAll('.seqColor').style('visibility', 'hidden');
        d3.selectAll('.' + encodingName + 'Color').style('visibility', 'visible');

        d3.selectAll('.innerShape')
            .style('fill', getColorFxn());
    }
};

var getColorFxn = function() {
    if (state.colorEncoding == 'div') {
        return getDivColor;
    } else if (state.colorEncoding == 'seq') {
        return getSeqColor;
    } else {
        return getCatColor;
    }
};

var getCatColor = function(d) {
    if (state.colorByRows == true) {
        return state.rowColors[d.row];
    } else if (state.colorByRows == false) {
        return state.colColors[d.col];
    } else {
        return defaultColor;
    }
};

var getDivColor = function(d) {
    return colors.div[Math.round(state.divScale(d.prop))];
};

var getSeqColor = function(d) {
    return colors.seq[Math.round(state.seqScale(d.prop))];
};

// TODO: finish texture
var applySignEncoding = function(encodingName) {
    if (encodingName == 'shape') {
        state.signEncoding = 'shape';
        var tempData = d3.selectAll('.innerShape').data();

        matrixView.selectAll('circle.innerShape').data([])
            .exit()
            .transition().duration(transdur)
            .attr('r', 0)
            .remove();

        matrixView.selectAll('rect.innerShape').data(tempData)
            .enter().append('svg:rect')
            .attr('class', 'innerShape')
            .attr('x', getCircleX)// Start w/circle pos, transition to rect pos
            .attr('y', getCircleY)// Start w/circle pos, transition to rect pos
            .attr('width', 0)
            .attr('height', 0)
            .style('stroke', 'black')
            .style('fill', getColorFxn())
            .style('fill-opacity',.6)
            .on('mouseover', function(d) {
                brushRow(d.row);
                brushCol(d.col);
                showTooltip(d.prop);
            })
            .on('mouseout', function(d) {
                unbrushRow(d.row);
                unbrushCol(d.col);
                hideTooltip();
            })
            .on('click', function(d) {
                selectRow(d.row);
                selectCol(d.col);
            })
            .transition().duration(transdur)
            .attr('x', getRectX)
            .attr('y', getRectY)
            .attr('width', getRectW)
            .attr('height', getRectW)
            .transition().duration(transdur).delay(transdur)
            .attr('transform', getRectRot);
    } else if (encodingName == 'texture') {
        state.signEncoding = 'texture';
    } else {
        if (state.signEncoding != 'none') {
            state.signEncoding = 'none';
            var tempData = d3.selectAll('.innerShape').data();

            matrixView.selectAll('rect.innerShape').data([])
                .exit()
                .transition().duration(transdur)
                .attr('x', getCircleX)
                .attr('y', getCircleY)
                .attr('width', 0)
                .attr('height', 0)
                .remove();

            matrixView.selectAll('circle.innerShape').data(tempData)
                .enter().append('svg:circle')
                .attr('class', 'innerShape')
                .attr('cx', getCircleX)
                .attr('cy', getCircleY)
                .attr('r', 0)
                .style('stroke', 'black')
                .style('fill', getColorFxn())
                .style('fill-opacity',.6)
                .on('mouseover', function(d) {
                    brushRow(d.row);
                    brushCol(d.col);
                    showTooltip(d.prop);
                })
                .on('mouseout', function(d) {
                    unbrushRow(d.row);
                    unbrushCol(d.col);
                    hideTooltip();
                })
                .on('click', function(d) {
                    selectRow(d.row);
                    selectCol(d.col);
                })
                .transition().duration(transdur)
                .attr('r', getR);
        }
    }
};

/**************** HIDING FUNCTIONS *************************/

var hideCols = function(selection) {
    var dataToUse = state.aggregatingBy == undefined ? state.currData : state.aggData;

    // Remove selected columns from currColOrder
    var i;
    for (var c = 0; c < selection.length; c++) {
        i = state.currColOrder.indexOf(selection[c]);
        if (i != -1) {
            state.currColOrder.splice(i, 1);
        }
    }
    // Remove selected columns' data from currData
    var i = 0;
    while (i < dataToUse.length) {
        if (selection.indexOf(dataToUse[i].col) != -1) {
            dataToUse.splice(i, 1);
            i--;
        }
        i++;
    }
    // Draw 'em
    updateMatrixView();
};

var hideColsNotIn = function(selection) {
    // Loop through currColOrder to see which aren't selected.
    var colsToHide = state.currColOrder.slice(0);
    var i = 0;
    while (i < colsToHide.length) {
        if (selection.indexOf(colsToHide[i]) != -1) {
            colsToHide.splice(i, 1);
            i--;
        }
        i++;
    }
    hideCols(colsToHide);
};

var hideEmptyCols = function() {
    // Loop through currData to see which cols are empty. TODO: Should this be data or currData?
    var dataToUse = state.aggregatingBy == undefined ? state.currData : state.aggData;
    var colsToHide = state.currColOrder.slice(0);
    var currDatumIndex;
    for (var i = 0; i < dataToUse.length; i++) {
        if (colsToHide.length == 0) {
            break;
        }
        currDatumIndex = colsToHide.indexOf(dataToUse[i].col);
        if (currDatumIndex != -1) {
            colsToHide.splice(currDatumIndex, 1);
        }
    }

    if (colsToHide.length != 0) {
        hideCols(colsToHide);
    }
};

var hideRows = function(selection) {
    var rowOrder = state.aggregatingBy == undefined ? state.currRowOrder : state.currAggOrder;
    var dataToUse = state.aggregatingBy == undefined ? state.currData : state.aggData;

    // Remove selected rows from currRowOrder
    var i;
    for (var r = 0; r < selection.length; r++) {
        i = rowOrder.indexOf(selection[r]);
        if (i != -1) {
            rowOrder.splice(i, 1);
        }
    }
    // Remove selected rows' data from currData
    var i = 0;
    while (i < dataToUse.length) {
        // TODO: this is a hacky fix. Should consolidate this and hideCols somehow.
        if (selection.indexOf(dataToUse[i].row) != -1 || state.currColOrder.indexOf(dataToUse[i].col) == -1) {
            dataToUse.splice(i, 1);
            i--;
        }
        i++;
    }
    // Draw 'em
    updateMatrixView();
};

var hideRowsNotIn = function(selection) {
    // Loop through currRowOrder to see which aren't selected.
    var rowsToHide = state.aggregatingBy == undefined ? state.currRowOrder.slice(0) : state.currAggOrder.slice(0);
    var i = 0;
    while (i < rowsToHide.length) {
        if (selection.indexOf(rowsToHide[i]) != -1) {
            rowsToHide.splice(i, 1);
            i--;
        }
        i++;
    }
    hideRows(rowsToHide);
};

var hideEmptyRows = function() {
    // Loop through currData to see which rows are empty. TODO: Should this be data or currData?
    var dataToUse = state.aggregatingBy == undefined ? state.currData : state.aggData;
    var rowsToHide = state.aggregatingBy == undefined ? state.currRowOrder.slice(0) : state.currAggOrder.slice(0);
    var currDatumIndex;
    for (var i = 0; i < dataToUse.length; i++) {
        if (rowsToHide.length == 0) {
            break;
        }
        currDatumIndex = rowsToHide.indexOf(dataToUse[i].row);
        if (currDatumIndex != -1) {
            rowsToHide.splice(currDatumIndex, 1);
        }
    }
    if (rowsToHide.length != 0) {
        hideRows(rowsToHide);
    }
};

/**************** DATA RETRIEVAL **************************/

var fetchFakeData = function() {
    state.theta = [
        { 0:.5, 3:.3},
        { 1:.4, 3:.5},
        { 4:.1, 2:.4},
        { 0:.2, 1:.2, 2:.2, 3:.2, 4:.2},
        { 2:.3, 5:.8}
    ];
    state.rowList = ['Document A', 'Document B', 'Document C', 'Document D', 'Document E'];
    state.colList = ['Topic 0', 'Topic 1', 'Topic 2', 'Topic 3', 'Topic 4', 'Topic 5'];

    state.maxVal = 1;
    state.minVal = 0;
    state.maxSize = Math.max(Math.abs(state.maxVal), Math.abs(state.minVal));
    state.divScale = d3.scale.linear().domain([-1*state.maxSize, state.maxSize]).range([0, colors.div.length - 1]);
    state.seqScale = d3.scale.linear().domain([state.minVal, state.maxVal]).range([0, colors.seq.length - 1])
    mvNS.areaScale.domain([0,state.maxSize]);

    /*mvNS.rowLabelWidth = 15 * Math.max.apply(Math, state.rowList.map(function(e) { return e.length; }));
    mvNS.colLabelHeight = 15 * Math.max.apply(Math, state.colList.map(function(e) { return e.length; }));
    mvNS.w = Math.max(mvNS.minW, state.colList.length * matrixSeparation + mvNS.rowLabelWidth);
    matrixView.attr('width', mvNS.w);
    mvNS.h = Math.max(mvNS.minH, state.rowList.length * matrixSeparation + mvNS.colLabelHeight);
    matrixView.attr('height', mvNS.h);*/
    //setWidthsHeightsScales();

    useData();
};

var setWidthsHeightsScales = function() {
    var rowList = state.aggregatingBy == undefined ? state.rowList : state.aggList;
    var rowOrder = state.aggregatingBy == undefined ? state.currRowOrder : state.currAggOrder;

    var separation = state.aggregatingBy == undefined ? matrixSeparation : aggSizeFactor*matrixSeparation;
    mvNS.rowLabelWidth = 8 * Math.max.apply(Math, state.rowList.map(function(e) { return e == undefined ? 0 : e.length; }));
    mvNS.colLabelHeight = 8 * Math.max.apply(Math, state.colList.map(function(e) { return e == undefined ? 0 : e.length; }));
    mvNS.w = Math.max(mvNS.minW, state.currColOrder.length * separation + mvNS.rowLabelWidth);
    matrixView.attr('width', mvNS.w);
    mvNS.h = Math.max(mvNS.minH, rowOrder.length * separation + mvNS.colLabelHeight);
    matrixView.attr('height', mvNS.h);

    state.x = d3.scale.linear()
        .domain([-1, state.currColOrder.length])
        .range([mvNS.rowLabelWidth + mvNS.buffer, mvNS.w - mvNS.buffer]);
    state.y = d3.scale.linear()
        .domain([-1, rowOrder.length])
        .range([mvNS.colLabelHeight + mvNS.buffer, mvNS.h - mvNS.buffer]);
}

var fetchData = function() {
    $DATA_URL = '/_getData/fake.csv/fakeRows.txt/fakeCols.txt';
    d3.json(/*$DATA_URL*/$URL_FOR_getData.substring(0, $URL_FOR_getData.length-2) + $MATRIXCSV + '/' + $ROWFILE + '/' + $COLFILE, function(json) {
        state.theta = json.matrix;
        state.rowList = json.rowList;
        state.colList = json.colList;
        state.maxVal = json.max;
        state.minVal = json.min;
        state.maxSize = Math.max(Math.abs(state.maxVal), Math.abs(state.minVal));
        state.divScale = d3.scale.linear().domain([-1*state.maxSize, state.maxSize]).range([0, colors.div.length - 1]);
        state.seqScale = d3.scale.linear().domain([state.minVal, state.maxVal]).range([0, colors.seq.length - 1])
        mvNS.areaScale.domain([0,state.maxSize]);

        /*mvNS.rowLabelWidth = 15 * Math.max.apply(Math, state.rowList.map(function(e) { return e.length; }));
        mvNS.colLabelHeight = 15 * Math.max.apply(Math, state.colList.map(function(e) { return e.length; }));
        mvNS.w = Math.max(mvNS.minW, state.colList.length * matrixSeparation + mvNS.rowLabelWidth);
        matrixView.attr('width', mvNS.w);
        mvNS.h = Math.max(mvNS.minH, state.rowList.length * matrixSeparation + mvNS.colLabelHeight);
        matrixView.attr('height', mvNS.h);*/
        //setWidthsHeightsScales();

        useData();
    });
};

var fetchMetadata = function() {
    d3.json($METADATA_URL, function(json) {
        state.metadataTypes = json.dataTypes;
        state.metadataNames = json.fieldNames;
        state.metadata = json.metadata;

        initSidebarFunctions();
        initSettings();
    });
};

var fetchTheta = function() {
    d3.json($THETA_URL, function(json) {
        state.theta = json.theta;
        state.topicMetadata = json.topicMetadata;
        state.topicMetadataNames = json.topicMetadataFields;

        if (json.rowList == undefined) {
            state.rowList = new Array(json.numDocs);
            for (var i = 0; i < json.numDocs; i++) {
                state.rowList[i] = 'Document ' + i;
            }
        } else {
            state.rowList = json.rowList;
        }
        if (json.colList == undefined) {
            state.colList = new Array(json.numTopics);
            for (var i = 0; i < json.numTopics; i++) {
                state.colList[i] = 'Topic ' + i;
            }
        } else {
            state.colList = json.colList;
        }

        state.maxVal = 1;
        state.minVal = 0;
        state.maxSize = Math.max(Math.abs(state.maxVal), Math.abs(state.minVal));
        state.divScale = d3.scale.linear().domain([-1*state.maxSize, state.maxSize]).range([0, colors.div.length - 1]);
        state.seqScale = d3.scale.linear().domain([state.minVal, state.maxVal]).range([0, colors.seq.length - 1])
        mvNS.areaScale.domain([0,state.maxSize]);

        useData();

        fetchMetadata();
    });
};

var useData = function() {
    initOrders();
    initColors();
    setWidthsHeightsScales();

    //getQuartiles();

    // Now make the data points.
    state.data = [];
    var v, tempObject;
    for (var r = 0; r < state.theta.length; r++) {
        for (var c in state.theta[r]) {
            v = state.theta[r][c];
            state.data.push({'row': r, 'col': parseInt(c), 'prop': v});
        }
    }
    state.currData = state.data.slice(0);

    // Draw it.
    updateMatrixView();
};

var initOrders = function() {
    // Initially order documents just as they come.
    state.currRowOrder = new Array(state.rowList.length);
    for (var i = 0; i < state.rowList.length; i++) {
        state.currRowOrder[i] = i;
    }
    state.currColOrder = new Array(state.colList.length);
    for (var i = 0; i < state.colList.length; i++) {
        state.currColOrder[i] = i;
    }

    // Also create arrays for selectedRows and selectedCols
    state.selectedRows = [];
    state.selectedCols = [];
    updateRowSelectDiv();
};

var initColors = function() {
    // Initialize colors all as default
    state.colColors = new Array(state.colList.length);
    for (var i = 0; i < state.colList.length; i++) {
        state.colColors[i] = defaultColor;
    }
    state.colsColored = [];

    state.rowColors = new Array(state.rowList.length);
    for (var i = 0; i < state.rowList.length; i++) {
        state.rowColors[i] = defaultColor;
    }
    state.rowsColored = [];
};

// TODO: bring up a warning alerting the user that this will bring back hidden columns
// TODO: This screws up the drawing order when bringing back gridlines. Fix using d3's sort operator.
var resetOrders = function() {
    state.currData = state.data.slice(0);
    initOrders();
    setWidthsHeightsScales();
    updateMatrixView();
    /*repositionData(); // TODO: might keep these as option for when we don't want to unhide cols...
    repositionLabels();*/
};

var resetColors = function() {
    initColors();
    matrixView.selectAll('.innerShape')
        .style('fill', defaultColor);
    matrixView.selectAll('.outerShape')
        .style('fill', defaultColor);
    matrixView.selectAll('.rowHighlightBar')
        .style('fill', defaultColor)
        .style('fill-opacity', 0);
    matrixView.selectAll('.colHighlightBar')
        .style('fill', defaultColor)
        .style('fill-opacity', 0);
};

var repositionData = function() {
    matrixView.selectAll('circle')
        .transition()
        .duration(transdur)
        .attr('cx', getCircleX)
        .attr('cy', getCircleY);
    matrixView.selectAll('rect.innerShape')
        .transition()
        .duration(transdur)
        .attr('x', getRectX)
        .attr('y', getRectY)
        .attr('transform', getRectRot);
    drawGrid();
};

var repositionLabels = function(cameFromSortDropdown, cameFromTopicSortDropdown) {
    if (cameFromSortDropdown == false || cameFromSortDropdown == undefined) {
        $('#sortSelect').val('');
    }
    if (state.aggregatingBy == undefined) {
        matrixView.selectAll('.rowLabel')
            .transition()
            .duration(transdur)
            .attr('x', mvNS.rowLabelWidth)
            .attr('y', function(d) { return state.y(state.currRowOrder.indexOf(d)); });

        matrixView.selectAll('.rowHighlightBar')
            .transition()
            .duration(transdur)
            .attr('y', function(d) { return state.y(state.currRowOrder.indexOf(d)) - mvNS.highlightBarHeight/2; })
    } else {
        matrixView.selectAll('.aggLabel')
            .transition()
            .duration(transdur)
            .attr('x', mvNS.rowLabelWidth)
            .attr('y', function(d) { return state.y(state.currAggOrder.indexOf(d)); });

        matrixView.selectAll('.aggHighlightBar')
            .transition()
            .duration(transdur)
            .attr('y', function(d) { return state.y(state.currAggOrder.indexOf(d)) - mvNS.highlightBarHeight/2; })
    }

    matrixView.selectAll('.colLabel')
        .transition()
        .duration(transdur)
        .attr('x', function(d) { return state.x(state.currColOrder.indexOf(d)); })
        .attr('transform', function(d) { return 'rotate(-90 ' + state.x(state.currColOrder.indexOf(d)) + ' ' + mvNS.colLabelHeight / 2 + ')'; });

    matrixView.selectAll('.colHighlightBar')
        .transition()
        .duration(transdur)
        .attr('x', function(d) { return state.x(state.currColOrder.indexOf(d)) - mvNS.highlightBarHeight/2; })
};

var updateMatrixView = function() {
    $("#main_content").addClass("withLoadingIndicator");
    // Specify which data to use (aggregate or full)
    var rowOrder = state.aggregatingBy == undefined ? state.currRowOrder : state.currAggOrder;
    var dataToUse = state.aggregatingBy == undefined ? state.currData : state.aggData;

    // Update scales
    setWidthsHeightsScales();

    // First, draw grid.
    drawGrid();

    // Next, draw labels.
    var colLabel = matrixView.selectAll('.colLabel')
        .data(state.currColOrder, String);
    colLabel.enter().append('svg:text')
        .attr('class', 'colLabel')
        .text(function(d) { return state.colList[d]; })
        .attr('x', function(d) { return state.x(state.currColOrder.indexOf(d)); })
        .attr('y', mvNS.colLabelHeight / 2)
        .attr("text-anchor", "middle")
        .attr('transform', function(d) { return 'rotate(-90 ' + state.x(state.currColOrder.indexOf(d)) + ' ' + mvNS.colLabelHeight / 2 + ')'; })
        .attr('cursor', 'pointer')
        .on('mouseover', function(d) {
            brushCol(d);
        })
        .on('mouseout', function(d) {
            unbrushCol(d);
        })
        .on('contextmenu', function(d) {
            selectCol(d);
            event.preventDefault();
            d3.select('#colContextMenu')
                .style('top', event.pageY+'px')
                .style('left', event.pageX+'px');
            //$('#colContextMenu').dropdown('toggle');
            $('#colContextMenu').show();
        })
        .on('click', function(d) {
            toggleColSelect(d);
        })
        .on('dblclick', function(d) { sortRowsBy([d]); })
        .call(d3.behavior.drag()
            .on('dragstart', function(d) {
                // If I want to do any sort of highlighting of the dragged thing, probably do it here.
            })
            .on('drag', function(d) {
                var newX = Math.max(state.x(-1), Math.min(state.x(state.colList.length), d3.event.x));
                d3.select(this)
                    .attr('x', newX)
                    .attr('transform', function() { return 'rotate(-90 ' + newX + ' ' + mvNS.colLabelHeight / 2 + ')'; });
            })
            .on('dragend', function(d) {
                // Undo any highlighting here.

                // Find closest position to where the col is dropped and stick it there in the order.
                var newX = d3.select(this).attr('x');
                var newI = getColIndexByX(newX);
                var oldI = state.currColOrder.indexOf(d);
                if (newI < oldI) {
                    state.currColOrder.splice(newI, 0, state.currColOrder.splice(oldI, 1)[0]);
                    $('#topicSortSelect').val('');
                } else if (newI > oldI) {
                    state.currColOrder.splice(newI, 0, state.currColOrder[oldI]);
                    state.currColOrder.splice(oldI, 1);
                    $('#topicSortSelect').val('');
                }
                repositionData();
                repositionLabels();
            })
        );
    colLabel.transition()
        .duration(transdur)
        .attr('x', function(d) { return state.x(state.currColOrder.indexOf(d)); })
        .attr('transform', function(d) { return 'rotate(-90 ' + state.x(state.currColOrder.indexOf(d)) + ' ' + mvNS.colLabelHeight / 2 + ')'; });
    colLabel.exit().remove();

    var rowLabel = matrixView.selectAll('.rowLabel')
        .data(rowOrder, String)
    rowLabel.enter().append('svg:text')
        .attr('class', 'rowLabel')
        .text(function(d) { return state.rowList[d]; })
        .attr('x', mvNS.rowLabelWidth)
        .attr('y', function(d) { return state.y(rowOrder.indexOf(d)); })
        .attr("text-anchor", "end")
        .attr('cursor', 'pointer')
        .on('mouseover', function(d) {
            brushRow(d);
            if (d3.select('#metadataTooltipCheckbox').filter(':checked')[0].length == 1) {
                d3.select('#metadataTooltip')
                    .html(getMetadataString(d))
                    .style('visibility', 'visible')
                    .style('top', event.pageY+'px')
                    .style('left', (event.pageX + 5) + 'px');
            }
        })
        .on('mouseout', function(d) {
            unbrushRow(d);
            d3.select('#metadataTooltip')
                .style('visibility', 'hidden')
                .html('');
        })
        .on('contextmenu', function(d) {
            selectRow(d);
            event.preventDefault();
            d3.select('#rowContextMenu')
                .style('top', event.pageY+'px')
                .style('left', event.pageX+'px');
            //$('#rowContextMenu').dropdown('toggle');
            $('#rowContextMenu').show();
        })
        .on('click', function(d) {
            toggleRowSelect(d);
        })
        .on('dblclick', function(d) { sortColsBy([d]); })
        .call(d3.behavior.drag()
            .on('dragstart', function(d) {
                // If I want to do any sort of highlighting of the dragged thing, probably do it here.
            })
            .on('drag', function(d) {
                var newY = Math.max(state.y(-1), Math.min(state.y(state.rowList.length), d3.event.y)); //TODO - aggList?
                d3.select(this)
                    .attr('y', newY);
            })
            .on('dragend', function(d) {
                // Undo any highlighting here.

                // Find closest position to where the row is dropped and stick it there in the order.
                var newY = d3.select(this).attr('y');
                var newI = getRowIndexByY(newY);
                var oldI = rowOrder.indexOf(d);
                if (newI < oldI) {
                    rowOrder.splice(newI, 0, rowOrder.splice(oldI, 1)[0]);
                    $('#sortSelect').val('None');
                } else if (newI > oldI) {
                    rowOrder.splice(newI, 0, rowOrder[oldI]);
                    rowOrder.splice(oldI, 1);
                    $('#sortSelect').val('None');
                }
                repositionData();
                repositionLabels();
            })
        );
    rowLabel.transition()
        .duration(transdur)
        .attr('x', mvNS.rowLabelWidth)
        .attr('y', function(d) { return state.y(rowOrder.indexOf(d)); });
    rowLabel.exit().remove();

    var rowHighlightBar = matrixView.selectAll('.rowHighlightBar')
        .data(rowOrder, String);
    rowHighlightBar.enter().append('svg:rect')
        .attr('class', 'rowHighlightBar catColor')
        .attr('x', state.x(-1))
        .attr('width', state.x.range()[1] - state.x.range()[0])
        .attr('y', function(d) { return state.y(d) - mvNS.highlightBarHeight/2; })
        .attr('height', mvNS.highlightBarHeight)
        .style('fill', function(d) { return state.rowColors[d]; })
        .style('fill-opacity', function(d) { return state.rowsColored.indexOf(d) != -1 ? mvNS.minFill : 0; })
        .on('mouseover', function(d) {
            brushRow(d);
        })
        .on('mouseout', function(d) {
            unbrushRow(d);
        })
        .on('click', function(d) {
            toggleRowSelect(d);
        });
    rowHighlightBar.transition()
        .duration(transdur)
        .attr('x', state.x(-1))
        .attr('y', function(d) { return state.y(rowOrder.indexOf(d)) - mvNS.highlightBarHeight/2; })
        .attr('width', state.x(state.currColOrder.length) - state.x.range()[0])
        .attr('height', mvNS.highlightBarHeight);
    rowHighlightBar.exit().remove();

    var colHighlightBar = matrixView.selectAll('.colHighlightBar')
        .data(state.currColOrder, String);
    colHighlightBar.enter().append('svg:rect')
        .attr('class', 'colHighlightBar catColor')
        .attr('y', state.y(-1))
        .attr('height', state.y.range()[1] - state.y.range()[0])
        .attr('x', function(d) { return state.x(d) - mvNS.highlightBarHeight/2; })
        .attr('width', mvNS.highlightBarHeight)
        .style('fill', function(d) { return state.colColors[d]; })
        .style('fill-opacity', function(d) { return state.colsColored.indexOf(d) != -1 ? mvNS.minFill : 0; })
        .on('mouseover', function(d) {
            brushCol(d);
        })
        .on('mouseout', function(d) {
            unbrushCol(d);
        })
        .on('click', function(d) {
            toggleColSelect(d);
        });
    colHighlightBar.transition()
        .duration(transdur)
        .attr('x', function(d) { return state.x(state.currColOrder.indexOf(d)) - mvNS.highlightBarHeight/2; })
        .attr('y', state.y(-1))
        .attr('width', mvNS.highlightBarHeight)
        .attr('height', state.y(rowOrder.length) - state.y.range()[0]);
    colHighlightBar.exit().remove();

    // Finally, draw circles.
    var innerShapes = matrixView.selectAll('.innerShape')
        .data(dataToUse, function(d) { return d.row + ',' + d.col; });
    innerShapes.enter().append('svg:circle')
        .attr('class','innerShape')
        //.attr('r', 0)
        .attr('r', getR)
        .attr('cx', getCircleX)
        .attr('cy', getCircleY)
        .style('stroke', 'black')
        .style('fill-opacity', .6)
        .style('fill', function(d) { return state.rowColors[d.row]; })// TODO: in future, make this apply to columns, too
        .on('mouseover', function(d) {
            brushRow(d.row);
            brushCol(d.col);
            showTooltip(d.prop);
        })
        .on('mouseout', function(d) {
            unbrushRow(d.row);
            unbrushCol(d.col);
            hideTooltip();
        })
        .on('click', function(d) {
            selectRow(d.row);
            selectCol(d.col);
        })
        // TODO: for some reason, having back to back transitions is breaking the data input...
        /*.transition()
        .duration(transdur)
        .attr('r', getR)*/
    innerShapes.transition()
        .duration(transdur)
        .attr('cx', getCircleX)
        .attr('cy', getCircleY);
    innerShapes.exit()
        .transition()
        .duration(transdur / 5.0)
        .attr('r', 0)
        .remove();
    $("#main_content").removeClass("withLoadingIndicator");
};

var drawGrid = function() {
    var rowOrder = state.aggregatingBy == undefined ? state.currRowOrder : state.currAggOrder;

    // First, draw grid.
    var xLineEdge = matrixView.selectAll('.xLineEdge')
        .data([-1, state.x.domain()[1]])
    xLineEdge.enter().append('svg:line')
        .attr('class', 'xLineEdge')
        .attr('stroke', gridcolor)
        .attr('stroke-width', gridWidth)
        .attr('x1', function(d) { return state.x(d); })
        .attr('y1', state.y(-1))
        .attr('x2', function(d) { return state.x(d); })
        .attr('y2', state.y(rowOrder.length));
    xLineEdge.transition()
        .duration(transdur)
        .attr('x1', function(d) { return state.x(d); })
        .attr('y1', state.y(-1))
        .attr('x2', function(d) { return state.x(d); })
        .attr('y2', state.y(rowOrder.length));
    var yLineEdge = matrixView.selectAll('.yLineEdge')
        .data([-1, state.y.domain()[1]])
    yLineEdge.enter().append('svg:line')
        .attr('class', 'yLineEdge')
        .attr('stroke', gridcolor)
        .attr('stroke-width', gridWidth)
        .attr('x1', state.x(-1))
        .attr('y1', function(d) { return state.y(d); })
        .attr('x2', state.x(state.currColOrder.length))
        .attr('y2', function(d) { return state.y(d); });
    yLineEdge.transition()
        .duration(transdur)
        .attr('x1', state.x(-1))
        .attr('y1', function(d) { return state.y(d); })
        .attr('x2', state.x(state.currColOrder.length))
        .attr('y2', function(d) { return state.y(d); });

    var xLine = matrixView.selectAll('.xLine')
        .data(state.currColOrder, String);
    xLine.enter().append('svg:line')
        .attr('class', 'xLine')
        .attr('stroke', gridcolor)
        .attr('stroke-width', gridWidth)
        .attr('x1', function(d) {return state.x(state.currColOrder.indexOf(d)); })
        .attr('y1', state.y(-1))
        .attr('x2', function(d) {return state.x(state.currColOrder.indexOf(d)); })
        .attr('y2', state.y(rowOrder.length));
    xLine.transition()
        .duration(transdur)
        .attr('x1', function(d) {return state.x(state.currColOrder.indexOf(d)); })
        .attr('y1', state.y(-1))
        .attr('x2', function(d) {return state.x(state.currColOrder.indexOf(d)); })
        .attr('y2', state.y(rowOrder.length));
    xLine.exit().remove();

    var yLine = matrixView.selectAll('.yLine')
        .data(rowOrder, String);
    yLine.enter().append('svg:line')
        .attr('class', 'yLine')
        .attr('stroke', gridcolor)
        .attr('stroke-width', gridWidth)
        .attr('x1', state.x(-1))
        .attr('y1', function(d) { return state.y(rowOrder.indexOf(d)); })
        .attr('x2', state.x(state.currColOrder.length))
        .attr('y2', function(d) { return state.y(rowOrder.indexOf(d)); });
    yLine.transition()
        .duration(transdur)
        .attr('x1', state.x(-1))
        .attr('y1', function(d) { return state.y(rowOrder.indexOf(d)); })
        .attr('x2', state.x(state.currColOrder.length))
        .attr('y2', function(d) { return state.y(rowOrder.indexOf(d)); })
    yLine.exit().remove();
};

var getColIndexByX = function(xPos) {
    var index = Math.round(state.x.invert(xPos));
    return index < 0 ? 0 : (index >= state.colList.length ? state.colList.length - 1 : index);
};

var getRowIndexByY = function(yPos) {
    var index = Math.round(state.y.invert(yPos));
    if (state.aggregatingBy == undefined) {
        return index < 0 ? 0 : (index >= state.rowList.length ? state.rowList.length - 1 : index);
    } else {
        return index < 0 ? 0 : (index >= state.aggList.length ? state.aggList.length - 1 : index);
    }
};

var getR = function(datum) {
    //return datum.prop * mvNS.maxR;
    //return mvNS.rScale(datum.prop);
    var baseR = Math.sqrt(mvNS.areaScale(Math.abs(datum.prop)));
    return state.aggregatingBy == undefined ? baseR : aggSizeFactor*baseR;
    /*if (state.drawByQuartiles) {
     if (datum.prop < state.q1) {
     return Math.sqrt(mvNS.areaScale(0))
     } else if (datum.prop < state.q2) {
     return Math.sqrt(mvNS.areaScale(.25))
     } else if (datum.prop < state.q3) {
     return Math.sqrt(mvNS.areaScale(.50))
     } else {
     return Math.sqrt(mvNS.areaScale(1))
     }
     } else {
     return Math.sqrt(mvNS.areaScale(datum.prop));
     }*/
};

var getCircleX = function(datum) {
    return state.x(state.currColOrder.indexOf(datum.col));
};

var getCircleY = function(datum) {
    if (state.aggregatingBy == undefined) {
        return state.y(state.currRowOrder.indexOf(datum.row));
    } else {
        return state.y(state.currAggOrder.indexOf(datum.row));
    }
};

var getRectX = function(datum) {
    return getCircleX(datum) - getRectW(datum)/2;
};

var getRectY = function(datum) {
    return getCircleY(datum) - getRectW(datum)/2;
};

var getRectW = function(datum) {
    return Math.sqrt(2) * getR(datum);
};

var getRectRot = function(datum) {
    return (datum.prop >= 0) ? 'rotate(-45 ' + getCircleX(datum) + ' ' + getCircleY(datum) + ')' : 'none';
}

/************************ CROSS VIEWS ***********************************/

// When brushing col, also brush the rowView
var brushCol = function(colNum) {
    matrixView.selectAll('.innerShape').select(function (d) { return d.col == colNum ? this : null; })
        .style('stroke-width', 2);
    matrixView.selectAll('.colLabel').select(function (d) { return d == colNum ? this : null; })
        .style('font-weight', 'bold');
    d3.selectAll('.topic_model_line_graph g.topic_' + colNum).classed('highlight-red',true);
    d3.selectAll('.topic_model_line_graph g.topic_' + colNum).classed('active',true);
    d3.selectAll('.tLabel').select(function(d) { return parseInt(d) == colNum ? this : null; })
        .style('font-weight', 'bold');
};

var unbrushCol = function(colNum) {
    matrixView.selectAll('.innerShape').select(function (d) { return d.col == colNum ? this : null; })
        .style('stroke-width', 1);
    matrixView.selectAll('.colLabel').select(function (d) { return d == colNum ? this : null; })
        .style('font-weight', 'normal');
    d3.selectAll('.topic_model_line_graph g.topic_' + colNum).classed('highlight-red',false);
    d3.selectAll('.topic_model_line_graph g.topic_' + colNum).classed('active',false);
    d3.selectAll('.tLabel').select(function(d) { return parseInt(d) == colNum ? this : null; })
        .style('font-weight', 'normal');
};

// When brushing row, also brush _____
var brushRow = function(rowNum) {
    matrixView.selectAll('.innerShape').select(function (d) { return d.row == rowNum ? this : null; })
        .style('stroke-width', 2);
    matrixView.selectAll('.rowLabel').select(function (d) { return d == rowNum ? this : null; })
        .style('font-weight', 'bold');
};

var unbrushRow = function(rowNum) {
    matrixView.selectAll('.innerShape').select(function (d) { return d.row == rowNum ? this : null; })
        .style('stroke-width', 1);
    matrixView.selectAll('.rowLabel').select(function (d) { return d == rowNum ? this : null; })
        .style('font-weight', 'normal');
};

var toggleColSelect = function(colNum) {
    selectCol(colNum);
    var colIndex = state.selectedCols.indexOf(colNum);
    if (colIndex == -1) {
        state.selectedCols.push(colNum);
    } else {
        state.selectedCols.splice(colIndex, 1);
    }
    updateColSelectDiv();
};

var updateColSelectDiv = function() {
    if (state.selectedCols == undefined) {
        state.selectedCols = [];
    }
    if (state.selectedCols.length == 0) {
        d3.select('#selectedCols').html('No topics selected');
    } else {
        state.selectedCols.sort();
        var selectedColsList = d3.select('#selectedCols').html('');
        for (var i = 0; i < state.selectedCols.length; i++) {
            selectedColsList.append('a')
                .attr('class', 'selectedColLink')
                .attr('colNum', state.selectedCols[i])
                .style('cursor', 'pointer')
                .text(state.colList[state.selectedCols[i]]);
            selectedColsList.append('br');
        }
        d3.selectAll('.selectedColLink')
            .on('click', function() {
                selectCol(parseInt(d3.select(this).attr('colNum')));
            });
    }
};

var selectCol = function(colNum) {
    state.selectedCol = colNum;
    renderTopicView(colNum);
};

var toggleRowSelect = function(rowNum) {
    selectRow(rowNum);
    var rowIndex = state.selectedRows.indexOf(rowNum);
    if (rowIndex == -1) {
        state.selectedRows.push(rowNum);
    } else {
        state.selectedRows.splice(rowIndex, 1);
    }
    updateRowSelectDiv();
};

var updateRowSelectDiv = function() {
    if (state.selectedRows == undefined) {
        state.selectedRows = [];
    }
    if (state.selectedRows.length == 0) {
        d3.select('#selectedRows').html('No documents selected');
    } else {
        state.selectedRows.sort();
        var selectedRowsList = d3.select('#selectedRows').html('');
        for (var i = 0; i < state.selectedRows.length; i++) {
            selectedRowsList.append('a')
                .attr('class', 'selectedRowLink')
                .attr('rowNum', state.selectedRows[i])
                .style('cursor', 'pointer')
                .text(state.rowList[state.selectedRows[i]]);
            selectedRowsList.append('br');
        }
        d3.selectAll('.selectedRowLink')
            .on('click', function() {
                selectRow(parseInt(d3.select(this).attr('rowNum')));
            });
    }
};

var selectRow = function(rowNum) {
    state.selectedRow = rowNum;
    renderDocView(rowNum);
};

/************************************* SIDE BAR VEIWS ********************************************/
    // TODO: Make this look pretty and generate sizes dynamically
var renderTopicView = function(topicNum) {
    d3.select('#selectedTopicNum').html(topicNum);
    d3.select('#topicViewTitle')
        .on('dblclick', function() {
            $('#renameTopicModal').modal();
        })
        .on('mouseover', function() {
            brushCol(topicNum);
        })
        .on('mouseout', function() {
            unbrushCol(topicNum);
        });
    $('#topicViewTitle')
        .css('cursor','default')
        .css('user-select','none');
    var metadataStr = '';
    for (var fieldName in state.topicMetadata[topicNum]) {
        metadataStr += fieldName + ': ' + state.topicMetadata[topicNum][fieldName] + '<br />'
    }
    d3.select('#topicMetadataTab')
        .html('<h4>Topic: ' + state.colList[topicNum] + '</h4>' + metadataStr);

    d3.select('#topicView').html('<h4>Topic: ' + state.colList[topicNum] + '</h4>');

    var $TOPIC_URL = flask_util.url_for('corpus_get_topic',
                        {corpus_name:corpus_name,
                         topic_num: topicNum == 0 ? '0' : topicNum, // Cheap hack--I think flask_util.url_for can't deal with 0 as a parameter
                         num_words:tvNS.numWords});
    d3.json($TOPIC_URL, function(json) {
        if (json == null) {
            d3.select('#topicView').append('div')
                .attr('class', 'alert alert-block')
                .html('Topic data not found.')
        } else {
            topicView = d3.select('#topicView').append('svg:svg')
                .attr('width', tvNS.w)
                .attr('height', tvNS.h);

            var wordList = json.wordList;
            var propList = json.propList;

            var barScale = d3.scale.linear()
                .domain([0, propList[0]])
                .range([0, tvNS.maxBarWidth]);

            var wordLabel = topicView.selectAll('.wordLabel')
                .data(wordList, String); // Not sure I'd want to animate this, but whatever.
            wordLabel.enter().append('svg:text')
                .attr('class', 'wordLabel')
                .text(function(d) { return d; })
                .attr('x', tvNS.barXoffset - tvNS.barBuffer)
                .attr('y', function(d,i) { return tvNS.barYoffset + (i + 1)*(tvNS.barBuffer + tvNS.barHeight); })
                .attr('text-anchor', 'end')
                .attr('alignment-baseline', 'middle');
            wordLabel.exit().remove();

            var wordBar = topicView.selectAll('.wordBar')
                .data(propList);
            wordBar.enter().append('svg:rect')
                .attr('class', 'wordBar')
                .attr('x', tvNS.barXoffset + tvNS.barBuffer)
                .attr('y', function(d,i) { return tvNS.barYoffset + (i + 1)*(tvNS.barBuffer + tvNS.barHeight) - .5*(tvNS.barHeight); })
                .attr('width', function(d) { return barScale(d); })
                .attr('height', tvNS.barHeight)
                .style('stroke', tvNS.barBorder)
                .style('fill', tvNS.barFill)
                .style('fill-opacity', tvNS.barFillOpacity);
            wordBar.exit().remove();
        }
    });
};

var renderDocView = function(docNum) {
    if (docNum != undefined) {
        d3.select('#selectedDocNum').html(docNum);
        d3.select('#docViewTitle')
            .on('dblclick', function() {
                openDocInTextViewer(docNum);
            })
            .on('mouseover', function() {
                brushRow(docNum);
            })
            .on('mouseout', function() {
                unbrushRow(docNum);
            });
        $('#docViewTitle')
            .css('cursor','default')
            .css('user-select','none');
        var thetaD = state.aggregatingBy == undefined ? state.theta[docNum] : state.aggTheta[docNum];
        var thetaDtopics = new Array(thetaD.length);
        var thetaDpercs = new Array(thetaD.length);
        var i = 0;
        for (var topic in thetaD) {
            thetaDtopics[i] = topic;
            thetaDpercs[i] = thetaD[topic];
            i++;
        }

        dvNS.barFill = state.aggregatingBy == undefined ? state.rowColors[docNum] : state.aggColors[docNum];

        thetaDtopics.sort(function(a,b) { return thetaD[b] - thetaD[a]; });
        thetaDpercs.sort(function(a,b) { return b - a; })

        $docContainer = $('#right_sidebar_bottom_content');
        dvNS.w = $docContainer.width()-30;
        dvNS.h = $docContainer.height();

        var numTopics = thetaDtopics.length;
        if (dvNS.w < numTopics*dvNS.minBarWidth + (numTopics+1)*dvNS.barBuffer) {
            dvNS.barWidth = dvNS.minBarWidth;
        } else {
            dvNS.barWidth = Math.floor((dvNS.w - dvNS.barBuffer)/numTopics);
        }
        dvNS.xScale = d3.scale.linear()
            .domain([0, numTopics-1])
            .range([dvNS.barBuffer, (numTopics-1)*(dvNS.barBuffer + dvNS.barWidth)]);

        dvNS.yScale = d3.scale.linear()
            //.domain([0, Math.max.apply(Math, thetaDpercs)])
            .domain([0,1])
            .range([0, dvNS.h - 2*dvNS.chartBuffer - dvNS.labelBuffer]);

        // Metadata tab
        if (state.aggregatingBy == undefined) {
            var docMetadataTab = d3.select('#docMetadataTab')
                .html('<h2>Document: ' + state.rowList[docNum] + '</h2>' + '<p>' + getMetadataString(docNum) + '</p>');
        } else {
            var aggBtnGrp = d3.select('#docMetadataTab')
                .html('')
                .append('div')
                .attr('class', 'btn-group btn-group-vertical');
            for (var i = 0; i < state.aggregates[docNum].length; i++) {
                aggBtnGrp.append('button')
                    .attr('class', 'btn')
                    .attr('docNum', state.aggregates[docNum][i])
                    .text(state.rowList[state.aggregates[docNum][i]])
                    .on('click', function() {
                        var docNum = parseInt(d3.select(this).attr('docNum'));
                        openDocInTextViewer(docNum);
                    });
            }
        }

        // Topic Counts tab // TODO: clean this up, make it prettier
        var docTopicCountsTab = d3.select('#docTopicCountsTab')
            .html('')
            .append('svg:svg')
            .data([thetaDpercs])
            //.attr('width', dvNS.w)
            //.attr('height', dvNS.h);

        var tLabels = docTopicCountsTab.selectAll('.tLabel')
            .data(thetaDtopics)
            .enter().append('svg:text')
            .attr('class', 'tLabel')
            .text(function(d) { return d; })
            .attr('x', function(d,i) { return dvNS.xScale(i) + .5*dvNS.barWidth; })
            .attr('y', dvNS.h - dvNS.labelBuffer + dvNS.barBuffer)
            .attr('text-anchor', 'middle')
            .attr('alignment-baseline', 'hanging')
            //.style('font-weight', 'bold')
            .on('click', function(d) {
                selectCol(d)
            });

        var tBars = docTopicCountsTab.selectAll('.tBar')
            .data(thetaDpercs)
            .enter().append('svg:rect')
            .attr('class', 'tBar')
            .attr('x', function(d, i) { return dvNS.xScale(i)/* - .5*dvNS.barWidth*/; })
            .attr('y', function(d) { return dvNS.h - dvNS.labelBuffer - dvNS.yScale(d); })
            .attr('width', dvNS.barWidth)
            .attr('height', function(d) { return dvNS.yScale(d); })
            .style('stroke', dvNS.barBorder)
            .style('fill', dvNS.barFill)
            .style('fill-opacity', dvNS.barFillOpacity)
            .on('click', function(d, i) {
                selectCol(thetaDtopics[i]);
            })
            .on('mouseover', function(d, i) {
                brushCol(thetaDtopics[i]);
            })
            .on('mouseout', function(d, i) {
                unbrushCol(thetaDtopics[i]);
            });

        var pLabels = docTopicCountsTab.selectAll('.pLabel')
            .data(thetaDpercs)
            .enter().append('svg:text')
            .attr('class', 'pLabel')
            .text(function(d) { return d < .01 ? '<1%' : Math.floor(d*100).toString() + '%' })
            .attr('x', function(d,i) { return dvNS.xScale(i) + .5*dvNS.barWidth; })
            .attr('y', function(d) { return dvNS.h - dvNS.labelBuffer - dvNS.yScale(d) - 5; })
            .attr('text-anchor', 'middle');

        // Topic Layout tab
        //var topicKeys = thetaDtopics.slice(0,5).map(function(s) {return 'topic_' + s;});
        var pixel_size = $('#right_sidebar_bottom_content').height();
        var overviewURL = flask_util.url_for("text_get_topic_model_line_graph",
            { corpus_name: corpus_name,
              text_name: getFilename(docNum),
              pixel_size: pixel_size
            });
        $.get(overviewURL, function(response) {
            d3.select('#docTopicLayoutTab').html(response);
            var line = d3.selectAll('.topic_model_line_graph g')
                .on('click', function() {
                    var topicID = parseInt(d3.select(this).attr('data-key').split('_')[1]);
                    selectCol(topicID);
                })
                .on('mouseover', function(d, i) {
                    var topicID = parseInt(d3.select(this).attr('data-key').split('_')[1]);
                    brushCol(topicID);
                })
                .on('mouseout', function(d, i) {
                    var topicID = parseInt(d3.select(this).attr('data-key').split('_')[1]);
                    unbrushCol(topicID);
                });
        });
    }
};

var getMetadataString = function(docNum) {
    var m = state.metadata[docNum];
    var s = '';
    if ('Title' in m) {
        s += 'Title: ' + m['Title'] + '<br />';
    }
    if ('Author' in m) {
        s += 'Author: ' + m['Author'] + '<br />';
    }
    if ('Genre' in m) {
        s += 'Genre: ' + m['Genre'] + '<br />';
    }
    for (var field in m) {
        if (field != 'Author' && field != 'Title' && field != 'Genre') {
            s += field + ': ' + m[field] + '<br />';
        }
    }
    return s == '' ? 'No metadata available' : s;
};

var getFilename = function(docNum) {
    var textName = state.metadata[docNum].filename.split('/').pop();
    if (textName.indexOf('.txt') != -1) {
        textName = textName.substring(0, textName.indexOf('.txt'));
    }
    return textName;
};

var openDocInTextViewer = function(docNum) {
    window.open(flask_util.url_for('text_view_by_name',
        { corpus_name: corpus_name,
            text_name: getFilename(docNum)
        }));
};

var openDocsInMesoViewer = function(docList) {
    var text_names = new Array(docList.length);
    for (var i = 0; i < docList.length; i++) {
        text_names[i] = getFilename(docList[i]);
    }
    window.open(flask_util.url_for("corpus_mesoview",
        { corpus_name: corpus_name,
          included_text_names: text_names
        }));
};

initialize();
//fetchData();
//fetchFakeData();
fetchTheta();

localStorage[corpus_name] = "";
var removeTopicColor = function(topic) {
    uncolorCols([parseInt(topic.split('topic')[1])]);
};
var applyTopicColor = function(topic, color) {
    colorCols([parseInt(topic.split('topic')[1])], color);
};
window.addEventListener('storage', function() {
    var strToObj = function(str) {
        var topicList = str.split(',');
        var tmp;
        var obj = {};
        for (var i = 0; i < topicList.length; i++) {
            tmp = topicList[i].split('-');
            obj[tmp[0]] = tmp[1];
        }
        return obj;
    }
    if (event.key == corpus_name) {
        var oldTopicColors = strToObj(event.oldValue);
        var newTopicColors = strToObj(event.newValue);

        for (var topic in oldTopicColors) {
            if (! (topic in newTopicColors)) {
                removeTopicColor(topic);
            }
        }
        for (var topic in newTopicColors) {
            if (! (topic in oldTopicColors) || newTopicColors[topic] != oldTopicColors[topic]) {
                applyTopicColor(topic, newTopicColors[topic]);
            }
        }
    }
}, false);