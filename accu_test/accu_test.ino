#include <Adafruit_NeoPixel.h>
#include <LightShow.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>

IPAddress local_IP(192,168,0,1);
IPAddress gateway(192,168,0,255);
IPAddress subnet(255,255,255,0);

const char* ssid = "test-net";
const char* password = "iluvatar";

#define LED 2
#define COUNT 2

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(COUNT, LED, NEO_RGB + NEO_KHZ800);
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);

ESP8266WebServer server(80);

void handleRoot();
void handleNotFound();

void setup() {
  Serial.begin(9600);
  pixels.begin();
  pixels.setBrightness(255);
  Colors::black.putAll(pixels, COUNT);
  pixels.show();
  
  Serial.print("Setting soft-AP configuration ... ");
  Serial.println(WiFi.softAPConfig(local_IP, gateway, subnet) ? "Ready" : "Failed!");
  Serial.print("Setting soft-AP ... ");
  boolean result = WiFi.softAP(ssid, password);
  if(result == true)
  {
    FADE(Colors::black, 1000, Colors::green, pixels, 0, true)
    Serial.print("IP address:\t");
    Serial.println(WiFi.softAPIP());
    Serial.println("Ready");
  }
  else
  {
    FADE(Colors::black, 1000, Colors::red, pixels, 0, true)
    Serial.println("Failed!");
  }
  
  FADE(Colors::black, 1000, Colors::red+Colors::blue, pixels, 0, true)
  if(!accel.begin())
  {
    Serial.println("Ooops, no ADXL345 detected ... Check your wiring!");
    while(1);
  }
  
  server.on("/", handleRoot);
  server.on("/red", handleRed);
  server.on("/green", handleGreen);
  server.on("/blue", handleBlue);
  server.on("/off", handleOff);
  server.on("/white", handleWhite);
  server.onNotFound(handleNotFound);

  server.begin();
}

sensors_event_t event;

void loop() {
  FADE(Colors::black, 50, (Colors::red + Colors::green) * .1f, pixels, 0, true)

  accel.getEvent(&event);
//  Serial.print("x: "); Serial.print(event.acceleration.x); Serial.print("  ");
//  Serial.print("y: "); Serial.print(event.acceleration.y); Serial.print("  ");
//  Serial.print("z: "); Serial.print(event.acceleration.z); Serial.print("  ");

//  Serial.print("IP: "); Serial.print(WiFi.localIP());
  server.handleClient();

//  Serial.println();
}

void handleRoot() {
  FADE(Colors::black, 500, Colors::blue, pixels, 0, true)
  server.send(200, "text/plain", "(x: " + String(event.acceleration.x, 4) + ", y: " + String(event.acceleration.y, 4) + ", z: " + String(event.acceleration.z, 4) + ")");
}

void handleRed() {
  Colors::red.put(pixels, 1);
  pixels.show();
  server.send(200, "text/plain", "Showing red");
}

void handleGreen() {
  Colors::green.put(pixels, 1);
  pixels.show();
  server.send(200, "text/plain", "Showing green");
}

void handleBlue() {
  Colors::blue.put(pixels, 1);
  pixels.show();
  server.send(200, "text/plain", "Showing blue");
}

void handleOff() {
  Colors::black.put(pixels, 1);
  pixels.show();
  server.send(200, "text/plain", "Showing nothing");
}

void handleWhite() {
  Colors::white.put(pixels, 1);
  pixels.show();
  server.send(200, "text/plain", "Showing white");
}

void handleNotFound(){
  FADE(Colors::black, 500, Colors::red, pixels, 0, true)
  server.send(404, "text/plain", "404: Not found");
}
