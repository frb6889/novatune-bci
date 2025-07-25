import serial

class ServoController:
    def __init__(self, port, baudrate = 9700, timeout = 0.1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.first_call = True # mark if this is the first time

    def set_servo(self, idx):
        mapping = {
            62:0,
            64:1,
            65:2,
            67:3
        }
        if idx in mapping:
            # print(f"into set_servo!{idx}mapping to {mapping[idx]},servo id is {mapping[idx]+1}")
            mapped_idx = mapping[idx]
            cmd = f"{mapped_idx}\n"
            self.ser.write(cmd.encode())
            
        elif idx == 5:
            # print("servo reset input received!")
            self.ser.write(" ".encode())
        else:
            print(f"Invalid input: {idx} is not in the note mapping")
