import cProfile
import datetime
import json
import logging
import os
import pstats
import sys
import tempfile
import zipfile
from contextlib import contextmanager

import oval


logger = logging.getLogger(__name__)
LOG_FORMAT = '%(asctime)s %(levelname)-8.8s [%(name)s:%(lineno)s] %(message)s'


def setup_logging(
        log="-", log_level=logging.DEBUG, log_format=LOG_FORMAT):
    """
    Initialize logging for the app.
    """
    root = logging.getLogger()
    formatter = logging.Formatter(log_format)

    if log == "-":
        sh = logging.StreamHandler()
        sh.setLevel(log_level)
        sh.setFormatter(formatter)
        root.addHandler(sh)
    elif log:
        fh = logging.FileHandler(filename=log, mode='w')
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        root.addHandler(fh)

    root.setLevel(logging.DEBUG)


@contextmanager
def cli_context(obj):
    """
    Context manager for CLI options.
    """
    if obj.profiling:
        logger.info("enabling profiling")
        pr = cProfile.Profile()
        pr.enable()

    yield obj.bundle

    if obj.profiling:
        pr.disable()
        prof = pstats.Stats(pr, stream=sys.stdout)
        ps = prof.sort_stats('cumulative')
        ps.print_stats(300)


class OvalObj(object):
    pass


class Bundle(OvalObj):
    """
    Collection of oval.bio generated data.
    """
    def __init__(self, bundle_filename):
        self._filename = bundle_filename
        self._metadata_filename = "metadata.json"

    def create(self, **kwargs):
        """
        Creates an empty oval.bio session data bundle.
        Adds kwargs to metadata.
        """
        # set up metadata
        default_metadata = {
            "vendor": "oval.bio",
            "version": oval.__version__,
            "create_time": str(datetime.datetime.now()),
            "timestamp": str(datetime.datetime.now()),
            "chart_data": []}
        bundle_metadata = default_metadata.copy()
        bundle_metadata.update(kwargs)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_filename = f.name

        logger.debug("Creating bundle: {}".format(self._filename))

        with zipfile.ZipFile(self._filename, mode="w") as session:
            with open(temp_filename, "w") as json_file:
                json.dump(bundle_metadata, json_file)
            session.write(temp_filename, arcname=self._metadata_filename)

        os.remove(temp_filename)

    def attributes(self):
        """
        Returns the attribute names of the bundle.
        """
        with zipfile.ZipFile(self._filename, mode="r") as session:
            return list(
                json.loads(session.read(self._metadata_filename)).keys())

    def read_attribute(self, attribute):
        """
        Returns the specified attribute from the bundle.
        """
        with zipfile.ZipFile(self._filename, mode="r") as session:
            return json.loads(
                session.read(self._metadata_filename))[attribute]

    def write_attribute(self, attribute, value):
        """
        Write attribute value to the bundle.
        """
        # read existing attributes
        with zipfile.ZipFile(self._filename, mode="r") as session:
            metadata = json.loads(session.read(self._metadata_filename))

        # update the attributes
        metadata.update({attribute: value})

        # write it to a temp file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_filename = f.name
        with open(temp_filename, "w") as json_file:
            json.dump(metadata, json_file)

        # then add it to the zip
        with zipfile.ZipFile(self._filename, mode="w") as session:
            session.write(temp_filename, self._metadata_filename)

        os.remove(temp_filename)

    def remove_attribute(self, attribute):
        """
        Remove value from metadata.
        """
        # read existing attributes
        with zipfile.ZipFile(self._filename, mode="r") as session:
            metadata = json.loads(session.read(self._metadata_filename))

        # update the attributes
        del metadata[attribute]

        # write it to a temp file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_filename = f.name
        with open(temp_filename, "w") as json_file:
            json.dump(metadata, json_file)

        # then add it to the zip
        with zipfile.ZipFile(self._filename, mode="w") as session:
            session.write(temp_filename, self._metadata_filename)

        os.remove(temp_filename)
