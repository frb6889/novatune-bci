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
      if(brightness == 0){
        strip.setPixelColor(idx, strip.Color(0, 0, 0));
        strip.show();
      }else if (brightness == -1){
        // 渐变效果：三个值在1s内从0渐变到255
        int steps = 50;
        int delayTime = 1000 / steps; // 总时长1000ms = 1s

        for (int i = 0; i <= steps; i++) {
          int level = map(i, 0, steps, 0, 255);
          strip.setPixelColor(idx, strip.Color(level, level, level)); 
          strip.show();
          delay(delayTime); 
        }
      }else{
        strip.setPixelColor(idx, strip.Color(brightness, brightness, brightness));
        strip.show();
      }
    }
    Serial.readStringUntil('\n');
  }
}
