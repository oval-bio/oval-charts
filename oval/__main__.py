import csv
import json
import logging
import math
import os
import subprocess
import sys
import tempfile
import unittest
# import zipfile

import click

import oval.core

from tabulate import tabulate

logger = logging.getLogger(__name__)


@click.group(context_settings={"help_option_names": ['-h', '--help']})
@click.option(
    "--log", envvar="OVAL_LOG", default="-",
    help="Log file. Use '-' for stdout.")
@click.option(
    "--log-level", default="WARNING",
    help="Log output level.")
@click.option(
    '--profiling/--no-profiling', default=False,
    help="Print performance profiling info on exit.")
@click.option(
    "--bundle", default="session.zip",
    help="oval.bio session data bundle file.")
@click.pass_context
def root(context, log, log_level, profiling, bundle):
    """
    oval.bio session bundle utilities.
    """
    class Obj:
        pass

    context.obj = obj = Obj()
    obj.log = log
    obj.log_level = log_level
    obj.profiling = profiling
    obj.bundle = bundle

    level = getattr(logging, obj.log_level.upper())
    oval.core.setup_logging(obj.log, level)
    logger.debug("bundle: {}".format(bundle))


@root.command()
@click.option(
    '--pattern', '-p', default='test*.py',
    help="test files to match")
@click.pass_obj
def test(obj, pattern):
    """
    Run test suite.
    """
    with oval.core.cli_context(obj):
        loader = unittest.TestLoader()
        suite = loader.discover(
            os.path.abspath(os.path.dirname(__file__)),
            pattern=pattern)
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)


@root.command()
@click.pass_obj
def flake8(obj):
    """
    Run flake8.
    """
    try:
        subprocess.check_call([sys.executable, '-m', 'flake8'])
        print("flake8 OK")
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            print("\nThere were flake8 errors!")


@root.command()
@click.pass_obj
def version(obj):
    """
    Print version.
    """
    import oval
    print(oval.__version__)


@root.command()
@click.pass_obj
def create(obj):
    """
    Create empty oval bundle.
    """
    with oval.core.cli_context(obj) as bundle:
        bundle.create()


@root.command()
@click.pass_obj
def info(obj):
    """
    Print bundle metadata.
    """
    with oval.core.cli_context(obj) as bundle:
        print(json.dumps(
            bundle.read_attributes(), indent=4, sort_keys=True))


@root.command()
@click.pass_obj
@click.argument('args', nargs=-1)
def set(obj, args):
    """
    Set bundle metadata attributes.
    """
    with oval.core.cli_context(obj) as bundle:
        new_metadata = dict(arg.split(':') for arg in args)
        bundle.update_metadata(new_metadata)


@root.command()
@click.pass_obj
@click.argument('args', nargs=-1)
def remove(obj, args):
    """
    Remove the specified metadata attributes.
    """
    with oval.core.cli_context(obj) as bundle:
        bundle.remove_attributes(args)


@root.command()
@click.pass_obj
def list(obj):
    """
    List chart data in the bundle.
    """
    with oval.core.cli_context(obj) as bundle:
        print(tabulate(enumerate(bundle.list_charts())))


@root.command()
@click.pass_obj
@click.option(
    '--filename', '-f', help="chart data filename")
@click.argument('args', nargs=-1)
def add_chart(obj, filename, args):
    """
    Add chart data to the bundle.
    """
    with oval.core.cli_context(obj) as bundle:
        chart_kwargs = dict(arg.split(':') for arg in args)
        bundle.add_chart(filename, **chart_kwargs)


@root.command()
@click.pass_obj
@click.option(
    '--title', '-t', help="Chart title")
@click.option(
    '--start-time', '-s', default=1.0, help="Signal start time")
@click.option(
    '--end-time', '-e', default=11.0, help="Signal end time")
@click.option(
    '--num-samples', '-n', default=1000, help="How many rows to generate")
@click.option(
    '--amplitude', '-a', default=0.5, help="Signal amplitude")
@click.option(
    '--frequency', '-f', default=4, help="Signal frequency")
@click.option(
    '--phase', '-p', default=0.0, help="Signal phase")
@click.option(
    '--y-offset', '-y', default=0.0, help="Signal phase")
@click.option(
    '--x-label', '-i', default="Time (s)", help="x axis chart label")
@click.option(
    '--y-label', '-j', default="Sample", help="y axis chart label")
def gen_chart(
        obj, title, start_time, end_time,
        num_samples, amplitude, frequency, phase, y_offset,
        x_label, y_label):
    """
    Generate sinusoidal chart data for testing.
    """
    with oval.core.cli_context(obj) as bundle:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_filename = f.name

        with open(temp_filename, 'w', newline='') as csvfile:
            inst_writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            inst_writer.writerow(['time', 'sample'])
            sample_time = start_time
            inc = (end_time - start_time)/num_samples
            while sample_time < end_time:
                yt = amplitude * math.sin(
                    2*math.pi * frequency * sample_time + phase) + y_offset
                inst_writer.writerow([sample_time, yt])
                sample_time += inc

        if title is None:
            title = os.path.basename(temp_filename)

        bundle.add_chart(
            temp_filename, title=title,
            x_label=x_label, y_label=y_label)

        os.remove(temp_filename)


@root.command()
@click.pass_obj
@click.argument('args', nargs=-1)
def remove_chart(obj, args):
    """
    Remove chart data from the bundle by indices.
    """
    with oval.core.cli_context(obj) as bundle:
        bundle.remove_charts([int(i) for i in args])
