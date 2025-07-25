#include <Servo.h>
#define NUM_MOTORS 4
#define MODE_STOP 6
#define MODE_PID 7
#define MODE_SEQ 8
#define MODE_PLAY 9
#define MODE_PLAY_CUSTOM 10

Servo myServos[NUM_MOTORS]; 
int initial_pos[NUM_MOTORS] = {60, 10, 70, 10};
int target_pos[NUM_MOTORS]  = {initial_pos[0], initial_pos[1], initial_pos[2], initial_pos[3]};
int current_pos[NUM_MOTORS] = {initial_pos[0], initial_pos[1], initial_pos[2], initial_pos[3]};
int prev_error[NUM_MOTORS]  = {0, 0, 0, 0};
int int_error[NUM_MOTORS]   = {0, 0, 0, 0};

int mode = 6;  
int step = 0;

////////////////////////////////////// PID controller //////////////////////////////////////
// We're doing open-loop control, we don't have any feedback on current finger position
// Control variable : angular position (degs°) Target variable : angular position (degs°)
float Kp = 2.5; // Proportional factor
float Kd = 1; // Derivative factor
float Ki = 0.0000; // Integral factor 0.0001 before
float deadzone = 5; // choose either P-controller with deadzone or PI-controller without
bool deadzone_on = true;
float control = 0;
int noteIndex = 0;
unsigned long lastActionTime = 0;
String noteSequence = "1234";
unsigned long noteInterval = 1000; 
bool shouldPlayCustom = false;

void pControlServo(Servo &servo, int &current_pos, int target_pos, int &prev_error, int &int_error, bool deadzone_on = true) { 
  float error = target_pos - current_pos;
  if (abs(current_pos - target_pos) < 1) { return; } 
  if (deadzone_on == true) {if (abs(error) < deadzone) { return; }} 
  float derivative = error - prev_error;
  int_error += error;
  int_error = constrain(int_error, -50, 50); // avoid windup 
  control = Kp * error + Kd * derivative + Ki * int_error; // PID control
  control = constrain(control, -2, 2); 
  current_pos += control;
  current_pos = constrain(current_pos, 0, 180); // Constrain to servo range (0–180)
  prev_error = error;
  servo.write((int)current_pos);
  delay(10);
}

void playNotes(String sequence) {
  if (noteIndex >= sequence.length()) return;
  if (millis() - lastActionTime >= noteInterval) {
    char note = sequence.charAt(noteIndex);
    noteIndex++;
    lastActionTime = millis();
    switch (note) {
      case '0': playMotor(0); break;
      case '1': playMotor(1); break;
      case '2': playMotor(2); break;
      case '3': playMotor(3); break;
      case '9': delay(2000); // wait 2 seconds for each pause
      default: break;
    }
  }
}

void playMotor(int i) { // close then open each finger
  if (i < 0 || i >= NUM_MOTORS) return;
  target_pos[i] = initial_pos[i] + 90;
  while (abs(current_pos[i] - target_pos[i]) > deadzone) {
    pControlServo(myServos[i], current_pos[i], target_pos[i], prev_error[i], int_error[i], deadzone_on);
  } delay(600);
  target_pos[i] = initial_pos[i];
  while (abs(current_pos[i] - target_pos[i]) > deadzone) {
    pControlServo(myServos[i], current_pos[i], target_pos[i], prev_error[i], int_error[i], deadzone_on);
  } delay(600);
}

void setup() {  // Start serial communication & move them to their initial positions
  Serial.begin(9600);
  myServos[0].attach(2);  myServos[0].write(initial_pos[0]);
  myServos[1].attach(6);  myServos[1].write(initial_pos[1]);
  myServos[2].attach(4);  myServos[2].write(initial_pos[2]);
  myServos[3].attach(3);  myServos[3].write(initial_pos[3]);
  delay(500);
  Serial.println("Select mode: 6=MODE_STOP, 7=MODE_PID, 8=MODE_SEQ, 9=MODE_PLAY");
}

void loop() {
  if (Serial.available()) { 
    int incoming = Serial.parseInt(); 
    if (incoming == MODE_STOP || incoming == MODE_PID || incoming == MODE_SEQ || incoming == MODE_PLAY || incoming == MODE_PLAY_CUSTOM) { // mode 6 : Stop, mode 7: PID, mode 8: Sequential, mode 9: Song, mode 10: Custom melody
      mode = incoming;
      Serial.print("Selected mode: "); Serial.println(mode); return;} 
    if (mode == MODE_PID) { 
      Serial.println("PID control mode active. Input motor & target (ex: 1 110).");
      String inputLine = "";
      while (inputLine.length() == 0) {
        if (Serial.available()) {
          inputLine = Serial.readStringUntil('\n'); inputLine.trim();
        }
      }
      int servoId = -1; int target = -1; 
      int n = sscanf(inputLine.c_str(), "%d %d", &servoId, &target);
      target = constrain(target, 0, 180); 
      if (n==2) {
        switch (servoId) {
          case 1: target_pos[0] = target; break;
          case 2: target_pos[1] = target; break;
          case 3: target_pos[2] = target; break;
          case 4: target_pos[3] = target; break;
        }
      }
    }
    if (mode == MODE_PLAY_CUSTOM) { 
      Serial.println("Custom melody mode active, please input the desired melody:");
      String inputLine = "";
      while (inputLine.length() == 0) {
        if (Serial.available()) {
          inputLine = Serial.readStringUntil('\n');
          inputLine.trim();
        }
      }
      noteSequence = inputLine;
      noteIndex = 0;
      lastActionTime = millis();
      shouldPlayCustom = true;
    }
  }
  if (mode == MODE_STOP || mode == MODE_PID || mode == MODE_PLAY || mode == MODE_PLAY_CUSTOM) {
    step = 0; 
  }
  if (mode == MODE_STOP) { 
    myServos[0].write(initial_pos[0]); myServos[1].write(initial_pos[1]); myServos[2].write(initial_pos[2]); myServos[3].write(initial_pos[3]);
  } 
  else if (mode == MODE_PID) {
    pControlServo(myServos[0], current_pos[0], target_pos[0], prev_error[0], int_error[0], deadzone_on);
    pControlServo(myServos[1], current_pos[1], target_pos[1], prev_error[1], int_error[1], deadzone_on);
    pControlServo(myServos[2], current_pos[2], target_pos[2], prev_error[2], int_error[2], deadzone_on);
    pControlServo(myServos[3], current_pos[3], target_pos[3], prev_error[3], int_error[3], deadzone_on);
  }
  else if (mode == MODE_SEQ) {
    noteSequence = "0123"; // 0; re, 1: mi, 2: fa, 3: sol
    playNotes(noteSequence);
  }

  else if (mode == MODE_PLAY) { // Prerecorded melody
    // 1123321099011900112332109912199 - mi mi fa sol sol fa mi re do do re mi mi re re mi mi fa sol sol fa mi re do do re mi re do do
    noteSequence = "1123321099011900112332109912199"; // 0; re, 1: mi, 2: fa, 3: sol, 9: pause
    playNotes(noteSequence);
  }
  else if (mode == MODE_PLAY_CUSTOM && shouldPlayCustom) {
    playNotes(noteSequence);
    if (noteIndex >= noteSequence.length()) {
      shouldPlayCustom = false;
      Serial.println("Custom melody complete.");
    }
  }
  ////////////////////////////////////// Plotting //////////////////////////////////////
  /* Serial.print("S1:"); Serial.print(current_pos[0]);
  Serial.print(" S2:"); Serial.print(current_pos[1]);
  Serial.print(" S3:"); Serial.print(current_pos[2]);
  Serial.print(" S4:"); Serial.println(current_pos[3]); */
}


