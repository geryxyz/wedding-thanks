#include <Adafruit_NeoPixel.h>
#include <LightShow.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <LSM303.h>
#include "Colors.h"
#include <ESP8266WebServer.h>
#include <cstdint>
#include <limits>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

template <typename T>
constexpr double normalize (T value) {
  return value < 0
    ? -static_cast<double>(value) / std::numeric_limits<T>::min()
    :  static_cast<double>(value) / std::numeric_limits<T>::max()
    ;
}

#define ABS(x) ((x)>0?(x):-(x))

float mapfloat(float x, float in_min, float in_max, float out_min, float out_max)
{
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

#define LED 2
#define COUNT 2

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(COUNT, LED, NEO_RGB + NEO_KHZ800);

#define FEEDBACK_DUR 500

void feedback_digit(byte digit) {
  switch (digit) {
    case 1:
      FADE(Colors::black, FEEDBACK_DUR, Colors::red, pixels, 0, true)
    break;
    case 2:
      FADE(Colors::black, FEEDBACK_DUR, Colors::red + Colors::green, pixels, 0, true)
    break;
    case 3:
      FADE(Colors::black, FEEDBACK_DUR, Colors::green, pixels, 0, true) 
    break;
    case 4:
      FADE(Colors::black, FEEDBACK_DUR, Colors::green + Colors::blue, pixels, 0, true)
    break;
    case 5:
      FADE(Colors::black, FEEDBACK_DUR, Colors::blue, pixels, 0, true)
    break;
    case 6:
      FADE(Colors::black, FEEDBACK_DUR, Colors::blue + Colors::red, pixels, 0, true)
    break;
    case 7:
      FADE(Colors::black, FEEDBACK_DUR, Colors::white, pixels, 0, true)
    break;
    default:
    break;
  }
}

void feedback_severity(byte level) {
  switch (level) {
    case 0:
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::white, pixels, 0, true)
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::white, pixels, 0, true)
    break;
    case 1:
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::green, pixels, 0, true)
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::green, pixels, 0, true)
    break;
    case 2:
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::green + Colors::red, pixels, 0, true)
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::green + Colors::red, pixels, 0, true)
    break;
    case 3:
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::red, pixels, 0, true)
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::red, pixels, 0, true)
    break;
    default:
    break;
  }
}

void feedback(byte severity, byte d0=0, byte d1=0, byte d2=0) {
  pixels.setBrightness(255);
  feedback_severity(severity);
  feedback_digit(d0);
  feedback_digit(d1);
  feedback_digit(d2);
  feedback_severity(severity);
  Colors::black.putAll(pixels, COUNT);
  pixels.show();
  pixels.setBrightness(255);
  delay(FEEDBACK_DUR * 2);
}

// 0 - status
// 1 - ok
// 2 - warn
// 3 - error
//feedbacks table
#define IDLE                 0

#define SENSOR_OK            1, 1
#define SENSOR_INIT_ERROR    3, 1, 1
#define SENSOR_ERROR         3, 1, 2 

#define PIXELS_OK            1, 2

#define BEFORE_DETECT        0, 3, 1
#define DURING_DETECT        2, 3, 1
#define AFTER_DETECT         0, 3, 2

#define CONNECTION_WAITING   2, 4
#define CONNECTION_OK        1, 4, 1 
#define CONNECTION_ERROR     3, 4, 1
#define CONNECTION_LOST      3, 4, 2

#define REGISTRATION_OK      1, 5, 2
#define REGISTRATION_ERROR   3, 5, 3

#define MOVEMENT_ERROR       3, 6
//end feedbacks table

Adafruit_ADXL345_Unified accel1 = Adafruit_ADXL345_Unified(12345);
LSM303 accel2;

byte accel_num = 0;

void init_sensor() {
  if(accel1.begin())
  {
    Serial.println("looking for ADXL345...");
    accel_num = 1;
    feedback(SENSOR_OK);
    Serial.println("sensor init done");
  } else {
    Serial.println("looking for LSM303...");
    Wire.begin();
    if (accel2.init()) {
      accel2.enableDefault();
      accel_num = 2;
      feedback(SENSOR_OK);
      Serial.println("sensor init done");
    } else {
      feedback(SENSOR_INIT_ERROR);
      Serial.println("sensor init error");
      accel_num = 0;
      //ESP.restart();
    }
  }
}

#define XLIMITS1 -11.0, 9.0
#define YLIMITS1 -5.0, 14.0
#define ZLIMITS1 0.0, 24.0

#define XLIMITS2 -.5, .5
#define YLIMITS2 -.5, .5
#define ZLIMITS2 -.5, .5

void measure(float &x, float &y, float &z) {
  if (accel_num == 1) {
    sensors_event_t event; 
    accel1.getEvent(&event);
    x = mapfloat(event.acceleration.x, XLIMITS1, -1.0, 1.0);
    y = mapfloat(event.acceleration.y, YLIMITS1, -1.0, 1.0);
    z = mapfloat(event.acceleration.z, ZLIMITS1, -1.0, 1.0);
  } else if (accel_num == 2) {
    accel2.readAcc();
    x = mapfloat(normalize(accel2.a.x), XLIMITS2, -1.0, 1.0);
    y = mapfloat(normalize(accel2.a.y), YLIMITS2, -1.0, 1.0);
    z = mapfloat(normalize(accel2.a.z), ZLIMITS2, -1.0, 1.0);
  } else {
    Serial.println("Invalid sensor number.");
    feedback(SENSOR_ERROR);
    ESP.restart();
  }
}

float baseX = 0.0f;
float baseY = 0.0f;
float baseZ = 0.0f;

void detect_rest_position() {
  Serial.print("Waiting before measuring rest position... ");
  for (uint8_t i = 0; i < 10; i++) {
    feedback(BEFORE_DETECT);
    Serial.print(i); Serial.print(" ");
  }
  Serial.println();

  Serial.println("measuring rest position");
  float sumX = 0;
  float sumY = 0;
  float sumZ = 0;
  for (uint8_t i = 0; i < 10; i++) {
    float x, y, z;
    measure(x, y, z);
    sumX += x;
    sumY += y;
    sumZ += z;
    Serial.print("x: "); Serial.print(x);
    Serial.print(" y: "); Serial.print(y);
    Serial.print(" z: "); Serial.println(z);
    feedback(DURING_DETECT);
  }
  baseX = sumX / 10.0f;
  baseY = sumY / 10.0f;
  baseZ = sumZ / 10.0f;
  feedback(AFTER_DETECT);
  Serial.print("rest position (");
  Serial.print(baseX); Serial.print("; ");
  Serial.print(baseY); Serial.print("; ");
  Serial.print(baseZ);
  Serial.println(")");
}

void measure_delta(float &deltaX, float &deltaY, float &deltaZ) {
  float x, y, z;
  measure(x, y, z);
  deltaX = baseX - x;
  deltaY = baseY - y;
  deltaZ = baseZ - z;
}

void init_pixels() {
  pixels.begin();
  pixels.setBrightness(255);
  Colors::black.putAll(pixels, COUNT);
  pixels.show();
  feedback(PIXELS_OK);
  Serial.println("pixels init done");
}

const char* ssid = "wedding-thanks";
const char* password = "iluvatar";

void init_STA() {
  WiFi.begin(ssid, password);
  Serial.print("connecting to WIFI");
  for (byte i = 0; i < 100; i++) {
    if (WiFi.status() == WL_CONNECTED) {
      break;
    }
    feedback(CONNECTION_WAITING);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" WIFI connected.");
    feedback(CONNECTION_OK);
  } else {
    Serial.println(" No network.");
    feedback(CONNECTION_ERROR);
    ESP.restart();
  }  
}

void init_network() {
  Serial.println("Client mode activated");
  WiFi.mode(WIFI_STA);
  WiFi.setSleepMode(WIFI_NONE_SLEEP);
  init_STA();
}

ESP8266WebServer server(80);
HTTPClient http_client;

void hRoot() {
  server.send(200, "text/plain", "This is a working client.");
}

void hShow() {
  if (
      server.arg("ftR") != "" && server.arg("ftG") != "" && server.arg("ftB") != "" &&
      server.arg("ttR") != "" && server.arg("ttG") != "" && server.arg("ttB") != "" &&
      server.arg("fbR") != "" && server.arg("fbG") != "" && server.arg("fbB") != "" &&
      server.arg("tbR") != "" && server.arg("tbG") != "" && server.arg("tbB") != "" &&
      server.arg("d") != "" ) {
    server.send(200, "text/plain", "");
    Color from[2] = {
      Color((uint8_t)server.arg("ftR").toInt(), (uint8_t)server.arg("ftG").toInt(), (uint8_t)server.arg("ftB").toInt()),
      Color((uint8_t)server.arg("fbR").toInt(), (uint8_t)server.arg("fbG").toInt(), (uint8_t)server.arg("fbB").toInt())      
    };
    Color to[2] = {
      Color((uint8_t)server.arg("ttR").toInt(), (uint8_t)server.arg("ttG").toInt(), (uint8_t)server.arg("ttB").toInt()),
      Color((uint8_t)server.arg("tbR").toInt(), (uint8_t)server.arg("tbG").toInt(), (uint8_t)server.arg("tbB").toInt())
    };
    int duration = server.arg("d").toInt();
    //Serial.println("showing animation");
    MULTIFADE(COUNT, from, duration, to, pixels, false)
  } else {
    server.send(500, "text/plain", "");
    Serial.println("missing arguments for animation");
  }
}

bool is_measurement_on = true;

void hToggleMeasurement() {
  is_measurement_on = !is_measurement_on;
  server.send(200, "text/plain", String(is_measurement_on));
  Serial.print("Measurement: "); Serial.println(is_measurement_on);
}

float sensor_limit = .05;

void hLimit() {
  if (server.arg("l") != "") {
    sensor_limit = server.arg("l").toFloat();
    server.send(200, "text/plain", String(sensor_limit));
  } else {
    server.send(500, "text/plain", "");
    Serial.println("missing arguments for setting a limit");
  }
}

void init_http() {
  server.on("/", hRoot);
  server.on("/show", hShow);
  server.on("/toggle", hToggleMeasurement);
  server.on("/limit", hLimit);
  server.begin();
  Serial.print("Registration with server ... ");
  http_client.begin("http://192.168.1.2/reg");
  int status_code = http_client.GET();
  http_client.end();
  if (status_code == 200) {
    Serial.print(" done");
    Serial.print(" (status:"); Serial.print(status_code); Serial.println(")"); 
    feedback(REGISTRATION_OK);
  } else {
    Serial.print(" error");
    Serial.print(" (status:"); Serial.print(status_code); Serial.println(")");
    if (status_code < 0) {
       Serial.print("error: "); Serial.println(http_client.errorToString(status_code).c_str());
       Serial.print("WiFi status: "); Serial.println(WiFi.status()); 
    }
    feedback(REGISTRATION_ERROR);
    ESP.restart();
  }
}

#define BOUNCING_LIMIT 10000
unsigned long last_movement = 0;

void signalMovement() {
  Serial.print("Signal movement... ");
  http_client.begin("http://192.168.1.2/move");
  int status_code = http_client.GET();
  http_client.end();
  if (status_code == 200) {
    last_movement = millis();
    Serial.print("done");
    Serial.print(" (status:"); Serial.print(status_code); Serial.println(")"); 
    
  } else {
    Serial.print("error");
    Serial.print(" (status:"); Serial.print(status_code); Serial.println(")");
    if (status_code < 0) {
       Serial.print("error: "); Serial.println(http_client.errorToString(status_code).c_str());
       Serial.print("WiFi status: "); Serial.println(WiFi.status()); 
    }
    //feedback(MOVEMENT_ERROR);
    //ESP.restart();
  }
}

void setup() {
  WiFi.mode(WIFI_OFF);
  delay(1000);
  randomSeed(analogRead(0));
  Serial.begin(9600);
  Serial.println();
  init_pixels();
  init_sensor();
  if (accel_num != 0) {
    detect_rest_position();
  }
  init_network();
  init_http();
}

void loop() {
  server.handleClient();
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("connection lost");
    while (true) {
      feedback(CONNECTION_LOST);
    }
  }

  if (accel_num != 0 && is_measurement_on && (millis() - last_movement > BOUNCING_LIMIT)) {
    float deltaX, deltaY, deltaZ;
    measure_delta(deltaX, deltaY, deltaZ);
    Serial.print("deltaX: "); Serial.print(deltaX); Serial.print("\t");
    Serial.print("deltaY: "); Serial.print(deltaY); Serial.print("\t");
    Serial.print("deltaZ: "); Serial.print(deltaZ); Serial.print("\t");
    Serial.println();
  
    if (ABS(deltaX) > sensor_limit || ABS(deltaY) > sensor_limit || ABS(deltaZ) > sensor_limit) {
      signalMovement();
    }
  }
}
