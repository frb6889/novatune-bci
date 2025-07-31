"""Module core/configs provide project base settings"""
import glob
import json
import os
import os.path


class Settings:
    PROJECT_NAME: str = 'Kraken'
#     DEVICE = 'neo'
    DEVICE = 'EEGCap64-V3.0'
    CONFIG_INFO = {
        'host': '127.0.0.1',
        'port': 8712,
        'controlmode': 'socket',
        'channel_count': 65,
        'sample_rate': 1000,
        'buffer_length': 20,
#         'channel_labels': [
#             'CH001',
#             'CH002',
#             'CH003',
#             'CH004',
#             'CH005',
#             'CH006',
#             'CH007',
#             'CH008',
#             'STIM'
#         ],
#         'strips': [['CH001', 'CH002', 'CH003', 'CH004'], 
#                    ['CH005', 'CH006', 'CH007', 'CH008']],
        'channel_labels':[
    "Cz", "CP1", "C4", "Pz", "O1", "Fp1", "CP6", "O2", "CP2", "P8", "C3", "P7", "Fp2", "F8", "CP5",
    "F7", "HEOL", "FC5", "HEOR", "P4", "T7", "F3", "T8", "FC2", "PO4", "FC6", "P3", "PO3", "Oz", "F4",
    "FC1", "Fz", "FC4", "Fpz", "P6", "FCz", "C6", "POz", "F6", "PO6", "PO8", "C2", "TP8", "F2", "FT8",
    "AF4", "AF8", "CP4", "AF7", "CP3", "FT7", "AF3", "TP7", "F1", "PO7", "C1", "F5", "PO5", "C5", "ECG",
    "P5", "VEOL", "FC3", "VEOU",'EVENT'
],
        'reref': 'average', 
        'normP': [[-14, -13.4], 
             [-13.98, -13.37], 
             [-13.82, -13.2], 
             [-13.8, -13], 
             [-14, -13.46], 
             [-14.09, -13.4], 
             [-14.02, -13.34]],
        'visbands': [60, 90],
        'stds': 3,
        'nperseg': 1000
    }
    
    FINGERMODEL_IDS = {
        'rest': 0,
        'cylinder': 1,
        'ball': 2,
        'flex': 3,
        'double': 4,
        'treble': 5,
        'extend': 6,
        'hold': 7,
    }
    FINGERMODEL_IDS_INVERSE = {
        0: 'rest',
        1: 'cylinder',
        2: 'ball',
        3: 'flex',
        4: 'double',
        5: 'treble',
        6: 'extend',
        7: 'hold'
    }
    PROJECT_VERSION: str = '0.0.1'
    DATA_PATH = './data'
    MODEL_PATH = './static/models/ldaparm_TT.mat'
    LOG_PATH = './static/log/log_TT/log20240308/arrow.log'


settings = Settings()
