#include <Adafruit_NeoPixel.h>

#define PIN        6 
#define NUM_LEDS  51    // 灯数

Adafruit_NeoPixel strip(NUM_LEDS, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  Serial.begin(9600);
  strip.begin();
  strip.show();
}

void loop() {
  if (Serial.available()) {
    int idx = Serial.parseInt();

    int brightness = Serial.parseInt();


    if (idx >= 0 && idx < NUM_LEDS) {
      strip.setPixelColor(idx, strip.Color(brightness, brightness, brightness));
      strip.show();
    }
    Serial.readStringUntil('\n');
  }
}
