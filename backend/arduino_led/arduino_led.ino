#define LED1 2  // 对应音符 60
#define LED2 3  // 对应音符 62
#define LED3 4  // 对应音符 64
#define LED4 5  // 对应音符 65
#define LED5 6  // 对应音符 67

void setup() {
  Serial.begin(9600);
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);
  pinMode(LED4, OUTPUT);
  pinMode(LED5, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    int note = Serial.parseInt();  // 读取 MIDI 音符
    Serial.println(note);  // 输出调试信息

    // 关闭所有灯
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);
    digitalWrite(LED3, LOW);
    digitalWrite(LED4, LOW);
    digitalWrite(LED5, LOW);

    // 点亮对应音符的灯
    switch (note) {
      case 60: digitalWrite(LED1, HIGH); break;
      case 62: digitalWrite(LED2, HIGH); break;
      case 64: digitalWrite(LED3, HIGH); break;
      case 65: digitalWrite(LED4, HIGH); break;
      case 67: digitalWrite(LED5, HIGH); break;
    }
  }
}
