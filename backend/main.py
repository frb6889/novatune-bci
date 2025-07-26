# python midi_glove.py
import os
import sys
import csv
import mido
import pygame
import time
import serial
import random
from datetime import datetime

sys.path += [
    os.path.join(os.path.dirname(os.path.abspath(__file__))),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trainer'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
]


from trainer.training_config import TrainingConfig
from trainer.training_env import TrainingEnv
from trainer.training_loop import TrainingLoop
from logger import save_midi_log

def main():
    # 初始化
    trainingconfig = TrainingConfig()
    env = TrainingEnv(trainingconfig)
    app = TrainingLoop(env)

    # 运行主循环
    records = app.run()

    # 退出并保存日志
    save_midi_log(records)
    env.midi.close()
    pygame.quit()

if __name__ == "__main__":
    main()



