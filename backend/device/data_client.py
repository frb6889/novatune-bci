import socket
import threading

import numpy as np
from scipy import signal


class NeuracleDataClient:
    UPDATE_INTERVAL = 0.04
    BYTES_PER_NUM = 4

    def __init__(self, n_channel=9, samplerate=1000, host='localhost', port=8712, buffer_len=1.):
        self.n_channel = n_channel
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.chunk_size = int(self.UPDATE_INTERVAL * samplerate * self.BYTES_PER_NUM * n_channel)
        self.buffer = []
        self.max_buffer_length = int(buffer_len * samplerate)
        self._host = host
        self._port = port
        # thread lock
        self.lock = threading.Lock()
        self.__datathread = threading.Thread(target=self.__recv_loop)
        self.samplerate = samplerate

        self.filter = OnlineHPFilter(1, samplerate)

        # start client
        self.__config()

    def __config(self):
        self.__sock.connect((self._host, self._port))
        self.__run_forever()

    def is_active(self):
        return self.__sock.fileno() != -1

    def close(self):
        self.__sock.close()
        self.__datathread.join()

    def __recv_loop(self):
        while self.is_active():
            try:
                data = self.__sock.recv(self.chunk_size)
            except OSError:
                break
            if len(data) % 4 != 0:
                continue

            # unpack data
            data = self._unpack_data(data)

            # do highpass (exclude stim channel)
            data[:, :-1] = self.filter.filter_incoming(data[:, :-1])

            # update buffer
            self.lock.acquire()
            self.buffer.extend(data.tolist())
            # remove old data
            old_data_len = len(self.buffer) - self.max_buffer_length
            if old_data_len > 0:
                self.buffer = self.buffer[old_data_len:]
            self.lock.release()
    
    def _unpack_data(self, bytes_data):
        byte_data = bytearray(bytes_data)
        if len(byte_data) % 4 != 0:
            raise ValueError
        data = np.frombuffer(byte_data, dtype='<f')
        data = np.reshape(data, (-1, self.n_channel))
        # from uV to V, ignore event channel
        data[:, :-1] *= 1e-6
        return data

    def __run_forever(self):
        self.__datathread.start()

    def get_trial_data(self, clear=False):
        """
        called to copy trial data from buffer
        :args
            clear (bool): 
        :return:
            samplerate: number, samplerate
            events: ndarray (n_events, 3), [onset, duration, event_label]
            data: ndarray with shape of (channels, timesteps)
        """
        self.lock.acquire()
        data = self.buffer.copy()
        self.lock.release()
        data = np.array(data)
        trigger_channel = data[:, -1]
        onset = np.flatnonzero(trigger_channel)
        event_label = trigger_channel[onset]
        events = np.stack((onset, np.zeros_like(onset), event_label), axis=1)
        if clear:
            self.buffer.clear()
        return self.samplerate, events, data[:, :-1].T


class OnlineHPFilter:
    def __init__(self, freq=1, fs=1000):
        self.sos = signal.butter(2, freq, btype='hp', fs=fs, output='sos')
        self._z = None

    def filter_incoming(self, data):
        """
        Args: 
            data (ndarray): (n_times, n_chs)
        Returns:
            y (ndarray): (n_times, n_chs)
        """
        if self._z is None:
            self._z = np.zeros((self.sos.shape[0], 2, data.shape[1]))

        y, self._z = signal.sosfilt(self.sos, data, axis=0, zi=self._z)
        return y
