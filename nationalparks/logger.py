#!/usr/bin/env python
"""
module with functions to enable logging
"""

import time
from time import strftime 
import os
import re
import csv
import sys
import uuid
from datetime import date, datetime
import pandas as pd


## create path for logs if needed
if not os.path.exists(os.path.join("..","logs")):
    os.mkdir(os.path.join("..","logs"))

def update_parks_database(headers, park_count):
    """
    Update park database log.
    """
    ## define cyclic name for log
    today = date.today()
    logfile = os.path.join("..", "logs", "update_park_data-{}-{}.log".format(today.year, today.month))

    ## write the data to csv file
    header = [
        "unique_id", "timestamp", "park_count", "headers"
    ]

    ## determine if header needs to be written
    write_header = False
    if not os.path.exists(logfile):
        write_header = True
    
    ## update log
    with open(logfile, 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        if write_header:
            writer.writerow(header)
        to_write = map(str,[
            uuid.uuid4(),
            strftime("%Y_%m_%_d_%H_%M_%S"),
            headers, park_count])
        writer.writerow(to_write)