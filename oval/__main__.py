import csv
import json
import logging
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid

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
        metadata = bundle.read_attributes()
        num_charts = len(metadata["chart_data"])
        del metadata["chart_data"]
        metadata["num_charts"] = num_charts
        print(tabulate(metadata.items()))


@root.command()
@click.pass_obj
@click.option(
    '--key', '-k', multiple=True, help="Key corresponding to value argument")
@click.option(
    '--value', '-v', multiple=True, help="Value corresponding to key argument")
def set(obj, key, value):
    """
    Set bundle metadata attributes.
    """
    with oval.core.cli_context(obj) as bundle:
        bundle.update_metadata(dict(zip(key, value)))


@root.command()
@click.pass_obj
@click.argument('filename')
def set_text(obj, filename):
    """
    Set bundle text that shows up on published reports. Copies the file
    specified into the bundle and points metadata to it.
    """
    arcname = os.path.basename(filename)
    with oval.core.edit_archive(obj.bundle) as arc_dir:
        shutil.copy2(filename, os.path.join(arc_dir, arcname))
    with oval.core.cli_context(obj) as bundle:
        bundle.write_attribute("text", arcname)


@root.command()
@click.pass_obj
@click.option(
    '--filename', '-f', help="File containing html to use for the bundle.")
def set_html(obj, filename):
    """
    Set bundle html that shows up on published reports.
    """
    arcname = os.path.basename(filename)
    with oval.core.edit_archive(obj.bundle) as arc_dir:
        shutil.copy2(filename, os.path.join(arc_dir, arcname))
    with oval.core.cli_context(obj) as bundle:
        bundle.write_attribute("html", arcname)


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
@click.option(
    '--remove-zero/--no-remove-zero',
    '-r', help="Don't add rows with zero value in y_column", default=False)
@click.option(
    '--stroke', '-s', multiple=True,
    help="brush stroke to use for chart line", default=["steelblue"])
@click.option(
    '--stroke-width', '-w', multiple=True,
    help="brush stroke to use for chart line", default=[1.5])
@click.argument('x_column')
@click.argument('y_column', nargs=-1)
def add_chart(
        obj, filename, remove_zero, stroke, stroke_width, x_column, y_column):
    """
    Add chart data to the bundle. If multiple y_columns are specified,
    then multiple charts will be added.
    """
    with oval.core.cli_context(obj) as bundle:
        for i, y_col in enumerate(y_column):
            if i < len(stroke):
                st = stroke[i]
            else:
                st = stroke[-1]
            if i < len(stroke_width):
                st_w = stroke_width[i]
            else:
                st_w = stroke_width[-1]
            chart_kwargs = {
                "remove_zero": remove_zero,
                "x_column": x_column,
                "y_column": y_col,
                "stroke": st,
                "stroke_width": st_w}
            bundle.add_chart(filename, **chart_kwargs)


@root.command()
@click.pass_obj
@click.argument('index')
@click.argument('args', nargs=-1)
def edit_chart(obj, index, args):
    """
    Edit chart at index INDEX to include the specified key/value pairs, where
    key value pairs are alternating arguments, e.g. KEY VALUE KEY VALUE...
    """
    with oval.core.cli_context(obj) as bundle:
        key = args[::2]
        value = args[1::2]
        chart_kwargs = dict(zip(key, value))
        bundle.edit_chart(int(index), **chart_kwargs)


@root.command()
@click.pass_obj
@click.argument('index')
@click.argument('filename')
def copy_chart(obj, index, filename):
    """
    Copy chart at INDEX to FILENAME with TITLE.
    """
    with oval.core.cli_context(obj) as bundle:
        bundle.copy_chart(int(index), filename)


@root.command()
@click.pass_obj
@click.argument('index')
@click.argument('column', nargs=-1)
@click.option(
    '--range-min', '-i', help="Range minimum", default=0)
@click.option(
    '--range-max', '-j', help="Range maximum", default=1)
def rescale_chart_data(obj, index, column, range_min, range_max):
    """
    Rescales the COLUMNs of chart INDEX to be between
    RANGE_MIN and RANGE_MAX.
    """
    with oval.core.cli_context(obj) as bundle:
        bundle.rescale_chart_data(
            int(index), *column, feature_range=(range_min, range_max))


@root.command()
@click.pass_obj
@click.argument('index')
def chart_data_columns(obj, index):
    """
    Return chart data column names.
    """
    with oval.core.cli_context(obj) as bundle:
        print(tabulate(enumerate(bundle.chart_data_columns(int(index)))))


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


@root.command()
@click.pass_obj
@click.argument('idx', nargs=1)
def chart_info(obj, idx):
    """
    Print chart information.
    """
    with oval.core.cli_context(obj) as bundle:
        print(tabulate(bundle.get_chart(int(idx)).items()))


@root.command()
@click.pass_obj
@click.option(
    '--from-addr', '-f', help="From email address.")
@click.option(
    '--to-addr', '-t', help="To email address.")
@click.option(
    '--smtp-host', '-s', help="SMTP host")
@click.option(
    '--smtp-port', '-p', help="SMTP port")
@click.option(
    '--smtp-user', '-u', help="SMTP user")
@click.option(
    '--smtp-password', '-p', help="SMTP password")
@click.option(
    '--title', '-t', help="Post title", default=None)
def publish(
        obj, from_addr, to_addr, smtp_host, smtp_port,
        smtp_user, smtp_password, title):
    """
    Publish the bundle by email.
    """
    with oval.core.cli_context(obj) as bundle:
        metadata = bundle.read_attributes()

        text = ""
        html = None
        uuid_str = None
        if "text" in metadata:
            text = bundle.read_file(metadata["text"]).decode()
        if "html" in metadata:
            html = bundle.read_file(metadata["html"]).decode()
        if "uuid" in metadata:
            uuid_str = metadata["uuid"]
        else:
            logger.warning("missing metadata uuid")
            uuid_str = str(uuid.uuid1())

        if title is None:
            title = uuid_str

        kwargs = {
            "smtp_host": smtp_host,
            "smtp_port": int(smtp_port),
            "smtp_user": smtp_user,
            "smtp_password": smtp_password}

        if html is not None:
            kwargs["html_body"] = html

        files = [(obj.bundle, os.path.basename(obj.bundle), None)]
        logger.info("Publishing '{}' to {}".format(title, to_addr))
        oval.core.send_email(
            from_addr, to_addr, title, text, files=files, **kwargs)
