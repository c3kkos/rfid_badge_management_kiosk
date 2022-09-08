import os
import platform
import sys
import xmlrpc.client
from time import strftime, localtime, sleep

import apsw
import psutil
from PySide2 import QtCore, QtGui
from PySide2.QtCore import QTimer, QObject, Signal
from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

title = "*RFID Badge* - attendance system terminal"
version = "Version 0.7a - 25/08/2022"

# Odoo Data

odooIP = "your_ip"  # docker odoo ip on this pc
odooDATA = "your_db"
odooUSER = "your_user"
odooPASS = "your_password"
odooPORT = "8069"
odooURL = "http://" + odooIP

# timers intervals
trigger_clock = 500
trigger_odooping = 60000
trigger_odooauth = 240000
trigger_rfid_process = 40000

# rfid parameters

rfid_watchdog_path = "/opt/RFID_EVENTS/"

# apsw - Sqlite3 db path and file name.

apsw_db_file = "/your_path/db.db"

# initialize Sqlite DB

db = apsw.Connection(apsw_db_file)
cursor = db.cursor()


class Odoo():
    def __init__(self):
        self.DATA = odooDATA  # db name
        self.USER = odooUSER  # email address
        self.PASS = odooPASS  # password
        self.PORT = odooPORT  # port
        self.URL = odooURL  # base url
        self.URL_COMMON = "{}:{}/xmlrpc/2/common".format(
            self.URL, self.PORT)
        self.URL_OBJECT = "{}:{}/xmlrpc/2/object".format(
            self.URL, self.PORT)

    def authenticateOdoo(self):
        self.ODOO_COMMON = xmlrpc.client.ServerProxy(self.URL_COMMON)
        self.ODOO_OBJECT = xmlrpc.client.ServerProxy(self.URL_OBJECT)
        self.UID = self.ODOO_COMMON.authenticate(
            self.DATA
            , self.USER
            , self.PASS
            , {})

    def trigger_attendance_byRFIDCard(self, rfid_code):
        result = self.ODOO_OBJECT.execute_kw(
            self.DATA
            , self.UID
            , self.PASS
            , 'hr.employee'
            , 'register_attendance'
            , [[rfid_code]])
        return result


class clock(QObject):
    timetick = Signal(str)

    def __init__(self):
        super().__init__()

        # Define timer.
        self.timer = QTimer()
        self.timer.setInterval(trigger_clock)  # msecs 100 = 1/10th sec
        self.timer.timeout.connect(self.update_time)
        self.timer.start()

    def update_time(self):
        # Pass the current time to QML.
        curr_time = strftime("%H:%M:%S", localtime())
        self.timetick.emit(curr_time)


class OdooMachinePINGCheck(QObject):
    isOdooUp = Signal(bool)

    def __init__(self):
        super().__init__()

        # Define timer.
        self.timer = QTimer()
        self.timer.setInterval(trigger_odooping)  # msecs 100 = 1/10th sec
        self.timer.timeout.connect(self.pingThatServer)
        self.timer.start()

    def pingThatServer(self):
        current_os = platform.system().lower()
        status = ""
        if current_os == "windows":
            parameter = "-n"
        else:
            parameter = "-c"
        ip = odooIP
        exit_code = os.system(f"ping {parameter} 1 -w2 {ip} > /dev/null 2>&1")
        if exit_code:
            status = False
        else:
            status = True
        self.isOdooUp.emit(status)


class OdooAuthCheck(QObject):
    isOdooAuth = Signal(bool)

    def __init__(self):
        super().__init__()

        # Define timer.
        self.timer = QTimer()
        self.timer.setInterval(trigger_odooauth)  # msecs 100 = 1/10th sec
        self.timer.timeout.connect(self.tryOdooAuth)
        self.timer.start()

    def tryOdooAuth(self):
        od = Odoo()
        status = True
        try:
            od.authenticateOdoo()
            print("Authenticating")
        except:
            print("Login FAILED")
            status = False

        self.isOdooAuth.emit(status)


class RfidProcessCheck(QObject):
    isRfidReaderRunning = Signal(bool)

    def __init__(self):
        super().__init__()

        # Define timer.
        self.timer = QTimer()
        self.timer.setInterval(trigger_rfid_process)  # msecs 100 = 1/10th sec
        self.timer.timeout.connect(self.checkIfProcessRunning)
        self.timer.start()

    def checkIfProcessRunning(self):
        status = False
        for proc in psutil.pids():
            try:
                if ("rfid").lower() in psutil.Process(proc).cmdline()[1].lower():
                    print("Rfid reader process FOUND - returning true!")
                    print(psutil.Process(proc).cmdline()[1])
                    status = True
                    self.isRfidReaderRunning.emit(status)
                    return status
            except:
                pass
        print("no rfid process detected - return FALSE")
        self.isRfidReaderRunning.emit(status)
        return status


# watchdog classes to handle the rfid hardware loop

class Bridge(QObject):
    created = Signal(FileSystemEvent)


class Handler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.bridge = Bridge()

    def on_created(self, event):
        self.bridge.created.emit(event)


class rfidCheck(QObject):
    rfidCheckResult = Signal(bool)
    rfidAction = Signal(str)
    rfidCardID = Signal(str)
    rfidDate = Signal(str)
    rfidReset = Signal(bool)
    
    def __init__(self):
        
        # Define timer that start after a login and stops with reset method invoked
        self.reset_timer = QTimer()
        self.reset_timer.setInterval(2000)  # msecs 100 = 1/10th sec
        self.reset_timer.timeout.connect(self.resetRfidArea)
        #self.timer.start()
        
        super().__init__()
        self.handler = Handler()
        self.handler.bridge.created.connect(self.handle_created)

        self.observer = Observer()
        self.observer.schedule(self.handler, rfid_watchdog_path, recursive=True)
        self.observer.start()
    
    def handle_created(self, event):
        status = False
        # STEP 0 = check for invalid filename

        if len(str(event.src_path)) != 52:
            status = False
            return status

            #print("handle_created triggered")
            # print(f"created {event.src_path}")
            # print(event.event_type)

        # STEP 1 extract ID card string from event

        sampled = str(event.src_path)[17:]
        card_id = sampled[:12]
        event_date = sampled[13:] #dt_string = now.strftime("%Y_%m_%d-%I:%M:%S_%p")
        print("Card ID: " + card_id)
        print("Event Date : " + event_date)
        
        # STEP 2 trigger Odoo attendance method
        
        od = Odoo()
        data = False
                
        try:
            od.authenticateOdoo()
            print("Odoo Auth OK")
            data = (od.trigger_attendance_byRFIDCard(card_id))
            print(data)
        except:
            #If Odoo upload fails, we rename the event file and update sqlite db
            print("Odoo Event upload FAILED")
            os.rename(str(event.src_path),(str(event.src_path)+"_UPLOAD_FAIL"))
            sql="INSERT INTO attendance (card, date, uploaded) VALUES(?,?,?)"
            cursor.execute(sql, (card_id, event_date, 0))
            status = False
            self.rfidCheckResult.emit(status)
            self.rfidAction.emit("ODOO ERROR")
            self.rfidCardID.emit(card_id)
            self.rfidDate.emit(event_date)
            self.reset_timer.start()    
            return status
        
        # STEP 3 If we are HERE Odoo upload is successful, but the login could have failed. Do Data Checks
                
        if str(data.get("error_message"))=="": # odoo login successfull
            action = data.get("action")
            print("The employee with card id "+card_id+" has registered this action: "+action)
            print("Uploading succesful login to sqlite db and renaming file")
            os.rename(str(event.src_path),(str(event.src_path)+"_OK"))
            sql="INSERT INTO attendance (card, date, uploaded) VALUES(?,?,?)"
            cursor.execute(sql, (card_id, event_date, 1))
            status = True
            self.rfidCheckResult.emit(status)
            self.rfidAction.emit(action)
            self.rfidCardID.emit(card_id)
            self.rfidDate.emit(event_date)
            self.reset_timer.start()    
            return status
            
        else: # invalid card ID
            error = data.get("error_message")
            action = data.get("action")
            print("CARD ID NOT VALID - LOGIN FAILED - "+error)
            os.rename(str(event.src_path),(str(event.src_path)+"_LOGIN_FAIL"))
            # NOT registering to sqlite the invalid logins
            status = False
            self.rfidCheckResult.emit(status)
            self.rfidAction.emit("CARD ERROR")
            self.rfidCardID.emit("* * *")
            self.rfidDate.emit(event_date)
            self.reset_timer.start()    
            return status
    
    def resetRfidArea(self):
        self.reset_timer.stop()
        self.rfidAction.emit("WAITING CARD")
        self.rfidCardID.emit("- - -")
        self.rfidDate.emit("- - -")
        self.rfidReset.emit(True)
        return


# end of classes

# start main methods and process

app = QGuiApplication(sys.argv)

engine = QQmlApplicationEngine()
engine.quit.connect(app.quit)
engine.load('main.qml')

# Define our backend object, which we pass to QML

running_clock = clock()
odoopingcheck = OdooMachinePINGCheck()
odooauthcheck = OdooAuthCheck()
rfidCheck = rfidCheck()
rfid_process_check = RfidProcessCheck()

engine.rootObjects()[0].setProperty('title', title)
engine.rootObjects()[0].setProperty('version', version)

engine.rootObjects()[0].setProperty('running_clock', running_clock)
engine.rootObjects()[0].setProperty('odoopingcheck', odoopingcheck)
engine.rootObjects()[0].setProperty('odooauthcheck', odooauthcheck)
engine.rootObjects()[0].setProperty('rfid_process_check', rfid_process_check)
engine.rootObjects()[0].setProperty('rfidCheck', rfidCheck)

# Initial call to trigger first update. Must be after the setProperty to connect signals.

running_clock.update_time()
odoopingcheck.pingThatServer()
odooauthcheck.tryOdooAuth()
rfid_process_check.checkIfProcessRunning()

sys.exit(app.exec_())
