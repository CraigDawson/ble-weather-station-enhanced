#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <BLEPeripheral.h>

// define pins for Adafruit Bluefruit LE
// https://github.com/sandeepmistry/arduino-BLEPeripheral#pinouts
#define BLE_REQ 10
#define BLE_RDY 2
#define BLE_RST 9

BLEPeripheral blePeripheral = BLEPeripheral(BLE_REQ, BLE_RDY, BLE_RST);
BLEService weatherService = BLEService("BBB0");
BLEFloatCharacteristic temperatureCharacteristic = BLEFloatCharacteristic("BBB1", BLERead | BLENotify);
BLEDescriptor temperatureDescriptor = BLEDescriptor("2901", "Temp");
BLEFloatCharacteristic humidityCharacteristic = BLEFloatCharacteristic("BBB2", BLERead | BLENotify);
BLEDescriptor humidityDescriptor = BLEDescriptor("2901", "Humidity");
BLEFloatCharacteristic pressureCharacteristic = BLEFloatCharacteristic("BBB3", BLERead | BLENotify);
BLEDescriptor pressureDescriptor = BLEDescriptor("2901", "Pressure");

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
Adafruit_BME280 bme;

unsigned long previousMillis = 0;  // stores the last time sensor was read
unsigned long interval = 6000;     // interval at which to read sensor (milliseconds)
boolean       so = true;           // True for Serial Output

const int RED_PIN = 5;
const int GREEN_PIN = 6;
const int BLUE_PIN = 7;


void setup()
{  
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);  

  // Purple on reset/setup
  digitalWrite(RED_PIN, HIGH);
  digitalWrite(GREEN_PIN, LOW);
  digitalWrite(BLUE_PIN, HIGH);
  
  if (so) {
    Serial.begin(9600);
    Serial.println(F("\"Bluetooth Low Energy Weather Station\""));
    Serial.print(F("\"TemperatureC\","));
    Serial.print(F("\"TemperatureF\","));
    Serial.print(F("\"Humidity\","));
    Serial.print(F("\"PressureP\","));
    Serial.print(F("\"PressureHg"));
    Serial.println("");
  }
  
  // set advertised name and service
  blePeripheral.setLocalName("Weather");
  blePeripheral.setDeviceName("Weather");
  blePeripheral.setAdvertisedServiceUuid(weatherService.uuid());

  // add service and characteristic
  blePeripheral.addAttribute(weatherService);
  blePeripheral.addAttribute(temperatureCharacteristic);
  blePeripheral.addAttribute(temperatureDescriptor);
  blePeripheral.addAttribute(humidityCharacteristic);
  blePeripheral.addAttribute(humidityDescriptor);
  blePeripheral.addAttribute(pressureCharacteristic);
  blePeripheral.addAttribute(pressureDescriptor);

  blePeripheral.begin();
  //bme.begin();
  if (!bme.begin()) {
    if (so) {  
      Serial.println(F("Could not find a valid BME280 sensor, check wiring!"));
    }
    while (1);
  }
}


void loop()
{
  // Tell the bluetooth radio to do whatever it should be working on
  blePeripheral.poll();

  // limit how often we read the sensor
  if (millis() - previousMillis > interval) {
    pollSensors();
    previousMillis = millis();
  }
}


void pollSensors()
{

  float temperature = bme.readTemperature();
  float humidity = bme.readHumidity();
  float pressure = bme.readPressure();

  // if any one of measurements isnan() then return
  if (isnan(temperature) || isnan(humidity) || isnan(pressure)) {
    return;
  }

  // only set the characteristic value if the temperature has changed
  if (temperatureCharacteristic.value() != temperature) {
    temperatureCharacteristic.setValue(temperature);
  }
  if (so) {
    Serial.print(temperature);
    Serial.print(F(","));
  }
  float tempF = temperature * 1.8 + 32;
  if (so) {
    Serial.print(tempF);
    Serial.print(F(","));
  }

  // only set the characteristic value if the humidity has changed
  if (humidityCharacteristic.value() != humidity) {
    humidityCharacteristic.setValue(humidity);
  }
  if (so) {
    Serial.print(humidity);
    Serial.print(F(","));
  }

  // only set the characteristic value if the pressure has changed
  if (pressureCharacteristic.value() != pressure) {
    pressureCharacteristic.setValue(pressure);
  }
  if (so) {
    Serial.print(pressure);
    Serial.print(F(","));
  }
  float pressureHg = pressure / 3386.39;
  if (so) {
    Serial.print(pressureHg);    
    Serial.println("");

    if (pressureHg < 29.0) {
      // Red (turn just the red LED on):
      setIntensity(RED_PIN, 128);
    } else if (pressureHg < 29.7 && pressureHg >= 29.0) {
      // Yellow (turn red and green on):
      showRGB(64);
    } else if (pressureHg >= 29.7) {
      // Green (turn just the green LED on):
      setIntensity(GREEN_PIN, 64);
    }
  }
}


void showRGB(int color)
{
    int redIntensity;
    int greenIntensity;
    int blueIntensity;

    // In each of these zones, we'll calculate the brightness
    // for each of the red, green, and blue LEDs within the RGB LED.

    if (color <= 255)          // zone 1
    {
        redIntensity = 255 - color;    // red goes from on to off
        greenIntensity = color;        // green goes from off to on
        blueIntensity = 0;             // blue is always off
    }
    else if (color <= 511)     // zone 2
    {
        redIntensity = 0;                     // red is always off
        greenIntensity = 255 - (color - 256); // green on to off
        blueIntensity = (color - 256);        // blue off to on
    }
    else // color >= 512       // zone 3
    {
        redIntensity = (color - 512);         // red off to on
        greenIntensity = 0;                   // green is always off
        blueIntensity = 255 - (color - 512);  // blue on to off
    }

    // Now that the brightness values have been set, command the LED
    // to those values

    analogWrite(RED_PIN, redIntensity);
    analogWrite(BLUE_PIN, blueIntensity);
    analogWrite(GREEN_PIN, greenIntensity);
}


void setIntensity(int pin, int intensity)
{
    digitalWrite(RED_PIN, LOW);
    digitalWrite(GREEN_PIN, LOW);
    digitalWrite(BLUE_PIN, LOW);
    analogWrite(pin, intensity);
}

