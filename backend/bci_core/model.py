import numpy as np

from scipy import signal
from pyriemann.estimation import BlockCovariances
from pyriemann.tangentspace import TangentSpace
from pyriemann.preprocessing import Whitening
from sklearn.pipeline import make_pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from mne.decoding import Vectorizer, CSP


class DecimateFeature(BaseEstimator, TransformerMixin):
    """DecimateFeature 类用于对信号进行降采样以达到目标采样频率。"""
    def __init__(self, fs, target_fs=10, axis=-1):
        """初始化函数，设置原始采样频率 fs，目标采样频率 target_fs，以及降采样操作的轴 axis。"""
        self.fs = fs
        self.target_fs = target_fs
        self.axis = axis

    def fit(self, X, y=None):
        return self
    
    def transform(self, X, y=None):
        """
        对输入数据 X 进行两次降采样操作，以达到目标采样频率。
        使用 scipy.signal.decimate 方法进行降采样，采用零相位滤波以减少延迟。
        """
        decimate_rate = np.sqrt(self.fs / self.target_fs).astype(np.int16)
        X = signal.decimate(X, decimate_rate, axis=self.axis, zero_phase=True)
        # to 10Hz
        X = signal.decimate(X, decimate_rate, axis=self.axis, zero_phase=True)
        return X


class ChannelScaler(BaseEstimator, TransformerMixin):
    """
    ChannelScaler 类用于对信号的每个通道进行标准化处理。
    """
    def __init__(self, norm_axis=(0, 2)):
        self.channel_mean_ = None
        self.channel_std_ = None
        self.norm_axis=norm_axis

    def fit(self, X, y=None):
        '''

        :param X: 3d array with shape (n_epochs, n_channels, n_times)
        :param y:
        :return:
        '''
        self.channel_mean_ = np.mean(X, axis=self.norm_axis, keepdims=True)
        self.channel_std_ = np.std(X, axis=self.norm_axis, keepdims=True)
        return self

    def transform(self, X, y=None):
        X = X.copy()
        X -= self.channel_mean_
        X /= self.channel_std_
        return X


def riemann_feature_embedder(feat_dim, estimator='lwf'):
    """
    创建一个特征嵌入管道，利用 Riemann 几何方法进行特征提取和转换。

    参数 feat_dim 定义每个数据块的大小，estimator 选择协方差矩阵的估计方法。
    管道包括通道标准化、块协方差矩阵计算、白化处理以及切换到切线空间的步骤。
    """
    return make_pipeline(
        ChannelScaler(),  # not necessary
        BlockCovariances(block_size=feat_dim, estimator=estimator),
        Whitening(metric='riemann', dim_red={'expl_var': 0.99}),
        TangentSpace()
    )


def baseline_feature_embedder(fs, target_fs, axis):
    """
    创建一个基线特征嵌入管道，主要用于降采样和通道标准化。

    参数 fs, target_fs, axis 分别为原始采样频率、目标采样频率和降采样操作的轴。
    管道包括降采样、通道标准化和向量化处理的步骤。
    """
    return make_pipeline(
        DecimateFeature(fs, target_fs, axis),
        ChannelScaler(),
        Vectorizer()
    )


def cps_feature_embedder(n_chs):
    return make_pipeline(
        ChannelScaler(),
        CSP(n_chs, reg='ledoit_wolf', log=True)
    )
