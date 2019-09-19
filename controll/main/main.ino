#include <Adafruit_NeoPixel.h>
#include <LightShow.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include "Colors.h"
#include <ESP8266WebServer.h>

#define ABS(x) ((x)>0?(x):-(x))

float mapfloat(float x, float in_min, float in_max, float out_min, float out_max)
{
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

#define LED 2
#define COUNT 2

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(COUNT, LED, NEO_RGB + NEO_KHZ800);
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);

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
  pixels.setBrightness(64);
  feedback_severity(severity);
  feedback_digit(d0);
  feedback_digit(d1);
  feedback_digit(d2);
  feedback_severity(severity);
  Colors::black.putAll(pixels, COUNT);
  pixels.show();
  pixels.setBrightness(255);
  delay(FEEDBACK_DUR);
}

//feedbacks table
#define IDLE 0

#define SENSOR_OK 1, 1
#define SENSOR_INIT_ERROR 3, 1

#define PIXELS_OK 1, 2

#define BEFORE_DETECT 0, 1, 1
#define DURING_DETECT 2, 1, 1
#define AFTER_DETECT 0, 1, 1

#define CLIENT_MODE 0, 1
#define SERVER_MODE 0, 2
#define AP_OK 1, 2, 1
#define AP_ERROR 3, 2, 1
//end feedbacks table

float baseX;
float baseY;
float baseZ;

void init_sensor() {
  if(accel.begin())
  {
    feedback(SENSOR_OK);
    Serial.println("sensor init done");
  } else {
    feedback(SENSOR_INIT_ERROR);
    Serial.println("sensor init error");
    ESP.restart();
  }
  // accel.setRange(ADXL345_RANGE_16_G);
  // accel.setRange(ADXL345_RANGE_8_G);
  // accel.setRange(ADXL345_RANGE_4_G);
  // accel.setRange(ADXL345_RANGE_2_G);
}

void detect_rest_position() {
  for (uint8_t i = 0; i < 10; i++) {
    feedback(BEFORE_DETECT);
  }

  Serial.println("measuring rest position");
  float sumX = 0;
  float sumY = 0;
  float sumZ = 0;
  for (uint8_t i = 0; i < 10; i++) {
    sensors_event_t event; 
    accel.getEvent(&event);
    sumX += mapfloat(event.acceleration.x, -14.08, 6.39, -1.0, 1.0);
    sumY += mapfloat(event.acceleration.y, -12.63, 7.41, -1.0, 1.0);
    sumZ += mapfloat(event.acceleration.z, -1.69, 20.04, -1.0, 1.0);
    feedback(DURING_DETECT);
  }
  baseX = sumX / 10.0;
  baseY = sumY / 10.0;
  baseZ = sumZ / 10.0;
  feedback(AFTER_DETECT);
  Serial.print("rest position (");
  Serial.print(baseX); Serial.print("; ");
  Serial.print(baseY); Serial.print("; ");
  Serial.print(baseZ);
  Serial.println(")");
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
IPAddress local_IP(192,168,0,1);
IPAddress gateway(192,168,0,255);
IPAddress subnet(255,255,255,0);
bool server_mode = false;

void init_network() {
  int numberOfNetworks = WiFi.scanNetworks();
  Serial.println("Aviable networks");
  bool found = false;
  byte channel_counts[13] = {0,0,0,0,0,0,0,0,0,0,0,0,0};
  for(int i = 0; i < numberOfNetworks; i++){
      Serial.println(WiFi.SSID(i));
      if (WiFi.SSID(i) == ssid) {
        found = true;
      }
      byte current_channel = WiFi.channel(i) - 1;
      if (current_channel > 1) {
        channel_counts[current_channel - 2] += 2;
      }
      if (current_channel > 0) {
        channel_counts[current_channel - 1] += 1;
      }
      channel_counts[current_channel] += 3;
      if (current_channel < 12) {
        channel_counts[current_channel + 1] += 1;
      }
      if (current_channel < 11) {
        channel_counts[current_channel + 2] += 2;
      }
  }

  byte best_channel = 1;
  byte best_count = channel_counts[1];
  for(byte i = 0; i < 13; i++){
    Serial.print(i); Serial.print("->");
    Serial.println(channel_counts[i]);
    if (best_count > channel_counts[i]) {
      best_channel = i;
      best_count = channel_counts[i];
    }
  }
  Serial.print("best channel: ");
  Serial.println(best_channel);

  if (found) {
    feedback(CLIENT_MODE);
    server_mode = false;
    //TODO:implement this
    ESP.restart();
  } else {
    feedback(SERVER_MODE);
    server_mode = true;
    Serial.print("Setting soft-AP configuration ... ");
    Serial.println(WiFi.softAPConfig(local_IP, gateway, subnet) ? "Ready" : "Failed!");
    Serial.print("Setting soft-AP ... ");
    boolean result = WiFi.softAP(ssid, password, best_channel + 1);
    if(result == true)
    {
      feedback(AP_OK);
      Serial.println("Ready");
      Serial.print("IP address: ");
      Serial.println(WiFi.softAPIP());
    } else {
      feedback(AP_ERROR);
      Serial.println("Failed!");
      ESP.restart();
    }
  }
}

ESP8266WebServer server(80);

void init_client() {
  //TODO: implement this
  ESP.restart();
}

IPAddress* clients[4] = { NULL };

void hReg() {
  bool stored = false;
  for (byte i = 0; i < 4; i++) {
    if (clients[i] == NULL) {
      IPAddress remote_ip = server.client().remoteIP();
      clients[i] = new IPAddress(remote_ip[0], remote_ip[1], remote_ip[2], remote_ip[3]);
      stored = true;
      break;
    }
  }
  if (stored) {
    server.send(200, "text/plain", "Registration of " + server.client().remoteIP().toString());
  } else {
    server.send(200, "text/plain", "There is not any free slot.");
  }
}

void hReset() {
  server.send(200, "text/plain", "The server will restart.");
  ESP.restart();
}

void hClients() {
  String response = "Connected clients:\n";
  for (byte i = 0; i < 4; i++) {
    if (clients[i] != NULL) {
      response += (*clients[i]).toString();
    } else {
      response += "(empty)";      
    }
    response += '\n';
  }
  server.send(200, "text/plain", response);
}

void init_server() {
  server.on("/reg", hReg);
  server.on("/reset", hReset);
  server.on("/clients", hClients);
  server.begin();
}

void init_http() {
  if (server_mode) {
    init_server();
  } else {
    init_client();
  }
}

void setup() {
  delay(1000);
  randomSeed(analogRead(0));
  Serial.begin(9600);
  init_pixels();
  init_sensor();
  //detect_rest_position();
  init_network();
  init_http();
}

#define SLOWNESS 1500

/*void leaves() {
  Color blacks[COUNT] = {
    Colors::black,
    Colors::black
  };
  Color key0[COUNT] = {
    fuji_red,
    fuji_green
  };
  Color key1[COUNT] = {
    fuji_red,
    fuji_green
  };
  Color key2[COUNT] = {
    fuji_green,
    fuji_gold
  };
  Color key3[COUNT] = {
    fuji_deep_red,
    fuji_deep_red
  };
  MULTIFADE(COUNT, blacks, SLOWNESS, key0, pixels, false)
  MULTIFADE(COUNT, key0, SLOWNESS, key1, pixels, false)
  MULTIFADE(COUNT, key1, SLOWNESS, key2, pixels, false)
  MULTIFADE(COUNT, key2, SLOWNESS, key3, pixels, false)
  MULTIFADE(COUNT, key3, SLOWNESS, blacks, pixels, false)
  Colors::black.putAll(pixels, COUNT);
  pixels.show();
}

void spark() {
  long count = random(5, 10);
  for (uint8_t i = 0; i < count; i++){
    long index = random(COUNT);
    FADE(Colors::black, SLOWNESS/8, fuji_deep_red, pixels, index, false)
    FADE(fuji_deep_red, SLOWNESS/4, uovo01, pixels, index, false)
    FADE(uovo01, SLOWNESS/16, fuji_deep_red, pixels, index, false)
    FADE(fuji_deep_red, SLOWNESS/16, Colors::black, pixels, index, false)
    delay(random(100));
  }
  Colors::black.putAll(pixels, COUNT);
  pixels.show();
}

#define SENSOR_LIMIT .1
*/

void loop() {
  feedback(IDLE);

  server.handleClient();

  
//  FADE(Colors::black, 1000, Colors::red+Colors::blue, pixels, 0, true)
//  FADE(Colors::black, 1000, Colors::red+Colors::blue, pixels, 1, true)
/*  sensors_event_t event; 
  accel.getEvent(&event);
  float deltaX = baseX - mapfloat(event.acceleration.x, -14.08, 6.39, -1.0, 1.0);
  float deltaZ = baseZ - mapfloat(event.acceleration.z, -1.69, 20.04, -1.0, 1.0);
  float deltaY = baseY - mapfloat(event.acceleration.y, -12.63, 7.41, -1.0, 1.0);
  Serial.print("deltaX: "); Serial.print(deltaX); Serial.print("  ");
  Serial.print("deltaY: "); Serial.print(deltaY); Serial.print("  ");
  Serial.print("deltaZ: "); Serial.print(deltaZ); Serial.print("  ");

  if (   ABS(deltaX) > SENSOR_LIMIT 
      || ABS(deltaY) > SENSOR_LIMIT
      || ABS(deltaZ) > SENSOR_LIMIT
      || random(100) == 0) {
    switch (random(2)) {
      case 0:
        spark();
        break;
      case 1:
        leaves();
        break;
    }
  }

  Serial.println();
*/}
