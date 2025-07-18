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
    //is_gradiant: 1 为渐变，0 为不渐变，-1为
    int is_gradiant = Serial.parseInt();

    int old_r = Serial.parseInt();
    int old_g = Serial.parseInt();
    int old_b = Serial.parseInt();

    int new_r = Serial.parseInt();
    int new_g = Serial.parseInt();
    int new_b = Serial.parseInt();



    if (idx >= 0 && idx < NUM_LEDS) {
      if (is_gradiant == -1){
        // 渐变效果：三个值在1s内从0渐变到255
        int steps = 50;
        int delayTime = 1000 / steps; // 总时长1000ms = 1s

        for (int i = 0; i <= steps; i++) {
          int level_r = map(i, 0, steps, 0, 100);
          int level_g = map(i, 0, steps, 0, 255);

          strip.setPixelColor(idx, strip.Color(level_r, level_g, 0)); 
          strip.show();
          delay(delayTime); 
        }
      }else if(is_gradiant == 1){
        int steps = 50;
        int delayTime = 3000 / steps;

        for (int i = 0; i <= steps; i++) {
          int level_r = map(i, 0, steps, old_r, new_r);
          int level_g = map(i, 0, steps, old_g, new_g);
          int level_b = map(i, 0, steps, old_b, new_b);
          strip.setPixelColor(idx, strip.Color(level_r, level_g, level_b)); 
          strip.show();
          delay(delayTime); 
        }
      }else if(is_gradiant == 0){
        strip.setPixelColor(idx, strip.Color(0, 0, 0)); 
        strip.show();
      }
    }
    Serial.readStringUntil('\n');
  }
}
