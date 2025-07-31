import numpy as np

from .model import riemann_feature_embedder, baseline_feature_embedder, cps_feature_embedder
from .feature_extractors import FeatExtractor, FilterbankExtractor
from .utils import cut_epochs


def csp_model_builder(fs, n_components=8, lf_bands=[(15, 35), (35, 50)], hg_bands=[(55, 95), (105, 145)]):
    feat_extractor = FeatExtractor(fs, lf_bands, hg_bands)
    embedder = cps_feature_embedder(n_components)
    return [feat_extractor, embedder]


def riemann_model_builder(fs, n_ch=8, lf_bands=[(15, 35), (35, 50)], hg_bands=[(55, 95), (105, 145)]):
    feat_extractor = FeatExtractor(fs, lf_bands, hg_bands)
    # compute covariance
    feat_dim = []
    if lf_bands is not None:
        feat_dim.append(len(lf_bands) * n_ch)
    if hg_bands is not None:
        feat_dim.append(len(hg_bands) * n_ch)
    embedder = riemann_feature_embedder(feat_dim, estimator='lwf')
    return [feat_extractor, embedder]


def baseline_model_builder(fs, freqs=(20, 150, 15), target_fs=10):
    filter_banks = np.arange(*freqs)
    feat_extractor = FilterbankExtractor(fs, filter_banks)
    embedder = baseline_feature_embedder(fs, target_fs, axis=-1)
    return [feat_extractor, embedder]


def data_evaluation(model, raw: np.ndarray, fs, events=None, duration=None, return_cls=True):
    feat_extractor, embedder, clf = model
    filtered_data = feat_extractor.transform(raw)
    if (events is not None) and (duration is not None):
        X = cut_epochs((0, duration, fs), filtered_data, events[:, 0])
    else:
        X = filtered_data[None]
    # embed feature
    X_embed = embedder.transform(X)
    # pred 
    prob = clf.predict_proba(X_embed)
    if return_cls:
        y_pred = clf.classes_[np.argmax(prob, axis=1)]
        return prob, y_pred
    else:
        return prob

