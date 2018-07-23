#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Created : Thu 29 Jun 2017 01:57:08 PM EDT
# Modified: Mon 23 Jul 2018 05:45:13 PM EDT

import better_exceptions
import serial
from collections import deque
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
import math
import time
from termcolor import cprint

version = 0.99
runningMeanLen = 100
# serialPort = 'COM3:'  # Windows 10
# serialPort = "/dev/cu.usbmodem1411"  # OS X El Capt. (elgato)
serialPort = "/dev/ttyACM0"  # Linux Mint 17.3 Rosa


class HeaderTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    Timed Rotating Log File Handler with Header for each rotated log file.
    """
    def __init__(self,
                 filename,
                 header=None,
                 when='h',
                 interval=1,
                 backupCount=0,
                 log=None):
        self._header = header
        self._log = log
        super().__init__(filename, when, interval, backupCount)

    def doRollover(self):
        super().doRollover()
        self.doHeader()

    def doHeader(self):
        if self._log is not None and self._header is not None:
            self._log.info(self._header)


""" Little color lambda function """
pcolor = lambda color, arg: cprint(arg, color, attrs=["reverse"])


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
    def online_mean_deviation(self):
        """ Returns mean and deviation """
        n = 0
        mean = 0.0
        variance = 0.0

        for x in self:
            if x == 0:
                msg = "CB datum is 0"
                elog.error(msg)
                pcolor("red", msg)
                continue
            n += 1
            delta = x - mean
            mean += delta / n
            variance += delta * (x - mean)

        if n < 2:
            m, v = float("nan"), float("nan")
        else:
            m, v = mean, variance / (n - 1)

        return m, math.sqrt(v)


def trend(value, mean):
    """ return an ASCII trend indicator to print """
    v = float(value)
    a = float(mean)

    if a == 0.0:
        ind = "*"  # no delta yet
    elif v > a:
        ind = "^"
    elif v < a:
        ind = "v"
    else:
        ind = " "

    return ind


#----------------------------------------------------------------------
def create_timed_rotating_log(path, header):
    """"""
    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.INFO)

    handler = HeaderTimedRotatingFileHandler(
        path, header, when="W6", interval=1, backupCount=5, log=logger)
    logger.addHandler(handler)
    return logger, handler


#----------------------------------------------------------------------


def main():
    """
    Creates a rotating log
    """
    hdr = '"Date & Time","°C","°C mean","°F","°F mean","H%","H% mean","inHg","inHg mean","kPa","kPa mean","Hg 1hr delta","Hg 3hr delta","Dew Point"'

    logger, handler = create_timed_rotating_log("ble-weather.csv", hdr)
    handler.doHeader()  # Need to do initial header

    logger.setLevel(logging.INFO)

    # error log
    elog = logging.getLogger(__name__)
    elog.setLevel(logging.INFO)
    elog.info("BLE Weather Monitor V{}".format(version))

    ser = serial.Serial(serialPort, 9600)  # Needed for OS X

    pcolor(
        'cyan', 'BLE Weather Monitor V{}    Running Mean Size: {}'.format(
            version, runningMeanLen))

    # create circular buffers for running means
    celsius_cb = CircularBuffer(size=runningMeanLen)
    fahrenheit_cb = CircularBuffer(size=runningMeanLen)
    humidity_cb = CircularBuffer(size=runningMeanLen)
    kilopascal_cb = CircularBuffer(size=runningMeanLen)
    inch_of_mercury_cb = CircularBuffer(size=runningMeanLen)

    # throw out header from ardunio code  TODO: be smarter, eg, throw out until good data
    i = 2
    while i > 0:
        i -= 1
        pcolor("cyan", ser.readline())  # get rid of header +/-

    hg_delta = 0.0  # inHg delta value
    hg_last = 0.0  # last inHg value
    alert = ""  # pressure change alert
    delay = 6  # 6 seconds between readings
    t = 0  # time counter (zeros every hour)
    t2 = 0  # counts forever (roll over value??)
    hr = 0  # hour counter
    three_delta = 0.0  # three hour delta value
    three_last = 0.0  # last three hour delta value
    # main loop
    while True:
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("\n{}: {} / {}".format(dt, t, t2))

        raw = ser.readline()
        print("raw:{}".format(raw))

        # check for serial line error that translates to unpacking ValueError
        try:
            c, f, h, pa, hg = raw.decode().rstrip().split(",")
        except (ValueError):
            continue

        c = float(c)  # celsius
        f = float(f)  # fahrenheit
        if c == 0.0 or f == 0.0:
            msg = "{}: c={}, f={}, one or both zero, skipping...".format(
                dt, c, f)
            elog.error(msg)
            pcolor("red", msg)
            continue
        h = float(h)  # humidity
        kpa = float(pa) / 1000.0  # kilopascal
        hg = float(hg)  # inches of mercury

        # mean and delta calculations  TODO: clean this up (named tuples)
        c_m, c_d = 0.0, 0.0
        f_m, f_d = 0.0, 0.0
        h_m, h_d = 0.0, 0.0
        kpa_m, kpa_d = 0.0, 0.0
        hg_m, hg_d = 0.0, 0.0
        if t2 > 3:  # Need at least 3 reading to get mean & deviation from CB
            c_m, c_d = celsius_cb.online_mean_deviation
            f_m, f_d = fahrenheit_cb.online_mean_deviation
            h_m, h_d = humidity_cb.online_mean_deviation
            kpa_m, kpa_d = kilopascal_cb.online_mean_deviation
            hg_m, hg_d = inch_of_mercury_cb.online_mean_deviation
            # init last hg values
            if t2 == 4:  # After first averages then initialize other Hg's
                hg_last = hg  # initial hg_last value
                three_last = hg

        # add values to circular buffers
        celsius_cb.append(c)
        fahrenheit_cb.append(f)
        humidity_cb.append(h)
        kilopascal_cb.append(kpa)
        inch_of_mercury_cb.append(hg)

        # check for hourly readings
        if t == 600:
            t = 0
            hr += 1
            if hr == 3:
                hr = 0
                three_delta = three_last - hg
                three_last = hg

            hg_delta = hg_last - hg
            hg_last = hg
            if hg_delta > 0.06:  # rapid pressure rise threshold
                alert = "rapid pressure rise"
            elif hg_delta < -0.06:  # rapid pressure fall threshold
                alert = "rapid pressure fall"
            else:
                alert = ""

        # output to console
        print("C    = {:11.4f}  ({:11.4f}  {:11.4f} {})".format(
            c, c_m, c_d, trend(c, c_m)))
        print("F    = {:11.4f}  ({:11.4f}  {:11.4f} {})".format(
            f, f_m, f_d, trend(f, f_m)))
        print("h    = {:11.4f}% ({:11.4f}% {:11.4f} {})".format(
            h, h_m, h_d, trend(h, h_m)))
        print("kPa  = {:11.4f}  ({:11.4f}  {:11.4f} {})".format(
            kpa, kpa_m, kpa_d, trend(kpa, kpa_m)))
        print('"Hg  = {:11.4f}  ({:11.4f}  {:11.4f} {})'.format(
            hg, hg_m, hg_d, trend(hg, hg_m)))
        print("t = {}, hg_delta = {:.3f}, hg_last = {:.3f}, 3hr={:.3f}  {}".
              format(t * delay, hg_delta, hg_last, three_delta, alert))
        dew = f - (0.36 * (100.0 - h))
        print("dew: {}".format(dew))

        if t2 > 3:  # don't log 0 means
            # output to .csv file
            fs = ""  # format string
            for j in range(13):
                fs += ',"{:.4f}"'
            logger.info('"{}"'.format(dt) + fs.format(
                c,
                c_m,
                f,
                f_m,
                h,
                h_m,
                hg,
                hg_m,
                kpa,
                kpa_m,
                hg_delta,
                three_delta,
                dew,
            ))

        time.sleep(delay)

        t += 1
        t2 += 1


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
