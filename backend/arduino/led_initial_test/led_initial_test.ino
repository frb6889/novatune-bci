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
    for (int idx = 0; idx<=NUM_LEDS; idx++) {
      strip.setPixelColor(idx, strip.Color(255, 255, 255));
    }
    strip.show();
    
}

