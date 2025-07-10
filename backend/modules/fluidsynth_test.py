import fluidsynth
import time

fs = fluidsynth.Synth()
fs.start(driver="coreaudio")

sfid = fs.sfload("../assets/FluidR3_GM.sf2")
fs.program_select(0, sfid, 0, 0)  # ← 加这一句！

note_seq = [
    [60, 127, 2000],  # C4
    [62, 127, 2000],  # D4
    [64, 127, 2000],  # E4
    [60, 127, 2000]   # C4
]

for note in note_seq:
    fs.noteon(0, note[0], note[1])
    time.sleep(note[2] / 1000.0)
    fs.noteoff(0, note[0])

fs.delete()
