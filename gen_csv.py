import csv
import math
import json
import time
import uuid
import zipfile


OUTFILE_CSV = "instrument.csv"
OUTFILE_JSON = "metadata.json"
OUTFILE_ZIP = "Session_{}.zip".format(uuid.uuid1())
SAMPLES = 100
SAMPLE_TIME_INCR = 0.25


with open(OUTFILE_CSV, 'w', newline='') as csvfile:
    inst_writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
    inst_writer.writerow(['time', 'sample'])
    sample_time = 0.0
    for i in range(SAMPLES):
        samp = i/(SAMPLES-1)
        inst_writer.writerow([sample_time, math.sin(samp * 2*math.pi)])
        sample_time = sample_time + SAMPLE_TIME_INCR

metadata = {
    "timestamp": time.time(),
    "first_name": "Test",
    "last_name": "Client",
    "email": "test@example.com",
    "gender": "Male",
    "birthdate": "1/1/1970",
    "weight": 180.0}
with open(OUTFILE_JSON, "w") as json_file:
    json.dump(metadata, json_file)


with zipfile.ZipFile(OUTFILE_ZIP, mode="w") as session:
    session.write(OUTFILE_CSV)
    session.write(OUTFILE_JSON)
