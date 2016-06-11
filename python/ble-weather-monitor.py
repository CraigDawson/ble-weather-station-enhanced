import serial
from collections import deque
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import math

version = 0.8
runningMeanLen = 1000
# serialPort = 'COM3:'  # Windows 10
# serialPort = '/dev/cu.usbmodem1421'  # OS X El Capt.
serialPort = '/dev/ttyACM0'   # Linux Mint 17.3 Rosa


class CircularBuffer(deque):
    """ circular buffer w/ average from stackoverflow """
    def __init__(self, size=0):
        super(CircularBuffer, self).__init__(maxlen=size)

    @property
    def average(self):  # TODO: Make type check for integer or floats
        return sum(self)/len(self)

    @property
    def online_variance(self):
        n = 0
        mean = 0.0
        M2 = 0.0

        for x in self:
            n += 1
            delta = x - mean
            mean += delta / n
            M2 += delta * (x - mean)

        if n < 2:
            return float('nan'), float('nan')
        else:
            return mean, M2 / (n - 1)


def trend(v, a):
    vf = float(v)
    af = float(a)

    if (vf > af):
        return '^'
    elif (vf < af):
        return 'v'
    else:
        return ' '


"""
Creates a rotating log
"""
logger = logging.getLogger("Rotating Log")
logger.setLevel(logging.INFO)

# add a rotating handler
handler = RotatingFileHandler('ble-weather.csv',
                              maxBytes=5000000,
                              backupCount=5)
logger.addHandler(handler)

ser = serial.Serial(serialPort, 9600)   # OS X

logger.info('\"BLE Weather Monitor V{}\",,\"Running Mean Size:\",{}'.format(
    version, runningMeanLen))
logger.info('\"Date & Time\",\"°C\",\"°C mean\",\"°F\",\"°F mean\",\"H%\",\"H% mean\",\"inHg\",\"inHg mean\",\"kPa\",\"kPa mean\"')

c_cb = CircularBuffer(size=runningMeanLen)
f_cb = CircularBuffer(size=runningMeanLen)
h_cb = CircularBuffer(size=runningMeanLen)
kpa_cb = CircularBuffer(size=runningMeanLen)
hg_cb = CircularBuffer(size=runningMeanLen)

i = 2
while i > 0:
    i -= 1
    print(ser.readline())  # get rid of header +/-

i = 0
while True:
    print('\n{}:'.format(i))

    raw = ser.readline()
    print('raw:{}'.format(raw))

    data = raw.decode().rstrip().split(',')

    # for x in data:
    #     print(x)

    try:
        c = float(data[0])
        f = float(data[1])
        h = float(data[2])
        kpa = float(data[3]) / 1000.0
        hg = float(data[4])
    except ValueError:
        continue

    c_m, c_v, c_d = 0.0, 0.0, 0.0
    f_m, f_v, f_d = 0.0, 0.0, 0.0
    h_m, h_v, h_d = 0.0, 0.0, 0.0
    kpa_m, kpa_v, kpa_d = 0.0, 0.0, 0.0
    hg_m, hg_v, hg_d = 0.0, 0.0, 0.0
    if (i > 3):
        c_m, c_v = c_cb.online_variance
        f_m, f_v = f_cb.online_variance
        h_m, h_v = h_cb.online_variance
        kpa_m, kpa_v = kpa_cb.online_variance
        hg_m, hg_v = hg_cb.online_variance
        c_d = math.sqrt(c_v)
        f_d = math.sqrt(f_v)
        h_d = math.sqrt(h_v)
        kpa_d = math.sqrt(kpa_v)
        hg_d = math.sqrt(hg_v)

    """ TODO: check for serial error here """

    c_cb.append(c)
    f_cb.append(f)
    h_cb.append(h)
    kpa_cb.append(kpa)
    hg_cb.append(hg)

    print('C    = {:11.4f}  ({:11.4f}  {:11.4f} {})'.format(
        c,  c_m, c_d, trend(c, c_m)))
    print('F    = {:11.4f}  ({:11.4f}  {:11.4f} {})'.format(
        f,  f_m, f_d, trend(f, f_m)))
    print('h    = {:11.4f}% ({:11.4f}% {:11.4f} {})'.format(
        h,  h_m, h_d, trend(h, h_m)))
    print('kPa  = {:11.4f}  ({:11.4f}  {:11.4f} {})'.format(
        kpa, kpa_m, kpa_d, trend(kpa, kpa_m)))
    print('"Hg  = {:11.4f}  ({:11.4f}  {:11.4f} {})'.format(
        hg, hg_m, hg_d, trend(hg, hg_m)))

    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fs = ''  # format string
    for j in range(10):
        fs += ',\"{:.4f}\"'
    logger.info('\"{}\"'.format(dt) + fs.format(
        c,   c_m,
        f,   f_m,
        h,   h_m,
        hg,  hg_m,
        kpa, kpa_m))

    i += 1