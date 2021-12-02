import zmq
from flask import Flask, render_template
from threading import Thread, Event
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import serial
from serial.tools import list_ports
import sys
import time
from datetime import datetime
import sqlite3
import os

template_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
if sys.platform.startswith('win'):
    template_dir = 'C:\\Users\\fureun05\\pyairmon\\templates'

print(template_dir)


HOST = '127.0.0.1'
PORT = 9090
TASK_ZMQ = zmq.Context().socket(zmq.REQ)
TASK_ZMQ.connect('tcp://{}:{}'.format(HOST, PORT))
app = Flask("app", template_folder=template_dir,
            static_url_path="/static", static_folder='C:\\Users\\fureun05\\pyairmon\\static')

db_connection = sqlite3.connect("_pyaircon.db", check_same_thread=False)


@app.route('/', methods=['GET'])
def index():
    cursor = db_connection.cursor()
    cursor.execute("select * from aircon_history order by id desc limit 10")
    rows = cursor.fetchall()
    return render_template('index.html', rows=rows)

@app.route("/aircon_on")
def aircon_on():
    TASK_ZMQ.send_json({"command": "on"})
    results = TASK_ZMQ.recv_json()
    return f'{results}'

@app.route('/aircon_off')
def aircon_off():
    TASK_ZMQ.send_json({"command": "off"})
    results = TASK_ZMQ.recv_json()
    return f'{results}'


class Worker(Thread):
    def __init__(self):
        Thread.__init__(self)
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.REP)
        self.active = True

        self.db_conn = sqlite3.connect('_pyaircon.db', check_same_thread=False)
        self.db_conn.execute("""CREATE TABLE IF NOT EXISTS aircon_history(id INTEGER PRIMARY KEY autoincrement, command TEXT, reg_date datetime DEFAULT (datetime('now','localtime')))""")

        self.device = None
        self.ir_device_open()

        self.scheducler = BackgroundScheduler(timezone='Asia/Seoul', misfire_grace_time=300, coalesce=True)
        self.scheducler.add_job(self.send_aircon_control, 'cron', kwargs={'command':'on'}, day_of_week='mon-fri', hour=6, minute=0)
        self.scheducler.add_job(self.send_aircon_control, 'cron', kwargs={'command':'off'}, day_of_week='mon-fri', hour=17, minute=0)
        self.scheducler.start()

    def ir_device_open(self):
        try:
            os_type = sys.platform
            if os_type == 'darwin':
                com_ports = [ p for p in list_ports.comports() if 'usbserial' in p.device ]
                com_ports.sort(key=lambda x: x.device, reverse=False)
            else:
                com_ports = [ p for p in list_ports.comports() if 'USB-SERIAL' in p.description ]
                com_ports.sort(key=lambda x: x.device, reverse=False)

            if com_ports:
                self.device = serial.Serial(
                    port=com_ports[0].device,
                    baudrate=115200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=0.5
                )
                self.reader = SerialDeviceReader(self.device)
                self.reader.start()

        except Exception as ex:
            print(f'{ex}')


        print(self.device)


    def _ir_on(self):
        try:
            if not self.device:
                print('device does not exist')
            # self.s.write([0x44, 0x47, 0x65, 0x74, 0x49, 0x44, 0x5f, 0x5f, 0x5f, 0x40])
            self.device.write([0x49, 0x73, 0x65, 0x6e, 0x64, 0x49, 0x52, 0x5f, 0x5f, 0x4e])

            time.sleep(1)
            cmd_data = [ 0x32, 0x36, 0x20, 0x30, 0x32, 0x34, 0x34, 0x20, 0x34, 0x35, 0x41, 0x30, 0x20, 0x30, 0x42, 0x41
                , 0x41, 0x20, 0x32, 0x32, 0x46, 0x41, 0x20, 0x30, 0x31, 0x46, 0x34, 0x20, 0x30, 0x31, 0x46, 0x32
                , 0x20, 0x30, 0x31, 0x46, 0x32, 0x20, 0x30, 0x35, 0x44, 0x36, 0x20, 0x30, 0x31, 0x46, 0x38, 0x20
                , 0x30, 0x42, 0x42, 0x30, 0x20, 0x30, 0x31, 0x20, 0x32, 0x33, 0x20, 0x46, 0x32, 0x20, 0x37, 0x33
                , 0x20, 0x32, 0x32, 0x20, 0x33, 0x32, 0x20, 0x32, 0x46, 0x20, 0x33, 0x35, 0x20, 0x46, 0x32, 0x20
                , 0x45, 0x46, 0x20, 0x32, 0x45, 0x20, 0x46, 0x32, 0x20, 0x34, 0x46, 0x20, 0x33, 0x34, 0x20, 0x34
                , 0x31, 0x20, 0x33, 0x46, 0x20, 0x32, 0x38, 0x20, 0x33, 0x32, 0x20, 0x32, 0x33, 0x20, 0x32, 0x46
                , 0x20, 0x33, 0x36, 0x20, 0x46, 0x32, 0x20, 0x45, 0x46, 0x20, 0x32, 0x45, 0x20, 0x46, 0x32, 0x20
                , 0x38, 0x34, 0x20, 0x31, 0x33, 0x20, 0x46, 0x32, 0x20, 0x38, 0x33, 0x20, 0x32, 0x32, 0x20, 0x33
                , 0x32, 0x20, 0x33, 0x33, 0x20, 0x32, 0x46, 0x20, 0x33, 0x38, 0x20, 0x32, 0x32, 0x20, 0x32, 0x33
                , 0x20, 0x33, 0x33, 0x20, 0x46, 0x32, 0x20, 0x38, 0x33, 0x20, 0x33, 0x32, 0x20, 0x33, 0x33, 0x20
                , 0x46, 0x32, 0x20, 0x38, 0x46, 0x20, 0x33, 0x34, 0x20, 0x32, 0x46, 0x20, 0x46, 0x46, 0x20]
            self.device.write(cmd_data)
            time.sleep(2)

            print(f'send_ir_on end.')
            self.db_conn.execute("""INSERT INTO aircon_history(command) values('{}')""".format("ON"))
            self.db_conn.commit()
        except Exception as ex:
            print(f'{ex}')


    def _ir_off(self):
        try:
            if not self.device:
                print('device does not exist')

            self.device.write([0x49,0x73,0x65,0x6e,0x64,0x49,0x52,0x5f,0x5f,0x4e])
            time.sleep(1)
            cmd_data = [
                0x32,0x36,0x20,0x30,0x32,0x34,0x34,0x20,0x34,0x35,0x42,0x38,0x20,0x30,0x42,0x41
                ,0x41,0x20,0x32,0x32,0x46,0x41,0x20,0x30,0x31,0x46,0x38,0x20,0x30,0x31,0x46,0x36
                ,0x20,0x30,0x31,0x46,0x32,0x20,0x30,0x35,0x44,0x36,0x20,0x30,0x31,0x45,0x45,0x20
                ,0x30,0x42,0x42,0x41,0x20,0x30,0x31,0x20,0x32,0x33,0x20,0x46,0x32,0x20,0x37,0x33
                ,0x20,0x32,0x32,0x20,0x33,0x33,0x20,0x32,0x46,0x20,0x33,0x35,0x20,0x46,0x32,0x20
                ,0x45,0x46,0x20,0x32,0x45,0x20,0x46,0x32,0x20,0x36,0x33,0x20,0x33,0x34,0x20,0x31
                ,0x33,0x20,0x46,0x32,0x20,0x38,0x33,0x20,0x32,0x32,0x20,0x33,0x32,0x20,0x46,0x33
                ,0x20,0x36,0x46,0x20,0x32,0x45,0x20,0x46,0x32,0x20,0x45,0x46,0x20,0x32,0x38,0x20
                ,0x34,0x31,0x20,0x33,0x46,0x20,0x32,0x38,0x20,0x33,0x32,0x20,0x32,0x32,0x20,0x33
                ,0x33,0x20,0x33,0x32,0x20,0x46,0x33,0x20,0x35,0x32,0x20,0x33,0x33,0x20,0x32,0x32
                ,0x20,0x32,0x33,0x20,0x33,0x33,0x20,0x46,0x32,0x20,0x38,0x46,0x20,0x33,0x35,0x20
                ,0x32,0x32,0x20,0x33,0x46,0x20,0x32,0x37,0x20,0x33,0x33,0x20,0x32,0x46,0x20,0x46
                ,0x46,0x20]

            self.device.write(cmd_data)
            time.sleep(2)

            print(f'{datetime.now()} send_ir_off end.')
            self.db_conn.execute("""INSERT INTO aircon_history(command) values('{}')""".format("OFF"))
            self.db_conn.commit()
        except Exception as ex:
            print(f'{ex}')

    def send_aircon_control(self, command):
        r = requests.get('http://127.0.0.1:9000/aircon_' + command)
        print(f'send_aircon_control {r}')


    def run(self):
        self._socket.bind("tcp://{}:{}".format(HOST, PORT))
        self._socket.setsockopt(zmq.RCVTIMEO, 500)
        while self.active:
            ev = self._socket.poll(1000)
            if ev:
                data = self._socket.recv_json()
                if data['command'] == 'on':
                    self._ir_on()
                else:
                    self._ir_off()

                self._socket.send_json({"response": "ok", "payload": data})

        self.reader.stopped.set()
        self.device.close()
        self.db_conn.close()

class SerialDeviceReader(Thread):

    def __init__(self, s):
        Thread.__init__(self)
        self.stopped = Event()
        self.s = s

        print('SerialDeviceReader init.')
        # self.context = zmq.Context()
        # self.sender = self.context.socket(zmq.PUSH)
        # self.sender.connect('tcp://127.0.0.1:50011')

    def run(self):
        buf = bytearray()
        while not self.stopped.is_set() and self.s.isOpen():
            try:
                if self.s.in_waiting > 0:
                    read_buf = self.s.read(self.s.in_waiting)
                    buf.extend(read_buf)
                    print(f'{buf}')
                else:
                    buf.clear()
                    time.sleep(0.001)

            except Exception as ex:
                print(ex)
                continue

if __name__ == '__main__':
    worker = Worker()
    worker.start()
    app.run(host='192.168.10.55', port=5009)