import cProfile
import logging
import os
import pstats
import subprocess
import sys
import unittest

import click

import oval.core


logger = logging.getLogger(__name__)


@click.group(context_settings={"help_option_names": ['-h', '--help']})
@click.option(
    "--log", envvar="OVAL_LOG", default="-",
    help="Log file. Use '-' for stdout")
@click.option(
    "--log-level", default="WARNING",
    help="Log output level")
@click.option(
    '--profiling/--no-profiling', default=False,
    help="Print profiling info on exit")
@click.option(
    "--bundle", default="session.zip",
    help="oval.bio session data bundle")
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
    Run test suite
    """
    if obj.profiling:
        logger.info("enabling profiling")
        pr = cProfile.Profile()
        pr.enable()

    loader = unittest.TestLoader()
    suite = loader.discover(
        os.path.abspath(os.path.dirname(__file__)),
        pattern=pattern)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

    if obj.profiling:
        pr.disable()
        prof = pstats.Stats(pr, stream=sys.stdout)
        ps = prof.sort_stats('cumulative')
        ps.print_stats(300)


@root.command()
@click.pass_obj
def flake8(obj):
    """
    Run flake8
    """
    try:
        subprocess.check_call([sys.executable, '-m', 'flake8'])
        print("flake8 OK")
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            print("\nThere were flake8 errors!")
