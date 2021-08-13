# Oval.bio Charts

This is a tool to bundle CSVs with metadata then publish them via email. The goal is to define the structure of the zip bundles in a standard way so it's straightforward to generate arbitrary charts and reports to be collected and rendered on a website and be made available and in an easily downloadable format for clients to keep a copy of their own data.

## Installation

To install, enter a shell with python/pip and unzip and enter the source directory and enter the following commands:

> pip install -r requirements.txt

> pip install -e .

Then you should have an oval​ command in the path.
To print help:

> oval -h

To run unit tests

> oval test

## Running

To quickly test the workflow with generated data and all defaults, first run the following commands:

> oval create

> oval gen-chart

Then create a file in the current working directory called bundle.txt with the contents:

> [xyz-ips snippet="oval-charts"]

This is needed so the Wordpress plugin XYZ PHP Snippets can expand the chart rendering html and javascript. The snippet is the content of charts.php in the repo. Next, run:

> oval set-text bundle.txt

> oval --log-level=DEBUG publish -f from@email.com -t to@email.com -s mx.email.com -p 587 -u smtp-user -p password

The SMTP server specified when publishing should support SSL.

## Integration

The idea is for this command line application to be called from whatever process that generates the original raw csv data. After that data is generated, a script could collect it and bundle it with metadata describing the data then publish the bundle.
