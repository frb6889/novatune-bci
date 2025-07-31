import joblib
import numpy as np
import random
import logging
import os
from scipy import signal
from .utils import parse_model_type, reref
from .pipeline import data_evaluation


logger = logging.getLogger(__name__)


class Controller:
    """在线控制接口
    运行时主要调用decision方法，
    每次气动手反馈后调用reset_buffer方法，用以跳过气动手不应期
    Args:
        virtual_feedback_rate (float): 0-1之间浮点数，控制假反馈占比
        model_path (string): 模型文件路径
        buffer_steps (int): 
    """
    def __init__(self,
                 virtual_feedback_rate=1., 
                 real_feedback_model=None,
                 reref_method='monopolar'):
        
        self.real_feedback_model = real_feedback_model
        self.virtual_feedback_rate = virtual_feedback_rate
        self.reref_method = reref_method

    def step_decision(self, data, true_label=None):
        """抓握训练调用接口，只进行单次判决，不涉及马尔可夫过程，
        假反馈的错误反馈默认输出为10000
        Args: 
            data (mne.io.RawArray): 数据
            true_label (None or int): 训练时假反馈的真实标签
        Return:
            int: 统一化标签 (-1: keep, 0: rest, 1: cylinder, 2: ball, 3: flex, 4: double, 5: treble)
        """
        virtual_feedback = self.virtual_feedback(true_label)
        logger.debug('step_decision: virtual feedback: {}'.format(virtual_feedback))
        if virtual_feedback is not None:
            return virtual_feedback

        if self.real_feedback_model is not None:
            fs, data = self.parse_data(data)
            p = self.real_feedback_model.step_probability(fs, data)
            logger.debug('step_decison: model probability: {}'.format(str(p)))
            pred = np.argmax(p)
            real_decision = self.real_feedback_model.model.classes_[pred]
            return real_decision
        else:
            raise ValueError('Neither decision model nor true label are given')
    
    def decision(self, data, true_label=None):
        """决策主要方法，输出逻辑如下：
            如果有决策模型，无论是否有true_label，都会使用模型进行一步决策计算并填入buffer（不一定返回）

            如果有true_label（训练模式），产生一个随机数确定本trial是否为假反馈，
                是假反馈，产生一个随机数确定本trial产生正确or错误的假反馈，假反馈的标签为10000
                不是假反馈，使用模型决策
            如果没有true_label（测试模式），直接使用模型决策

            模型决策逻辑：
                根据模型记录的last_state，
                    如果当前state和last_state相同，输出-1
                    如果当前state和last_state不同，输出当前state

        Args: 
            data (mne.io.RawArray): 数据
            true_label (None or int): 训练时假反馈的真实标签
        Return:
            int: 统一化标签 (-1: keep, 0: rest, 1: cylinder, 2: ball, 3: flex, 4: double, 5: treble)
        """
        if self.real_feedback_model is not None:
            fs, data = self.parse_data(data)
            real_decision = self.real_feedback_model.viterbi(fs, data)
            # map to unified label
            if real_decision != -1:
                real_decision = self.real_feedback_model.model.classes_[real_decision]
        
        virtual_feedback = self.virtual_feedback(true_label)
        if virtual_feedback is not None:
            return virtual_feedback
        
        # true_label is None or not running virtual feedback in this trial
        # if no real model, raise ValueError
        if self.real_feedback_model is None:
            raise ValueError('Neither decision model nor true label are given')
        return real_decision

    def virtual_feedback(self, true_label=None):
        if true_label is not None:
            p = random.random()
            if p < self.virtual_feedback_rate:  # virtual feedback (error rate 0.2)
                p_correct = random.random()
                if p_correct < 0.8:
                    return true_label
                else:
                    return 10000
        return None
    
    def parse_data(self, data):
        fs, event, data_array = data
        # do preprocessing
        data_array = reref(data_array, self.reref_method)
        return fs, data_array


class HMMModel:
    """HMMModel 是一个基于隐马尔可夫模型（Hidden Markov Model, HMM）的框架，用于建模状态转移和更新。"""
    def __init__(self, 
                 transmat=None, 
                 n_classes=2, 
                 state_trans_prob=0.6, 
                 state_change_threshold=0.5,
                 momentum=0.5):
        """
        初始化HMM模型。
            transmat: 状态转移矩阵，如果为 None，则自动生成一个简单的转移矩阵。
            n_classes: 状态的数量。
            state_trans_prob: 状态保持不变的概率。
            state_change_threshold: 状态改变的阈值。
            momentum: 用于更新状态概率的动量因子。
        """
        self.n_classes = n_classes
        self.set_current_state(0)

        self.state_change_threshold = state_change_threshold

        if transmat is None:
            # build state transition matrix
            self.state_trans_matrix = np.zeros((n_classes, n_classes))
            # fill diagonal
            np.fill_diagonal(self.state_trans_matrix, state_trans_prob)
            # fill 0 -> each state, 
            self.state_trans_matrix[0, 1:] = (1 - state_trans_prob) / (n_classes - 1)
            self.state_trans_matrix[1:, 0] = 1 - state_trans_prob
        else:
            if isinstance(transmat, str):
                transmat = np.loadtxt(transmat)
            self.state_trans_matrix = transmat

        # momentum factor
        self.momentum = momentum
    
    def set_current_state(self, current_state):
        self._last_state = current_state
        self._probability = np.zeros(self.n_classes)
        self._probability[current_state] = 1.
    
    def step_probability(self, fs, data):
        raise NotImplementedError
    
    def viterbi(self, fs, data, return_step_p=False):
        """
            Interface for class decision

        """
        p = self.step_probability(fs, data)
        if return_step_p:
            return p, self.update_state(p)
        else:
            return self.update_state(p)
    
    def update_state(self, current_p):
        # veterbi algorithm
        prob = (self.state_trans_matrix * self._probability.T).sum(axis=1) * current_p
        # normalize
        prob /= np.sum(prob)
        # momentum
        self._probability = self.momentum * self._probability + (1 - self.momentum) * prob

        logger.debug("viterbi probability, {}".format(str(self._probability)))

        current_state = np.argmax(self._probability)
        if current_state == self._last_state:
            return -1
        else:
            if self._probability[current_state] > self.state_change_threshold:
                self.set_current_state(current_state)
                return current_state
            else:
                return -1
    
    @property
    def probability(self):
        return self._probability.copy()


class ClfEmissionHMM(HMMModel):
    """
    ClfEmissionHMM 则是 HMMModel 的一个扩展，结合了分类模型的输出作为HMM的发射概率。
    """
    def __init__(self, model, **kwargs):
        """
        初始化分类器发射的HMM模型。
            model: 包含特征提取器、嵌入器和分类模型的元组或模型文件路径。
        """
        if isinstance(model, str):
            model = joblib.load(model)
        self.feat_extractor, self.embedder, self.model = model

        super(ClfEmissionHMM, self).__init__(n_classes=len(self.model.classes_), **kwargs)
    
    def step_probability(self, fs, data):
        p = data_evaluation([self.feat_extractor, self.embedder, self.model], data, fs, None, None, False).squeeze()
        return p


def model_loader(model_path, **kwargs):
    """
    模型如果存在训练好的transmat，会直接load
    """
    model_root, model_filename = os.path.dirname(model_path), os.path.basename(model_path)
    model_name = model_filename.split('.')[0]
    transmat_path = os.path.join(model_root, model_name + '_transmat.txt')
    if os.path.isfile(transmat_path):
        transmat = np.loadtxt(transmat_path)
    else:
        transmat = None
    kwargs['transmat'] = transmat

    return ClfEmissionHMM(model_path, **kwargs)
