import csv
import datetime
import math
import json
import time
import uuid
import zipfile


OUTFILE_CSVS = {
    "inst0.csv": {
        "start_time": 1.0,
        "end_time": 11.0,
        "num_samples": 100,
        "amplitude": 0.5,
        "freq": 4,
        "phase": 0.0,
        "y_offset": 0.0},
    "inst1.csv": {
        "start_time": 1.0,
        "end_time": 11.0,
        "num_samples": 100,
        "amplitude": 0.5,
        "freq": 4,
        "phase": 0.0,
        "y_offset": 0.0}}


OUTFILE_JSON = "metadata.json"
OUTFILE_ZIP = "Session_{}.zip".format(uuid.uuid1())


def gen_chart(
        filename, start_time=1.0, end_time=11.0, num_samples=100,
        amplitude=0.5, freq=4, phase=0.0, y_offset=0):
    """
    Generate sinusoid.
    """
    with open(filename, 'w', newline='') as csvfile:
        inst_writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        inst_writer.writerow(['time', 'sample'])
        sample_time = start_time
        inc = (end_time - start_time)/num_samples
        while sample_time < end_time:
            yt =  amplitude * math.sin(
                2*math.pi * freq * sample_time + phase) + y_offset
            inst_writer.writerow([sample_time, yt])
            sample_time += inc

    return {
        "chart_type": "line",
        "source": "default",
        "filename": filename,
        "title": "Test Data",
        "x_label": "Time (s)",
        "x_min": start_time,
        "x_max": end_time,
        "y_label": "Amplitude",
        "y_min": -amplitude,
        "y_max": amplitude,
        "x_column": "time",
        "y_column": "sample"}


metadata = {
    "vendor": "oval.bio",
    "version": "1.0.0",
    "timestamp": str(datetime.datetime.now()),
    "first_name": "Test",
    "last_name": "Client",
    "email": "test@example.com",
    "gender": "Male",
    "birthdate": "1/1/1970",
    "weight": 180.0,
    "chart_data": []}


with zipfile.ZipFile(OUTFILE_ZIP, mode="w") as session:
    for csv_filename, kwargs in OUTFILE_CSVS.items():
        meta = gen_chart(csv_filename, **kwargs)
        metadata["chart_data"].append(meta)
        session.write(csv_filename)

    with open(OUTFILE_JSON, "w") as json_file:
        json.dump(metadata, json_file)
    session.write(OUTFILE_JSON)
