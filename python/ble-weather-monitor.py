#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Created : Thu 29 Jun 2017 01:57:08 PM EDT
# Modified: Tue 24 Jul 2018 03:31:10 PM EDT

import better_exceptions
import serial
from collections import deque
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
import math
import time
from termcolor import cprint
from collections import namedtuple

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
    hdr = '"Date & Time","°C","°C mean","°F","°F mean","H%","H% mean","inHg","inHg mean","kPa","kPa mean","Hg 1hr delta","Hg 3hr delta","Dew Point", "DP mean"'

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
    dew_point_cb = CircularBuffer(size=runningMeanLen)

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
        dew = f - (0.36 * (100.0 - h))

        # mean and delta calculations
        StatData = namedtuple('StatData', ['mean', 'dev'])
        stats = {
            'celsius': StatData(0.0, 0.0),
            'fahrenheit': StatData(0.0, 0.0),
            'humidity': StatData(0.0, 0.0),
            'kilopascal': StatData(0.0, 0.0),
            'inchOfMercury': StatData(0.0, 0.0),
            'dewPoint': StatData(0.0, 0.0),
        }
        if t2 > 3:  # Need at least 3 reading to get mean & deviation from CB
            stats['celsius'] = StatData(*celsius_cb.online_mean_deviation)
            stats['fahrenheit'] = StatData(
                *fahrenheit_cb.online_mean_deviation)
            stats['humidity'] = StatData(*humidity_cb.online_mean_deviation)
            stats['kilopascal'] = StatData(
                *kilopascal_cb.online_mean_deviation)
            stats['inchOfMercury'] = StatData(
                *inch_of_mercury_cb.online_mean_deviation)
            stats['dewPoint'] = StatData(*dew_point_cb.online_mean_deviation)
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
        dew_point_cb.append(dew)

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
            c, *stats['celsius'], trend(c, stats['celsius'].mean)))
        print("F    = {:11.4f}  ({:11.4f}  {:11.4f} {})".format(
            f, *stats['fahrenheit'], trend(f, stats['fahrenheit'].mean)))
        print("h    = {:11.4f}% ({:11.4f}% {:11.4f} {})".format(
            h, *stats['humidity'], trend(h, stats['humidity'].mean)))
        print("kPa  = {:11.4f}  ({:11.4f}  {:11.4f} {})".format(
            kpa, *stats['kilopascal'], trend(kpa, stats['kilopascal'].mean)))
        print('"Hg  = {:11.4f}  ({:11.4f}  {:11.4f} {})'.format(
            hg, *stats['inchOfMercury'], trend(hg,
                                               stats['inchOfMercury'].mean)))
        print('"DP  = {:11.4f}  ({:11.4f}  {:11.4f} {})'.format(
            dew, *stats['dewPoint'], trend(dew, stats['dewPoint'].mean)))
        print("t = {}, hg_delta = {:.3f}, hg_last = {:.3f}, 3hr={:.3f}  {}".
              format(t * delay, hg_delta, hg_last, three_delta, alert))

        if t2 > 3:  # don't log 0 means
            # output to .csv file
            fs = ""  # format string
            for j in range(14):
                fs += ',"{:.4f}"'
            logger.info('"{}"'.format(dt) + fs.format(
                c, stats['celsius'].mean, f, stats['fahrenheit'].mean, h,
                stats['humidity'].mean, hg, stats['inchOfMercury'].mean, kpa,
                stats['kilopascal'].mean, hg_delta, three_delta, dew,
                stats['dewPoint'].mean))

        time.sleep(delay)

        t += 1
        t2 += 1


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
