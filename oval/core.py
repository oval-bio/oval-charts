import cProfile
import datetime
import json
# from email.mime.application import MIMEApplication
import logging
import mimetypes
import os
import pstats
import shutil
import smtplib
import ssl
import sys
import tempfile
import zipfile
from contextlib import contextmanager
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

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


@contextmanager
def edit_archive(zip_file):
    """
    Context to extract zip file to a temp directory,
    yielding that then re-archiving the directory contents.
    """
    with tempfile.TemporaryDirectory() as extract_dir:
        if os.path.exists(zip_file):
            try:
                with zipfile.ZipFile(zip_file, mode="r") as archive:
                    archive.extractall(extract_dir)
            except zipfile.BadZipFile:
                pass
        yield extract_dir
        with zipfile.ZipFile(zip_file, mode="w") as archive:
            for root, dirs, files in os.walk(extract_dir):
                for name in files:
                    logger.debug("archiving: {}".format(name))
                    archive.write(os.path.join(root, name), name)


def send_email(from_addr, to_addrs, subject, body, files=[], **kwargs):
    logger.debug("sending email: {} -> {} :: subject: {} :: body: {}".format(
        from_addr, to_addrs, subject, body))

    if not isinstance(to_addrs, list):
        to_addrs = [to_addrs]

    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = COMMASPACE.join(to_addrs)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    if "html_body" in kwargs:
        html_body = kwargs["html_body"]
    else:
        html_body = "<p>{}</p>".format(body)
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    for f in files:
        name, realname, mimetype = f

        if not bool(mimetype):
            ctype, encoding = mimetypes.guess_type(name)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded
                # (compressed), so use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
        else:
            maintype, subtype = mimetype.split('/', 1)

        logger.info("attachment: {} : {} : {}/{}".format(
            name, realname, maintype, subtype))

        switch = {
            "text": MIMEText,
            "image": MIMEImage,
            "audio": MIMEAudio,
        }
        if maintype in switch:
            with open(name, "rb") as fil:
                part = switch[maintype](fil.read(), _subtype=subtype)
        else:
            with open(name, "rb") as fil:
                part = MIMEBase(maintype, subtype)
                part.set_payload(fil.read())
            # Encode the payload using Base64
            encoders.encode_base64(part)
        # After the file is closed
        part.add_header('Content-Disposition', 'attachment', filename=realname)
        msg.attach(part)

    msg_str = msg.as_string()
    smtp = None
    try:
        smtp = smtplib.SMTP(kwargs["smtp_host"], kwargs["smtp_port"])
        context = ssl.create_default_context()
        smtp.starttls(context=context)
        smtp.login(kwargs["smtp_user"], kwargs["smtp_password"])
        for to_addr in to_addrs:
            log_msg = "sending email from {} to {}: {}".format(
                from_addr, to_addr, subject)
            logger.debug(log_msg)
            smtp.sendmail(from_addr, to_addr, msg_str)
    except Exception as e:
        logger.exception(str(e))
    finally:
        if smtp is not None:
            smtp.quit()


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
        with edit_archive(self._filename) as arc_dir:
            # update timestamp
            metadata["timestamp"] = str(datetime.datetime.now())

            # replace the metadata file
            with open(os.path.join(
                    arc_dir, self._metadata_filename), "w") as json_file:
                json.dump(metadata, json_file, indent=4, sort_keys=True)

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
        self.remove_attributes([attribute])

    def remove_attributes(self, attributes):
        """
        Remove values from metadata.
        """
        metadata = self._get_metadata()
        for attrib in attributes:
            del metadata[attrib]
        self._set_metadata(metadata)

    def num_charts(self):
        """
        Return the number of charts in the bundle.
        """
        return len(self.read_attribute("chart_data"))

    def add_chart(self, csv_filename, **kwargs):
        """
        Add csv data to the bundle. Keyword args are added
        to chart metadata.
        """
        # TODO: support what pandas supports
        df = pd.read_csv(csv_filename)

        if len(df.columns) < 2:
            raise BundleError("Not enough columns in csv")

        x_column = df.columns[0]
        y_column = df.columns[1]
        x_min = df[x_column].min()
        x_max = df[x_column].max()
        y_min = df[y_column].min()
        y_max = df[y_column].max()
        arcname = os.path.basename(csv_filename)

        default_title = os.path.basename(csv_filename)
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
            "y_column": y_column}
        chart_metadata.update(kwargs)

        metadata = self._get_metadata()
        if "chart_data" not in metadata or \
           type(metadata["chart_data"]) != list:
            metadata["chart_data"] = []
        metadata["chart_data"].append(chart_metadata)
        self._set_metadata(metadata)

        with edit_archive(self._filename) as arc_dir:
            shutil.copy2(csv_filename, os.path.join(arc_dir, arcname))

    def remove_chart(self, index):
        """
        Removes chart at the specified index.
        """
        metadata = self._get_metadata()
        metadata["chart_data"].pop(index)
        self._set_metadata(metadata)

    def remove_charts(self, indices):
        """
        Removes charts at the specified indices all at once.
        """
        metadata = self._get_metadata()
        metadata["chart_data"] = [
            i for j, i in enumerate(metadata["chart_data"])
            if j not in indices]
        self._set_metadata(metadata)

    def get_chart(self, index):
        """
        Returns chart at the specified index.
        """
        metadata = self._get_metadata()
        return metadata["chart_data"][index]

    def list_charts(self):
        """
        Return a list of indexes and chart titles.
        """
        metadata = self._get_metadata()
        chart_titles = []
        for chart_data in metadata["chart_data"]:
            chart_titles.append(chart_data["title"])
        return chart_titles
