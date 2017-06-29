#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Created : Thu 29 Jun 2017 01:57:08 PM EDT
# Modified: Thu 29 Jun 2017 05:41:10 PM EDT

import better_exceptions
import serial
from collections import deque
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import math
import time
from termcolor import cprint


version = 0.98
runningMeanLen = 1000
# serialPort = 'COM3:'  # Windows 10
serialPort = '/dev/cu.usbmodem1411'  # OS X El Capt. (elgato)
# serialPort = '/dev/ttyACM0'   # Linux Mint 17.3 Rosa

pcolor = lambda color, arg: cprint(arg, color, attrs=['reverse'])


class CircularBuffer(deque):
    """
    Circular buffer w/ average from stackoverflow:
        https://stackoverflow.com/questions/4151320/efficient-circular-buffer
    However using varance/delta instead.
    """
    def __init__(self, size=0):
        super(CircularBuffer, self).__init__(maxlen=size)

    # @property
    # def average(self):  # TODO: Make type check for integer or floats
    #     return sum(self)/len(self)

    @property
    def online_variance(self):
        """ NOTE: Returns mean and deviation not variance """
        n = 0
        mean = 0.0
        mean2 = 0.0

        for x in self:
            n += 1
            delta = x - mean
            mean += delta / n
            mean2 += delta * (x - mean)

        if n < 2:
            m, v = float('nan'), float('nan')
        else:
            m, v = mean, mean2 / (n - 1)

        return m, math.sqrt(v)


def trend(value, mean):
    """ return an ASCII trend indicator to print """
    v = float(value)
    a = float(mean)

    # pcolor('red', 'v={}, a={}'.format(v, a))

    if (a == 0.0):
        ind = '*'  # no delta yet
    elif (v > a):
        ind = '^'
    elif (v < a):
        ind = 'v'
    else:
        ind = ' '

    return ind


def main():
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

    ser = serial.Serial(serialPort, 9600)   # Needed for OS X

    logger.info('\"BLE Weather Monitor V{}\",,\"Running Mean Size:\",{}'.format(
        version, runningMeanLen))
    logger.info('\"Date & Time\",\"°C\",\"°C mean\",\"°F\",\"°F mean\",\"H%\",\"H% mean\",\"inHg\",\"inHg mean\",\"kPa\",\"kPa mean\",\"Hg 1hr delta\", \"Hg 3hr delta\"')

    # create circular buffers for running means
    celsius_cb = CircularBuffer(size=runningMeanLen)
    fahrenheit_cb = CircularBuffer(size=runningMeanLen)
    humidity_cb = CircularBuffer(size=runningMeanLen)
    kilopascal_cb = CircularBuffer(size=runningMeanLen)
    inch_of_mercury_cb = CircularBuffer(size=runningMeanLen)

    # throw out header from ardunio code
    i = 2
    while i > 0:
        i -= 1
        pcolor('cyan', ser.readline())  # get rid of header +/-

    hg_delta = 0.0      # inHg delta value
    hg_last = 0.0       # last inHg value
    alert = ''          # pressure change alert
    delay = 6           # 6 seconds between readings
    t = 0               # time counter
    hr = 0              # hour counter
    three_delta = 0.0   # three hour delta value
    three_last = 0.0    # last three hour delta value
    # main loop
    while True:
        print('\n{}:'.format(t))

        raw = ser.readline()
        print('raw:{}'.format(raw))

        # check for serial line error that translates to unpacking ValueError
        try:
            c, f, h, pa, hg = raw.decode().rstrip().split(',')
        except (ValueError):
            continue

        c = float(c)                # celsius
        f = float(f)                # fahrenheit
        h = float(h)                # humidity
        kpa = float(pa) / 1000.0    # kilopascal
        hg = float(hg)              # inches of mercury

        # mean and delta calculations  TODO: clean this up (ADT?, nested?)
        c_m, c_d = 0.0, 0.0
        f_m, f_d = 0.0, 0.0
        h_m, h_d = 0.0, 0.0
        kpa_m, kpa_d = 0.0, 0.0
        hg_m, hg_d = 0.0, 0.0
        if (t > 3):
            c_m, c_d = celsius_cb.online_variance
            f_m, f_d = fahrenheit_cb.online_variance
            h_m, h_d = humidity_cb.online_variance
            kpa_m, kpa_d = kilopascal_cb.online_variance
            hg_m, hg_d = inch_of_mercury_cb.online_variance
            # init last hg values
            if (t == 4):
                hg_last = hg  # initial hg_last value
                three_last = hg

        # add values to circular buffers
        celsius_cb.append(c)
        fahrenheit_cb.append(f)
        humidity_cb.append(h)
        kilopascal_cb.append(kpa)
        inch_of_mercury_cb.append(hg)

        # check for hourly readings
        if (t == 600):
            t = 0
            hr += 1
            if hr == 3:
                hr = 0
                three_delta = three_last - hg
                three_last = hg

            hg_delta = hg_last - hg
            hg_last = hg
            if (hg_delta > 0.06):
                alert = 'rapid pressure rise'
            elif (hg_delta < -0.06):
                alert = 'rapid pressure fall'
            else:
                alert = ''

        # output to console
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
        print('t = {}, hg_delta = {:.3f}, hg_last = {:.3f}, 3hr={:.3f}  {}'.format(
            t * delay, hg_delta, hg_last, three_delta, alert))
        dew = f - (0.36 * (100.0 - h))
        print('dew: {}'.format(dew))

        # output to .csv file
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fs = ''  # format string
        for j in range(12):
            fs += ',\"{:.4f}\"'
        logger.info('\"{}\"'.format(dt) + fs.format(
            c,   c_m,
            f,   f_m,
            h,   h_m,
            hg,  hg_m,
            kpa, kpa_m,
            hg_delta, three_delta))

        time.sleep(delay)

        t += 1


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
