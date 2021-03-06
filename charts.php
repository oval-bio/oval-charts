<?php

$media = get_attached_media('');
foreach($media as $attachment) {
?>

<script type="text/javascript" src="/data/jquery-3.6.0.min.js"></script>
<script type="text/javascript" src="/data/jszip/dist/jszip.min.js"></script>
<script type="text/javascript" src="/data/jszip-utils/dist/jszip-utils.min.js"></script>
<script src="/data/d3/d3.v4.js"></script>
<script type="module" src="/data/d3-dsv/csv.js"></script>

<div id="session_metadata_<?=$attachment->ID;?>"></div>
<div id="instrument_charts_<?=$attachment->ID;?>"></div>

<script>
    function showText(elt, text) {
        elt.innerHTML += "<p>" + text + "</p>";
    }

    function showMetadata(elt, content) {
        var time_str = new Date(content.timestamp).toString();
        elt.innerHTML +=
            "<p>" +
              content.title + "<br/>" +
              time_str
            "</p>";
    }

    function showChart(chart, data) {
        // set the dimensions and margins of the graph
        var margin = {top: 60, right: 30, bottom: 80, left: 60},
            width = 560 - margin.left - margin.right,
            height = 400 - margin.top - margin.bottom;

        // append the svg object to the body of the page
        var svg = d3.select("#instrument_charts_<?=$attachment->ID;?>")
          .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
          .append("g")
            .attr("transform",
                  "translate(" + margin.left + "," + margin.top + ")");

        //Read the data
        var csv_data = d3.csvParse(data, d3.autoType);

        // select scale function
        var x_scale = d3.scaleLinear;
        var y_scale = d3.scaleLinear;
        var x_min = chart.x_min;
        var y_min = chart.y_min;
        var x_max = chart.x_max;
        var y_max = chart.y_max;
        if("x_scale" in chart){
          if(chart.x_scale == "linear"){
            x_scale = d3.scaleLinear;
          }
          else if(chart.x_scale == "time"){
            x_scale = d3.scaleTime;
            x_min = Date.parse(chart.x_min);
            x_max = Date.parse(chart.x_max);
          }
        }
        if("y_scale" in chart){
          if(chart.y_scale == "linear"){
            y_scale = d3.scaleLinear;
          }
          else if(chart.y_scale == "time"){
            y_scale = d3.scaleTime;
            y_min = Date.parse(chart.y_min);
            y_max = Date.parse(chart.y_max);
          }
        }

        // Add X axis
        var x = x_scale()
          //.domain(d3.extent(csv_data, function(d) { return d[chart.x_column]; }))
          .domain([x_min, x_max])
          .range([ 0, width ]);
        xAxis = svg.append("g")
          .attr("transform", "translate(0," + height + ")")
          .call(d3.axisBottom(x));

        // Add Y axis
        var y = y_scale()
          //.domain(d3.extent(csv_data, function(d) { return d[chart.y_column]; }))
          .domain([y_min, y_max])
          .range([ height, 0 ]);
        yAxis = svg.append("g")
          .call(d3.axisLeft(y));

        svg.append('text')
          .attr('x', width/2)
          .attr('y', -20)
          .attr('text-anchor', 'middle')
          .style('font-family', 'Helvetica')
          .style('font-size', 20)
          .text(chart.title);

        // X label
        svg.append('text')
          .attr('x', width/2)
          .attr('y', height+40)
          .attr('text-anchor', 'middle')
          .style('font-family', 'Helvetica')
          .style('font-size', 12)
          .text(chart.x_label);

        // Y label
        svg.append('text')
          .attr('text-anchor', "middle")
          .attr('transform', 'translate(-40,' + height/2 + ')rotate(-90)')
          .style('font-family', 'Helvetica')
          .style('font-size', 12)
          .text(chart.y_label);

        // Add a clipPath: everything out of this area won't be drawn.
        var clip = svg.append("defs").append("svg:clipPath")
            .attr("id", "clip")
            .append("svg:rect")
            .attr("width", width )
            .attr("height", height )
            .attr("x", 0)
            .attr("y", 0);

        // Add brushing
        var brush = d3.brushX()                   // Add the brush feature using the d3.brush function
            .extent( [ [0,0], [width,height] ] )  // initialise the brush area: start at 0,0 and finishes at width,height: it means I select the whole graph area
            .on("end", updateChart);              // Each time the brush selection changes, trigger the 'updateChart' function

        // Create the line variable: where both the line and the brush take place
        var line = svg.append('g')
          .attr("clip-path", "url(#clip)");

        // Add the line
        line.append("path")
          .datum(csv_data)
          .attr("class", "line")  // I add the class line to be able to modify this line later on.
          .attr("fill", chart.fill)
          .attr("stroke", chart.stroke)
          .attr("stroke-width", chart.stroke_width)
          .attr("d", d3.line()
            .x(function(d) { return x(d[chart.x_column]) })
            .y(function(d) { return y(d[chart.y_column]) })
            );

        // Add the brushing
        line
          .append("g")
            .attr("class", "brush")
            .call(brush);

        // A function that set idleTimeOut to null
        var idleTimeout;
        function idled() { idleTimeout = null; }

        // A function that update the chart for given boundaries
        function updateChart() {

          // What are the selected boundaries?
          extent = d3.event.selection;

          // If no selection, back to initial coordinate. Otherwise, update X axis domain
          if(!extent){
            if (!idleTimeout) return idleTimeout = setTimeout(idled, 350); // This allows to wait a little bit
            x.domain([ 4,8]);
          }else{
            x.domain([ x.invert(extent[0]), x.invert(extent[1]) ]);
            line.select(".brush").call(brush.move, null); // This remove the grey brush area as soon as the selection has been done
          }

0         // Update axis and line position
          xAxis.transition().duration(1000).call(d3.axisBottom(x));
          line
              .select('.line')
              .transition()
              .duration(1000)
              .attr("d", d3.line()
                .x(function(d) { return x(d[chart.x_column]) })
                .y(function(d) { return y(d[chart.y_column]) })
              );
        }

        // If user double click, reinitialize the chart
        svg.on("dblclick",function(){
          x.domain(d3.extent(csv_data, function(d) { return d[chart.x_column]; }))
          xAxis.transition().call(d3.axisBottom(x))
          line
            .select('.line')
            .transition()
            .attr("d", d3.line()
              .x(function(d) { return x(d[chart.x_column]) })
              .y(function(d) { return y(d[chart.y_column]) })
          );
          //location.reload();
        });
    }

    var htmltext = JSZipUtils.getBinaryContent("<?=$attachment->guid;?>", function (err, data) {
        var elt = document.getElementById('session_metadata_<?=$attachment->ID;?>');
        if (err) {
            showText(elt, err);
            return;
        }
        try {
            JSZip.loadAsync(data)
                .then(function (zip) {
                    zip.file("metadata.json").async("string").then(
                      function(data) {
                        // get metadata
                        var metadata = JSON.parse(data);
                        showMetadata(elt, metadata);

                        // load charts
                        var chart_data = metadata.chart_data;
                        for(var chart_idx = 0; chart_idx < chart_data.length; chart_idx++) {
                          var chart = chart_data[chart_idx];
                          const module = {
                            chart: chart,
                            loadChart: function(data) {
                              showChart(this.chart, data);
                            }};

                          const load_chart = module.loadChart;

                          zip.file(chart.filename).async("string").then(
                            load_chart.bind(module));
                        }

                      });
                });
        } catch(e) {
            showText(elt, e);
        }
    });
</script>

<?
}
?>
