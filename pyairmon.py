import sys
import time
from datetime import datetime
import serial
from serial.tools import list_ports
from threading import Thread, Event
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s [%(module)s -> %(funcName)s] - %(message)s')
os_type = sys.platform
if os_type == 'darwin':
    handler = TimedRotatingFileHandler('logs/log.txt', when='midnight')
else:
    handler = TimedRotatingFileHandler('c:\\log.txt', when='midnight')

handler.suffix = '%Y%m%d'
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class AirconIrController():

    def __init__(self):
        self.s = None
        self.stopped = Event()

        # self.context = zmq.Context()
        # self.receiver = self.context.socket(zmq.SUB)
        # self.receiver.bind("tcp://127.0.0.1:50010")
        # self.receiver.subscribe("")

        self.reader = None

        self.scheducler = BackgroundScheduler(timezone='Asia/Seoul', misfire_grace_time=300, coalesce=True)
        self.scheducler.add_job(self.send_ir_on, 'cron', day_of_week='mon-fri', hour=7, minute=00)
        self.scheducler.add_job(self.send_ir_off, 'cron', day_of_week='mon-fri', hour=17, minute=0)
        self.scheducler.start()

        logger.info(f'service start.')
        print(f'{datetime.now()} service start.')


    def ir_open(self):
        com_ports = []
        os_type = sys.platform
        if os_type == 'darwin':
            com_ports = [ p for p in list_ports.comports() if 'usbserial' in p.device ]
            com_ports.sort(key=lambda x: x.device, reverse=False)
        else:
            com_ports = [ p for p in list_ports.comports() if 'USB-SERIAL' in p.description ]
            com_ports.sort(key=lambda x: x.device, reverse=False)

        if com_ports:
            self.s = serial.Serial(
                port=com_ports[0].device,
                baudrate=115200,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=0.5
            )
            logger.debug(f'{self.s}')
            self.reader = SerialDeviceReader(self.s)
            self.reader.start()

            time.sleep(3)


    def shutdown(self):
        try:
            self.reader.shutdown()
            self.scheducler.shutdown()
        except:
            pass


    def send_ir_on(self):
        try:
            self.ir_open()

            if not self.s:
                logger.debug('No serial device.')
                return
            # self.s.write([0x44, 0x47, 0x65, 0x74, 0x49, 0x44, 0x5f, 0x5f, 0x5f, 0x40])
            self.s.write([0x49, 0x73, 0x65, 0x6e, 0x64, 0x49, 0x52, 0x5f, 0x5f, 0x4e])

            time.sleep(2)
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
            self.s.write(cmd_data)
            time.sleep(5)

            self.reader.shutdown()
            logger.info(f'send_ir_on end.')
            print(f'{datetime.now()} send_ir_on end.')
        except Exception as ex:
            logger.error(f'{ex}')


    def send_ir_off(self):
        try:
            self.ir_open()
            if not self.s:
                logger.debug('No serial device.')
                return

            self.s.write([0x49,0x73,0x65,0x6e,0x64,0x49,0x52,0x5f,0x5f,0x4e])
            time.sleep(2)
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

            self.s.write(cmd_data)
            time.sleep(5)

            self.reader.shutdown()
            logger.info(f'send_ir_off end.')
            print(f'{datetime.now()} send_ir_off end.')
        except Exception as ex:
            logger.error(f'{ex}')


class SerialDeviceReader(Thread):

    def __init__(self, s):
        Thread.__init__(self)
        self.stopped = Event()
        self.s = s

        logger.info('SerialDeviceReader init.')
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
                    logger.debug(f'{buf}')
                else:
                    buf.clear()
                    time.sleep(0.001)

            except Exception as ex:
                print(ex)
                continue



    def shutdown(self):
        self.stopped.set()
        self.s.close()
        logger.info('SerialDeviceReader shutdown.')


if __name__ == '__main__':
    airmon = AirconIrController()
    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            logger.error('Ctrl+C and Exit')
            airmon.shutdown()
            sys.exit()

