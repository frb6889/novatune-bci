import numpy as np
import time
from IPython.display import clear_output
import scipy.signal as signal
import mne
import matplotlib.pyplot as plt
from IPython.display import display, clear_output
import time
from settings.config import Settings
from device.data_client import NeuracleDataClient

config_info = Settings.CONFIG_INFO
# get data
config_info['buffer_length'] = 1
receiver = NeuracleDataClient(n_channel=len(config_info['channel_labels']),
                    samplerate=config_info['sample_rate'], 
                    host=config_info['host'],
                    port=config_info['port'],
                    buffer_len=config_info['buffer_length'])
time.sleep(6.0)
# functions getting data
def _parse_data(data):
    fs, event, data_array = data
    # do preprocessing
#     data_array = reref(data_array, self.reref_method)
    return fs, event, data_array

# 模拟数据生成函数（用于离线测试）
def generate_random_ecog_data(n_channels=8, n_samples=1000):
    """生成随机EEG数据模拟在线获取"""
    return np.random.randn(n_channels, n_samples) * 100  # 8通道×1000时间点

# 滤波函数
def bandpass_filter(data, lowcut=1, highcut=300, fs=1000):
    nyq = 0.5 * fs  # 奈奎斯特频率
    low = lowcut / nyq
    high = highcut / nyq
    order = 4  # 滤波器阶数
    b, a = signal.butter(order, [low, high], btype='band')
    return signal.filtfilt(b, a, data)


# 主循环
def main_loop(interval=1.0):
    """主循环函数，interval为更新间隔(秒)"""
    try:
        while True:
            # 模拟在线获取数据（实际使用时替换为你的真实数据获取代码）
            # data = generate_random_ecog_data()

            # 真实的ECoG数据处理
            data_from_buffer= receiver.get_trial_data(clear=True)
            fs, event, data = _parse_data(data_from_buffer)

            
            # 滤波处理
            data_highGM = bandpass_filter(data, lowcut=60, highcut=200)
            
            # 计算high-gamma频带能量
            energy = np.sum(data_highGM ** 2, axis=1)  # 向量化计算
            
            # 清屏并打印结果
            clear_output(wait=True)
            print(f"更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("8个通道的高频gamma能量分别是: ")
            print("+" + "-"*30 + "+")
            print("|  通道  |     能量值     |")
            print("+" + "-"*30 + "+")
            for ch in range(8):
                print(f"|  {ch+1:2d}   |  {energy[ch]}  |")
            print("+" + "-"*30 + "+")
            print(f"下次更新将在{interval}秒后... (按Ctrl+C停止)")
            
            # 等待指定间隔
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n实时监控已停止")

if __name__ == "__main__":
    print("开始高频gamma能量实时监控...")
    main_loop(interval=1.0)  # 1秒更新一次