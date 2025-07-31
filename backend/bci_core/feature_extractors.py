import numpy as np
from mne import filter
from mne.time_frequency import tfr_array_morlet
from scipy import signal, fftpack
from sklearn.base import BaseEstimator, TransformerMixin


class FilterbankExtractor(BaseEstimator, TransformerMixin):
    """
    用于提取滤波器组特征
    """
    def __init__(self, sfreq, filter_banks):
        """
        初始化函数接收两个参数：`sfreq` 和 `filter_banks`。
            `sfreq` 是信号的采样频率。
            `filter_banks` 是一个包含多个频率的数组，这些频率定义了要应用的滤波器组。
        """
        self.sfreq = sfreq
        self.filter_banks = filter_banks
    
    def fit(self, X, y=None):
        """
        fit 方法是为了与scikit-learn的接口兼容而定义的。在这种情况下，它不进行任何操作，只是返回实例自身。这是因为特征提取不需要训练过程。
        """
        return self
    
    def transform(self, X, y=None):
        """
        transform 方法接收输入数据 X 并使用 filterbank_extractor 函数对其进行变换，然后返回变换后的数据。
            这个方法主要用于将定义的滤波器组应用于输入数据，以提取频率特征。
        """
        return filterbank_extractor(X, self.sfreq, self.filter_banks, reshape_freqs_dim=True)


def filterbank_extractor(data, sfreq, filter_banks, reshape_freqs_dim=False):
    """
    filterbank_extractor 是一个独立的函数，负责具体的特征提取过程。
        data: 输入数据。
        sfreq: 采样频率。
        filter_banks: 定义了要提取的频率带的数组。
        reshape_freqs_dim: 一个布尔值，指定是否要重新塑形频率维度，默认为 False。   
    
    处理步骤
    1. 计算每个滤波器的周期数 n_cycles，这里简单地将 filter_banks 除以4。
    2. 使用 tfr_array_morlet 函数计算数据的时频表示。这个函数应用Morlet小波变换，用于计算指定频率的平均功率。
    3. 默认情况下，输出的功率维度是 (n_ch, n_freqs, n_times)。如果 reshape_freqs_dim 为 True，则将功率数组重塑，以便频率维度和时间维度合并。
    """
    n_cycles = filter_banks / 4
    power = tfr_array_morlet(data[None],
                            sfreq=sfreq,
                            freqs=filter_banks,
                            n_cycles=n_cycles,
                            output='avg_power',
                            verbose=False)
    # (n_ch, n_freqs, n_times)
    if reshape_freqs_dim:
        power = power.reshape((-1, power.shape[-1]))
    return power


class FeatExtractor:
    """
    FeatExtractor 是主要的特征提取器类，负责协调低频带（LFB）和高伽马（HG）频带特征的提取。
    """
    def __init__(self, sfreq, lfb_bands, hg_bands):
        """
        初始化函数，设置采样频率和特定频带的参数。
            sfreq: 信号的采样频率。
            lfb_bands: 低频带参数，如果不为None，则用于LFB特征提取。
            hg_bands: 高伽马频带参数，如果不为None，则用于HG特征提取。
        根据 lfb_bands 和 hg_bands 的值，决定是否初始化相应的特征提取器。

        """
        self.sfreq = sfreq
        self.use_lfb = lfb_bands is not None
        self.use_hgb = hg_bands is not None
        if self.use_lfb:
            self.lfb_extractor = LFPExtractor(sfreq, lfb_bands)
        if self.use_hgb:
            self.hgs_extractor = HGExtractor(sfreq, hg_bands)

    def fit(self, X, y=None):
        """为了与scikit-learn兼容而定义的方法，不进行任何操作，仅返回自身实例。"""
        return self
    
    def transform(self, X):
        """
        对输入数据 X 进行特征提取。
        如果启用了LFB或HG特征提取，则分别调用相应的提取器，并将特征数组合并。   
        """
        feature = []
        if self.use_lfb:
            feature.append(self.lfb_extractor.transform(X))
        if self.use_hgb:
            feature.append(self.hgs_extractor.transform(X))
        return np.concatenate(feature, axis=0)


class HGExtractor:
    def __init__(self, sfreq, hg_bands):
        self.sfreq = sfreq
        self.hg_bands = hg_bands

    def transform(self, data):
        """
        data: single trial data (n_ch, n_times)
        """
        hg_data = []
        for b in self.hg_bands:
            filter_signal = filter.filter_data(data, self.sfreq, l_freq=b[0], h_freq=b[1], verbose=False, n_jobs=4)
            signal_power = np.abs(fast_hilbert(data=filter_signal))
            hg_data.append(signal_power)
        hg_data = np.concatenate(hg_data, axis=0)
        return hg_data
        

def fast_hilbert(data):
    n_signal = data.shape[-1]
    fft_length = fftpack.next_fast_len(n_signal)
    pad_signal = np.zeros((*data.shape[:-1], fft_length))
    pad_signal[..., :n_signal] = data
    complex_signal = signal.hilbert(pad_signal, axis=-1)[..., :n_signal]
    return complex_signal


class LFPExtractor:
    def __init__(self, sfreq, lfb_bands):
        self.sfreq = sfreq
        self.lfb_bands = lfb_bands

    def transform(self, data):
        """
        data: single trial data (n_ch, n_times)
        """
        lfp_data = []
        for b in self.lfb_bands:
            band_data = filter.filter_data(data, self.sfreq, b[0], b[1], method='iir', phase='zero', verbose=False)
            lfp_data.append(band_data)
        lfp_data = np.concatenate(lfp_data, axis=0)
        return lfp_data