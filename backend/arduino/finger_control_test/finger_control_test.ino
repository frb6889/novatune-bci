#include <Servo.h>

Servo myServo1, myServo2, myServo3, myServo4;

int initial_pos1 = 40, initial_pos2 = 45, initial_pos3 = 70, initial_pos4 = 10;

int mode = 4;  // 默认是接收 Serial 的模式

void sweepServo(Servo &servo, int initial_pos) {
  for (int pos = initial_pos; pos <= initial_pos + 145; pos += 1) {
    servo.write(pos);
    delay(10);
  }
  delay(50);

  for (int pos = initial_pos + 145; pos >= initial_pos; pos -= 1) {
    servo.write(pos);
    delay(10);
  }
  delay(50);
}

void setup() {
  Serial.begin(9600);

  myServo1.attach(2);
  myServo1.write(initial_pos1);

  myServo2.attach(6);
  myServo2.write(initial_pos2);

  myServo3.attach(4);
  myServo3.write(initial_pos3);

  myServo4.attach(3);
  myServo4.write(initial_pos4);

  delay(500);
  
  Serial.println("请输入模式：4=调试、5=顺序、6=Serial MIDI");
}

void loop() {
  if (Serial.available()) {
    int incoming = Serial.parseInt();

    // 切换模式
    if (incoming == 4 || incoming == 5 || incoming == 6) {
      mode = incoming;
      Serial.print("已切换至模式 ");
      Serial.println(mode);
      return;
    }

    if (mode == 4) {
      // 调试模式：通过串口设置 initial pos
      Serial.println("输入格式：编号 位置（如：1 20 表示设置servo1起始位置为20）");
      while (Serial.available() < 2); // 等待两个数字
      int servoId = Serial.parseInt();
      int newPos = Serial.parseInt();
      switch (servoId) {
        case 1: initial_pos1 = newPos; myServo1.write(initial_pos1); break;
        case 2: initial_pos2 = newPos; myServo2.write(initial_pos2); break;
        case 3: initial_pos3 = newPos; myServo3.write(initial_pos3); break;
        case 4: initial_pos4 = newPos; myServo4.write(initial_pos4); break;
        default: Serial.println("无效的编号"); return;
      }
      Serial.print("设置完成：servo");
      Serial.print(servoId);
      Serial.print(" 初始位置 = ");
      Serial.println(newPos);
    }
    else if (mode == 5) {
      // 顺序控制
      Serial.print("目前的初始值分别是：");
      Serial.print(initial_pos1); //40 
      Serial.print(" ");
      Serial.print(initial_pos2); //45
      Serial.print(" ");
      Serial.print(initial_pos3); //70
      Serial.print(" ");
      Serial.print(initial_pos4); //15

      sweepServo(myServo1, initial_pos1);
      sweepServo(myServo2, initial_pos2);
      sweepServo(myServo3, initial_pos3);
      sweepServo(myServo4, initial_pos4);
    }
    else if (mode == 6) {
      // MIDI 控制
      switch (incoming) {
        case 62: sweepServo(myServo1, initial_pos1); break;
        case 64: sweepServo(myServo2, initial_pos2); break;
        case 65: sweepServo(myServo3, initial_pos3); break;
        case 67: sweepServo(myServo4, initial_pos4); break;
        default: Serial.print("未绑定的MIDI值："); Serial.println(incoming);
      }
    }
  }
}
