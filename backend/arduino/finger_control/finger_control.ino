#include <Servo.h>

Servo myServo1, myServo2, myServo3, myServo4;

const int initial_pos1 = 0, initial_pos2 = 0, initial_pos3 = 0, initial_pos4 = 0;

void sweepServo(Servo &servo, int initial_pos) {
  // 从当前 0 转到 180
  for (int pos = initial_pos; pos <= initial_pos+150; pos += 1) {
    servo.write(pos);
    delay(10);
  }
  delay(50); // 稍作等待

  // 从 180 回到 0
  for (int pos = initial_pos+150; pos >= initial_pos; pos -= 1) {
    servo.write(pos);
    delay(10);
  }
  delay(50);
}

void setup() {
  Serial.begin(9700);

  //2 1。   3 4。    4 3。  6 2。
  myServo1.attach(2);
  myServo1.write(0);

  myServo2.attach(6);
  myServo2.write(0);

  myServo3.attach(4);
  myServo3.write(0);
  
  myServo4.attach(3);
  myServo4.write(0);

  delay(500); // 稍等所有舵机就绪并停在 0°

  // 依次控制
  
  /* sweepServo(myServo1);
  sweepServo(myServo2);
  sweepServo(myServo3);
  sweepServo(myServo4); */
}

void loop() {
  //针对do re mi fa训练场景
  if (Serial.available()) {
    int idx = Serial.parseInt();
    if(idx == 60){
      sweepServo(myServo1,initial_pos1);
    }else if(idx==62){
      sweepServo(myServo2,initial_pos2);
    }else if(idx==64){
      sweepServo(myServo3,initial_pos3);
    }else if(idx==65){
      sweepServo(myServo4,initial_pos4);
    }
  }
  
}
