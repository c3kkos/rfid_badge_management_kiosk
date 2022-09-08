#!/usr/bin/env python

import touch
import signal
import time
import sys
import os
from datetime import datetime

from pirc522 import RFID

run = True
rdr = RFID()
util = rdr.util()
util.debug = True

def end_read(signal,frame):
    global run
    print("\nCtrl+C captured, ending read.")
    run = False
    rdr.cleanup()
    sys.exit()

signal.signal(signal.SIGINT, end_read)

rfid_reader_version = "RFID Reader Loop v2.0a 01/09/2022"
touch_path = "/your_path/RFID_EVENTS/"

print("Starting "+rfid_reader_version)
while run:
    rdr.wait_for_tag()

    (error, data) = rdr.request()
    if not error:
        print("\nCard detected: " + format(data, "02x"))

    (error, uid) = rdr.anticoll()
    if not error:
        print("Card read UID: "+str(uid[0]).zfill(3)+str(uid[1]).zfill(3)+str(uid[2]).zfill(3)+str(uid[3]).zfill(3))
        id = str(uid[0]).zfill(3)+str(uid[1]).zfill(3)+str(uid[2]).zfill(3)+str(uid[3]).zfill(3)
        # dd/mm/YY H:M:S
        now = datetime.now()
        dt_string = now.strftime("%Y_%m_%d-%I:%M:%S_%p")
        print("Event file created at "+touch_path+str(id)+"_"+dt_string)
        touch.touch(touch_path+str(id)+"_"+dt_string)
        time.sleep(2)
