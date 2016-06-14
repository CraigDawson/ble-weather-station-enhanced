# ble-weather-station-enhanced
Make: Bluetooth book's BLE Weather Station with enhancements

![alt text](https://raw.githubusercontent.com/CraigDawson/ble-weather-station-enhanced/master/documentation/IMG_4110.jpg)

## Introduction

There are two improvements done to the original *BLE Weather Station* from the *Make: Bluetooth* book *(see references below)*

 1.  A tri-color LED module was added to indicate the weather: green - fair, yellow - change, and red - stormy.  This is based on the barometer.  The code for this is on the UNO.

 1. A python program was added to read the UNO's serial port and store the data in a CSV logfile so it can be plotted in Excel or another spreadsheet program.

 1. The only change to the phonegap code was to change the local location in the javascript code.

## New LED Wiring
Below is how you wire the tri-colored LED.
![alt text](https://raw.githubusercontent.com/CraigDawson/ble-weather-station-enhanced/master/arduino/Added_LED_bb.png)

## Example plot of CSV output file
![alt text](https://raw.githubusercontent.com/CraigDawson/ble-weather-station-enhanced/master/documentation/excel_chart.png)

## References:

**Book:**

  * [Make: Bluetooth: Bluetooth LE Projects with Arduino, Raspberry Pi, and Smartphones](https://www.amazon.com/gp/product/1457187094/ref=oh_aui_search_detailpage?ie=UTF8&psc=1)


**Hardware:**

  * [SainSmart UNO](https://www.amazon.com/gp/product/B006GX8IAY/ref=oh_aui_search_detailpage?ie=UTF8&psc=1)

  * [Prototype shield](https://www.amazon.com/gp/product/B00Q9YB7PI/ref=oh_aui_detailpage_o09_s00?ie=UTF8&psc=1)


**Kit 1:**   [Make:Bluetooth Book Parts Pack](https://www.adafruit.com/products/3026)

**Note: these are the only components needed from kit 1**

  * [nRF8001 Breakout](https://www.adafruit.com/product/1697)
  * [BME280 sensor](https://www.adafruit.com/product/2652)


**Kit 2:**  [SainSmart New Basic Starter Kit for Arduino](https://www.amazon.com/gp/product/B00UV7KAPM/ref=oh_aui_search_detailpage?ie=UTF8&psc=1)

**Note: The RGB LED board is all that is needed and an UNO (the one above or this one)**

  * RGB component *It is a board with an RBG LED, limiting resistors, and pins. You could use the discrete components instead.*
  * Kit does include a UNO board


**Original Book Code:**

  * [Make: Bluetooth ble-weather code from book](https://github.com/MakeBluetooth/ble-weather)
