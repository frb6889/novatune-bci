import mido

# 准备：获取midi ports名称
print("Available MIDI input ports:")
print(mido.get_input_names())

print("Available MIDI output ports:")
print(mido.get_output_names())

# 
midi_input_name = 'Vboard 49' # 替换成实际设备名称

with mido.open_input(midi_input_name) as inport:
    print("Listening for MIDI messages...")
    for msg in inport:
        print(msg)  # 打印接收到的 MIDI 消息

        """  
        消息示例：
        中央C：
        note_on channel=0 note=60 velocity=18 time=0
        note_off channel=0 note=60 velocity=0 time=0
        D：
        note_on channel=0 note=62 velocity=8 time=0
        note_off channel=0 note=62 velocity=0 time=0
        E：
        note_on channel=0 note=64 velocity=8 time=0
        note_off channel=0 note=64 velocity=0 time=0
        """