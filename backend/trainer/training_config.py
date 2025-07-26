class TrainingConfig:
    def __init__(self):
        # !! Currently, only songs composed of re, mi, fa, so (62, 64, 65, 67) are supported.
        # !! Selecting "remifaso" will automatically shuffle the sequence:
        self.song_name = "remifaso"

        # Whether to play [GUIDING (indicator) SOUND] for testing
        self.play_indicate_note = True

        # Whether to connect [SERVO] for testing
        self.has_servo = False

        # Whether to connect the [TRIGGER BOX] for testing
        self.has_trigger_box = False
