<?php
$media = get_attached_media('');
foreach($media as $attachment) {
  echo $attachment->guid;
?>
<script type="text/javascript" src="/data/jquery-3.6.0.min.js"></script>
<script type="text/javascript" src="/data/jszip/dist/jszip.min.js"></script>
<script type="text/javascript" src="/data/jszip-utils/dist/jszip-utils.min.js"></script>
<!-- Load d3.js -->
<script src="/data/d3/d3.v4.js"></script>
<div id="zip_output"></div>
<iframe id="iframe"></iframe>
<script>
    function showError(elt, err) {
        elt.innerHTML = "<p class='alert alert-danger'>" + err + "</p>";
    }
    function showContent(elt, content) {
        elt.innerHTML = "<p class='alert alert-success'>loaded !<br/>" +
          "Content = " + content + "</p>";
    }
    var htmltext = JSZipUtils.getBinaryContent("<?=$attachment->guid;?>", function (err, data) {
        var elt = document.getElementById('zip_output');
        if (err) {
            showError(elt, err);
            return;
        }
        try {
            JSZip.loadAsync(data)
                .then(function (zip) {
                    for(var name in zip.files) {
                        if (name.substring(name.lastIndexOf('.') + 1) === "json") {
                            return zip.file(name).async("string");
                        }
                    }
                    return zip.file("").async("string");
                })
                .then(function success(text) {
                    $('#iframe').contents().find('html').html(text);
                    showContent(elt, text);
                }, function error(e) {
                    showError(elt, e);
                });
        } catch(e) {
            showError(elt, e);
        }
    });
</script>

<!-- Create a div where the graph will take place -->
<div id="my_dataviz"></div>

<script>

// set the dimensions and margins of the graph
var margin = {top: 60, right: 30, bottom: 80, left: 60},
    width = 560 - margin.left - margin.right,
    height = 400 - margin.top - margin.bottom;

// append the svg object to the body of the page
var svg = d3.select("#my_dataviz")
  .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform",
          "translate(" + margin.left + "," + margin.top + ")");

//Read the data
d3.csv("https://oval.bio/data/simplifies_extended.csv",

  // When reading the csv, I must format variables:
  function(d){
    return { date : d3.timeParse("%Y-%m-%d %H:%M:%S")(d.date), value : d.value }
  },

  // Now I can use this dataset:
  function(data) {

    // Add X axis --> it is a date format
    var x = d3.scaleTime()
      .domain(d3.extent(data, function(d) { return d.date; }))
      .range([ 0, width ]);
    xAxis = svg.append("g")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x));

    // Add Y axis
    var y = d3.scaleLinear()
      .domain([0, d3.max(data, function(d) { return +d.value; })])
      .range([ height, 0 ]);
    yAxis = svg.append("g")
      .call(d3.axisLeft(y));

      svg.append('text')
      .attr('x', width/2)
      .attr('y', -20)
      .attr('text-anchor', 'middle')
      .style('font-family', 'Helvetica')
      .style('font-size', 20)
      .text('Spirometer Graph');

      // X label
      svg.append('text')
      .attr('x', width/2)
      .attr('y', height+40)
      .attr('text-anchor', 'middle')
      .style('font-family', 'Helvetica')
      .style('font-size', 12)
      .text('Time (MS)');
      //
      // Y label
      svg.append('text')
      .attr('text-anchor', "middle")
      .attr('transform', 'translate(-40,' + height/2 + ')rotate(-90)')
      .style('font-family', 'Helvetica')
      .style('font-size', 12)
      .text('Svpulse');

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
        .on("end", updateChart)               // Each time the brush selection changes, trigger the 'updateChart' function

    // Create the line variable: where both the line and the brush take place
    var line = svg.append('g')
      .attr("clip-path", "url(#clip)")

    // Add the line
    line.append("path")
      .datum(data)
      .attr("class", "line")  // I add the class line to be able to modify this line later on.
      .attr("fill", "none")
      .attr("stroke", "steelblue")
      .attr("stroke-width", 1.5)
      .attr("d", d3.line()
        .x(function(d) { return x(d.date) })
        .y(function(d) { return y(d.value) })
        )

    // Add the brushing
    line
      .append("g")
        .attr("class", "brush")
        .call(brush);

    // A function that set idleTimeOut to null
    var idleTimeout
    function idled() { idleTimeout = null; }

    // A function that update the chart for given boundaries
    function updateChart() {

      // What are the selected boundaries?
      extent = d3.event.selection

      // If no selection, back to initial coordinate. Otherwise, update X axis domain
      if(!extent){
        if (!idleTimeout) return idleTimeout = setTimeout(idled, 350); // This allows to wait a little bit
        x.domain([ 4,8])
      }else{
        x.domain([ x.invert(extent[0]), x.invert(extent[1]) ])
        line.select(".brush").call(brush.move, null) // This remove the grey brush area as soon as the selection has been done
      }

      // Update axis and line position
      xAxis.transition().duration(1000).call(d3.axisBottom(x))
      line
          .select('.line')
          .transition()
          .duration(1000)
          .attr("d", d3.line()
            .x(function(d) { return x(d.date) })
            .y(function(d) { return y(d.value) })
          )
    }

    // If user double click, reinitialize the chart
    svg.on("dblclick",function(){
      x.domain(d3.extent(data, function(d) { return d.date; }))
      xAxis.transition().call(d3.axisBottom(x))
      line
        .select('.line')
        .transition()
        .attr("d", d3.line()
          .x(function(d) { return x(d.date) })
          .y(function(d) { return y(d.value) })
      )
      //location.reload();
    });

})
</script>
<?
}
?>
