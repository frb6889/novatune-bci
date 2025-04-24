import mido

class MIDIHandler:
    def __init__(self):
        names = mido.get_input_names()
        if not names:
            print("MIDI device not found ㅠㅠ")
            self.device = None
            self.port = None
            return
        
        self.device = names[0]
        self.port = mido.open_input(self.device)
        print(f"listening to target MIDI device: {self.device}")
    
    def poll_all(self):
        return self.port.iter_pending()
    def close(self):
        self.port.close()