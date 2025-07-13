#include <Adafruit_NeoPixel.h>

#define PIN        6 
#define NUM_LEDS  51    // 灯数

Adafruit_NeoPixel strip(NUM_LEDS, PIN, NEO_GRB + NEO_KHZ800);


void setup() {
  strip.begin();
  strip.show();

  
}

void loop() {
  strip.clear();
    for (int idx = 0; idx<=20; idx++) {
      strip.setPixelColor(idx, strip.Color(255, 255, 255));
    }
    for (int idx = 21; idx<=30; idx++) {
      strip.setPixelColor(idx, strip.Color(255, 0, 0));
    }
    for (int idx = 31; idx<=40; idx++) {
      strip.setPixelColor(idx, strip.Color(0, 255, 0));
    }
    for (int idx = 41; idx<=50; idx++) {
      strip.setPixelColor(idx, strip.Color(0, 0, 255));
    }
    strip.show();
    
}

