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

import pandas as pd


logger = logging.getLogger(__name__)
LOG_FORMAT = '%(asctime)s %(levelname)-8.8s [%(name)s:%(lineno)s] %(message)s'


class BundleError(RuntimeError):
    pass


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

    yield Bundle(obj.bundle)

    if obj.profiling:
        pr.disable()
        prof = pstats.Stats(pr, stream=sys.stdout)
        ps = prof.sort_stats('cumulative')
        ps.print_stats(300)


class OvalObj(object):
    pass


class Bundle(OvalObj):
    """
    Collection of oval.bio generated chart data.
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
            "chart_data": []}
        bundle_metadata = default_metadata.copy()
        bundle_metadata.update(kwargs)

        self._set_metadata(bundle_metadata)

    def attributes(self):
        """
        Returns the attribute names of the bundle.
        """
        with zipfile.ZipFile(self._filename, mode="r") as session:
            return list(
                json.loads(session.read(self._metadata_filename)).keys())

    def read_attributes(self):
        """
        Returns entire bundle metadata.
        """
        with zipfile.ZipFile(self._filename, mode="r") as session:
            return json.loads(session.read(self._metadata_filename))

    def has_attribute(self, attribute):
        """
        Return whether the attribute exists in the bundle metadata.
        """
        return attribute in self.attributes()

    def read_attribute(self, attribute):
        """
        Returns the specified attribute from the bundle.
        """
        with zipfile.ZipFile(self._filename, mode="r") as session:
            return json.loads(
                session.read(self._metadata_filename))[attribute]

    def _get_metadata(self):
        """
        Return existing attributes
        """
        with zipfile.ZipFile(self._filename, mode="r") as session:
            return json.loads(session.read(self._metadata_filename))

    def _set_metadata(self, metadata):
        """
        Sets bundle metadata
        """
        # update timestamp
        metadata["timestamp"] = str(datetime.datetime.now())

        # write it to a temp file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_filename = f.name
        with open(temp_filename, "w") as json_file:
            json.dump(metadata, json_file)

        # then add it to the zip
        with zipfile.ZipFile(self._filename, mode="w") as session:
            session.write(temp_filename, self._metadata_filename)

        # cleanup temp file
        os.remove(temp_filename)

    def update_metadata(self, new_metadata):
        """
        Updates metadata.
        """
        metadata = self._get_metadata()
        metadata.update(new_metadata)
        self._set_metadata(metadata)

    def write_attribute(self, attribute, value):
        """
        Write attribute value to the bundle.
        """
        metadata = self._get_metadata()
        metadata[attribute] = value
        self._set_metadata(metadata)

    def remove_attribute(self, attribute):
        """
        Remove value from metadata.
        """
        metadata = self._get_metadata()
        del metadata[attribute]
        self._set_metadata(metadata)

    def num_charts(self):
        """
        Return the number of charts in the bundle.
        """
        return len(self.read_attribute("chart_data"))

    def add_chart(self, csv_filename, **kwargs):
        """
        Add csv data to the bundle.
        """
        df = pd.read_csv(csv_filename, **kwargs)

        if len(df.columns) < 2:
            raise BundleError("Not enough columns in csv")

        x_column = df.columns[0]
        y_column = df.columns[1]
        x_min = df[x_column].min()
        x_max = df[x_column].max()
        y_min = df[y_column].min()
        y_max = df[y_column].max()
        arcname = os.path.basename(csv_filename)

        default_title = os.path.basename(
            os.path.splitext(csv_filename)[0])
        chart_metadata = {
            "chart_type": "line",
            "source": "default",
            "filename": arcname,
            "mimetype": "text/csv",
            "title": default_title,
            "x_label": x_column,
            "x_min": x_min,
            "x_max": x_max,
            "y_label": y_column,
            "y_min": y_min,
            "y_max": y_max,
            "x_column": x_column,
            "y_column": y_column,
            "dataframe": kwargs}

        metadata = self._get_metadata()
        if "chart_data" not in metadata or \
           type(metadata["chart_data"]) != list:
            metadata["chart_data"] = []
        metadata["chart_data"].append(chart_metadata)
        self._set_metadata(metadata)

        with zipfile.ZipFile(self._filename, mode="w") as session:
            session.write(csv_filename, arcname=arcname)

    def remove_chart(self, index):
        """
        Removes chart at the specified index.
        """
        metadata = self._get_metadata()
        metadata["chart_data"].pop(index)
        self._set_metadata(metadata)

    def get_chart(self, index):
        """
        Returns chart at the specified index.
        """
        metadata = self._get_metadata()
        return metadata["chart_data"][index]
