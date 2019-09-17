#include <Adafruit_NeoPixel.h>
#include <LightShow.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include "Colors.h"

#define ABS(x) ((x)>0?(x):-(x))

float mapfloat(float x, float in_min, float in_max, float out_min, float out_max)
{
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

#define LED 2
#define COUNT 2

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(COUNT, LED, NEO_RGB + NEO_KHZ800);
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);

#define FEEDBACK_DUR 1000

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
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::green, pixels, 0, true)
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::green, pixels, 0, true)
    break;
    case 1:
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::green + Colors::red, pixels, 0, true)
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::green + Colors::red, pixels, 0, true)
    break;
    case 2:
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::red, pixels, 0, true)
      FADE(Colors::black, FEEDBACK_DUR/10, Colors::red, pixels, 0, true)
    break;
    default:
    break;
  }
}

void feedback(byte severity, byte d0=0, byte d1=0, byte d2=0) {
  feedback_severity(severity);
  feedback_digit(d0);
  feedback_digit(d1);
  feedback_digit(d2);
  feedback_severity(severity);
  Colors::black.putAll(pixels, COUNT);
  pixels.show();
  delay(FEEDBACK_DUR);
}

//feedbacks table
#define IDLE 0

#define SENSOR_OK 0, 1
#define SENSOR_INIT_ERROR 2, 1

#define PIXELS_OK 0, 2

#define BEFORE_DETECT 1, 1, 1
#define DURING_DETECT 1, 1, 2
#define AFTER_DETECT 0, 1, 1
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
  for (uint8_t i = 0; i < 20; i++) {
    feedback(BEFORE_DETECT);
  }

  float sumX = 0;
  float sumY = 0;
  float sumZ = 0;
  for (uint8_t i = 0; i < 20; i++) {
    sensors_event_t event; 
    accel.getEvent(&event);
    sumX += mapfloat(event.acceleration.x, -14.08, 6.39, -1.0, 1.0);
    sumY += mapfloat(event.acceleration.y, -12.63, 7.41, -1.0, 1.0);
    sumZ += mapfloat(event.acceleration.z, -1.69, 20.04, -1.0, 1.0);
    feedback(DURING_DETECT);
  }
  baseX = sumX / 20.0;
  baseY = sumY / 20.0;
  baseZ = sumZ / 20.0;
  feedback(AFTER_DETECT);
}

void init_pixels() {
  pixels.begin();
  pixels.setBrightness(255);
  Colors::black.putAll(pixels, COUNT);
  pixels.show();
  feedback(PIXELS_OK);
  Serial.println("pixels init done");
}

void setup() {
  delay(1000);
  randomSeed(analogRead(0));
  Serial.begin(9600);
  init_pixels();
  init_sensor(); 

  detect_rest_position();
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
