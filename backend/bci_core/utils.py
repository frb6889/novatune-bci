import numpy as np
import itertools
from datetime import datetime
import joblib
from sklearn.model_selection import KFold
from sklearn.metrics import roc_auc_score
from mne import baseline
import logging
import os

logger = logging.getLogger(__name__)


def event_to_stim_channel(events, time_length, trial_length=None, start_ind=0):
    x = np.zeros(time_length, dtype=np.int32)
    if isinstance(trial_length, dict):
        for i in range(0, len(events)):
            ind = events[i, 0] - start_ind
            x[ind:ind + trial_length[events[i, 2]]] = events[i, 2]
    elif trial_length is not None:
        for i in range(0, len(events)):
            ind = events[i, 0] - start_ind
            x[ind:ind + trial_length] = events[i, 2]
    else:
        for i in range(0, len(events) - 1):
            ind_start = events[i, 0] - start_ind
            ind_end = events[i + 1, 0] - start_ind
            x[ind_start:ind_end] = events[i, 2]
    return x


def count_transmat_by_events(events):
    y = events[:, -1]
    classes = np.unique(y)
    classes_ind = {c: i for i, c in enumerate(classes)}
    transmat_prior = np.zeros((len(classes), len(classes)))
    for i in range(len(y) - 1):
        transmat_prior[classes_ind[y[i]], classes_ind[y[i + 1]]] += 1
    # normalize
    transmat_prior /= np.sum(transmat_prior, axis=1, keepdims=True)
    return transmat_prior


def model_saver(model, model_path, model_type, subject_id, event_id):
    # event list should be sorted by class label
    sorted_events = sorted(event_id.items(), key=lambda item: item[1])
    # Extract the keys in the sorted order and store them in a list
    sorted_events = [item[0] for item in sorted_events]

    try:
        os.mkdir(os.path.join(model_path, subject_id))
    except FileExistsError:
        pass

    now = datetime.now()
    classes = '+'.join(sorted_events)
    date_time_str = now.strftime("%m-%d-%Y-%H-%M-%S")
    model_name = f'{model_type}_{classes}_{date_time_str}.pkl'
    joblib.dump(model, os.path.join(model_path, subject_id, model_name))


def parse_model_type(model_path):
    model_path = os.path.normpath(model_path)
    file_name = model_path.split(os.sep)[-1]
    model_type, events, _ = file_name.split('_')
    events = events.split('+')
    return model_type.lower(), events


def event_metric(event_true, event_pred, fs, hit_time_range=(-0.5, 2), ignore_event=(0,), f_beta=1.):
    """评价单试次f_alpha score
    Args: 
        event_true:
        event_pred:
        fs:
        hit_time_range (tuple): 
        ignore_event (tuple): ignore certain events
        f_beta (float): f_(alpha) score
    Return:
        f_beta score (float): f_alpha score
    """
    if ignore_event is not None:
        event_true = event_true.copy()[np.logical_not(np.isin(event_true[:, 2], ignore_event))]
        event_pred = event_pred.copy()[np.logical_not(np.isin(event_pred[:, 2], ignore_event))]
    true_idx = 0
    pred_idx = 0
    correct_count = 0
    latencies = []
    hit_time_range = (int(fs * hit_time_range[0]), int(fs * hit_time_range[1]))
    while true_idx < len(event_true) and pred_idx < len(event_pred):
        if event_true[true_idx, 0] + hit_time_range[0] <= event_pred[pred_idx, 0] < event_true[true_idx, 0] + hit_time_range[1]:
            if event_true[true_idx, 2] == event_pred[pred_idx, 2]:
                latencies.append((event_pred[pred_idx, 0] - event_true[true_idx, 0]) / fs)
                correct_count += 1
                true_idx += 1
                pred_idx += 1
            else:
                pred_idx += 1
        elif event_pred[pred_idx, 0] < event_true[true_idx, 0] + hit_time_range[0]:
            pred_idx += 1
        else:
            true_idx += 1
    
    if len(event_pred) > 0:
        precision = correct_count / len(event_pred)
    else:
        precision = 0.
    
    recall = correct_count / len(event_true)

    if f_beta ** 2 * precision + recall > 0:
        fbeta_score = (1 + f_beta ** 2) * (precision * recall) / (f_beta ** 2 * precision + recall)
    else:
        fbeta_score = 0.

    return precision, recall, fbeta_score, latencies


def cut_epochs(t, data, timestamps):
    """
    cutting raw data into epochs
    :param t: tuple (start, end, samplerate)
    :param data: ndarray (..., n_times), the last dimension should be the times
    :param timestamps: list of timestamps
    :return: ndarray (n_epochs, ... , n_times), the first dimension be the epochs
    """
    timestamps = np.array(timestamps)
    start = timestamps + int(t[0] * t[2])
    end = timestamps + int(t[1] * t[2])
    # do boundary check
    if start[0] < 0:
        start = start[1:]
        end = end[1:]
    if end[-1] > data.shape[-1]:
        start = start[:-1]
        end = end[:-1]
    epochs = np.stack([data[..., s:e] for s, e in zip(start, end)], axis=0)
    return epochs


def apply_baseline(t, data, mode='mean'):
    """
    Simple wrapper of mne rescale function
    :param t: tuple (start, end, samplerate)
    :param data: ndarray of any shape with axis=-1 the time axis
    :param mode: 'mean' | 'ratio' | 'logratio' | 'percent' | 'zscore' | 'zlogratio'
        refer to mne.baseline.rescale
    :return: ndarray
    """
    start, end, samplerate = t
    base = (start, 0)
    times = np.linspace(start, end, data.shape[-1])
    data = baseline.rescale(data, times, baseline=base, mode=mode, verbose=False)
    return data


def product_dict(**kwargs):
    keys = kwargs.keys()
    vals = kwargs.values()
    for instance in itertools.product(*vals):
        yield dict(zip(keys, instance))


def param_search(model_func, X, y, params: dict, random_state=123):
    """

    :param model_func: model builder
    :param X: ndarray (n_trials, n_channels, n_times)
    :param y: ndarray (n_trials, )
    :param params: dict of params, key is param name and value is search range
    :param random_state:
    :return:
    """
    kfold = KFold(n_splits=10, shuffle=True, random_state=random_state)

    best_auc = -1
    best_param = None
    for p_dict in product_dict(**params):
        model = model_func(**p_dict)

        n_classes = len(np.unique(y))

        y_pred = np.zeros((len(y), n_classes))

        for train_idx, test_idx in kfold.split(X):
            X_train, y_train = X[train_idx], y[train_idx]
            X_test = X[test_idx]
            model.fit(X_train, y_train)
            y_pred[test_idx] = model.predict_proba(X_test)
        auc = multiclass_auc_score(y, y_pred, n_classes=n_classes)

        # update
        if auc > best_auc:
            best_param = p_dict
            best_auc = auc
        
        # print each steps
        logger.debug(f'Current: {p_dict}, {auc}; Best: {best_param}, {best_auc}')

    return best_auc, best_param


def multiclass_auc_score(y_true, prob, n_classes=None):
    if n_classes is None:
        n_classes = len(np.unique(y_true))
    if n_classes > 2:
        auc = roc_auc_score(y_true, prob, multi_class='ovr')
    elif n_classes == 2:
        auc = roc_auc_score(y_true, prob[:, 1])
    else:
        raise ValueError
    return auc


def reref(data, method):
    data = data.copy()
    if method == 'average':
        data -= data.mean(axis=0)
        return data
    elif method == 'bipolar':
        # neo specific
        anode = data[[0, 1, 2, 3, 7, 6, 5]]
        cathode = data[[1, 2, 3, 7, 6, 5, 4]]
        return anode - cathode
    elif method == 'monopolar':
        return data
    else:
        raise ValueError(f'Rereference method unacceptable, got {str(method)}, expect "monopolar" or "average" or "bipolar"')
    