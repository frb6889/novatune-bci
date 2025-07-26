import socket
import struct

import serial


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class TriggerNeuracle:

    def __init__(self, port, **kwargs):
        self.kwargs = kwargs
        # initiate triggerbox
        self.triggerbox = TriggerBox(port=port)

    def send_trigger(self, data):
        # directly using serial port
        self.triggerbox.OutputEventData(data)


class TriggerBox(object):
    """docstring for TriggerBox"""
    functionIDSensorParaGet = 1

    functionIDSensorParaSet = 2
    functionIDDeviceInfoGet = 3
    functionIDDeviceNameGet = 4
    functionIDSensorSampleGet = 5
    functionIDSensorInfoGet = 6
    functionIDOutputEventData = 225
    functionIDError = 131

    sensorTypeDigitalIN = 1
    sensorTypeLight = 2
    sensorTypeLineIN = 3
    sensorTypeMic = 4
    sensorTypeKey = 5
    sensorTypeTemperature = 6
    sensorTypeHumidity = 7
    sensorTypeAmbientlight = 8
    sensorTypeDebug = 9
    sensorTypeAll = 255

    deviceID = 1
    # TODO: get device ID

    # properties
    comportHandle = None
    deviceName = None
    deviceInfo = None
    sensorInfo = None
    tcpOutput = None

    def __init__(self, port=None, tcpPort=None):
        if tcpPort is not None:
            self.tcpOutput = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcpOutput.connect(('localhost', tcpPort))

        self.comportHandle = serial.Serial(port, 115200, timeout=0.05)
        self.comportHandle.flush()
        self.GetDeviceName()
        self.GetDeviceInfo()
        self.GetSensorInfo()

    def OutputEventData(self, eventData):
        # directly mark trigger with serial
        # eventData is an unsigned short
        assert isinstance(eventData, int)
        msg = struct.pack('<H', eventData)
        self.SendCommand(self.functionIDOutputEventData, msg)
        resp = self.ReadResponse(self.functionIDOutputEventData)
        if self.tcpOutput is not None:
            self.tcpOutput.send(resp)

    def SetEventData(self, sensorID, eventData, triggerToBeOut=1):
        assert isinstance(eventData, int)
        sensorPara = self.GetSensorPara(sensorID)
        sensorPara.TriggerToBeOut = triggerToBeOut
        sensorPara.EventData = eventData
        self.SetSensorPara(sensorID, sensorPara)

    def GetDeviceName(self):
        self.SendCommand(self.functionIDDeviceNameGet, 1)
        name = self.ReadResponse(self.functionIDDeviceNameGet)
        name = name.decode()
        self.deviceName = name
        return name

    def GetDeviceInfo(self):
        self.SendCommand(self.functionIDDeviceInfoGet, 1)
        info = self.ReadResponse(self.functionIDDeviceInfoGet)
        deviceInfo = AttrDict({
            'HardwareVersion': info[0],
            'FirmwareVersion': info[1],
            'SensorSum': info[2],
            'ID': struct.unpack('<I', info[4:])
        })
        self.deviceInfo = deviceInfo
        return deviceInfo

    def GetSensorInfo(self):
        switch = {
            self.sensorTypeDigitalIN: 'DigitalIN',
            self.sensorTypeLight: 'Light',
            self.sensorTypeLineIN: 'LineIN',
            self.sensorTypeMic: 'Mic',
            self.sensorTypeKey: 'Key',
            self.sensorTypeTemperature: 'Temperature',
            self.sensorTypeHumidity: 'Humidity',
            self.sensorTypeAmbientlight: 'Ambientlight',
            self.sensorTypeDebug: 'Debug'
        }
        self.SendCommand(self.functionIDSensorInfoGet)
        info = self.ReadResponse(self.functionIDSensorInfoGet)
        sensorInfo = []
        for i in range(0, len(info), 2):
            # print(info[i], info[i+1])
            sensor_type = info[i]
            try:
                sensorType = switch[sensor_type]
            except KeyError:
                sensorType = 'Undefined'
                # print('Undefined sensor type')
            sensorNum = info[i + 1]
            sensorInfo.append(AttrDict(Type=sensorType, Number=sensorNum))
        self.sensorInfo = sensorInfo
        return sensorInfo

    def GetSensorPara(self, sensorID):
        sensor = self.sensorInfo[sensorID]
        cmd = [self.SensorType(sensor.Type), sensor.Number]
        cmd = struct.pack('<2B', *cmd)
        self.SendCommand(self.functionIDSensorParaGet, cmd)
        para = self.ReadResponse(self.functionIDSensorParaGet)
        para = struct.unpack('<2B3H', para)
        sensorPara = AttrDict({
            'Edge': para[0],
            'OutputChannel': para[1],
            'TriggerToBeOut': para[2],
            'Threshold': para[3],
            'EventData': para[4]
        })
        return sensorPara

    def SetSensorPara(self, sensorID, sensorPara):
        sensor = self.sensorInfo[sensorID]
        cmd = [self.SensorType(sensor.Type), sensor.Number] + [sensorPara[key]
                                                               for key in sensorPara.keys()]
        cmd = struct.pack('<4B3H', *cmd)
        self.SendCommand(self.functionIDSensorParaSet, cmd)
        resp = self.ReadResponse(self.functionIDSensorParaSet)
        isSucceed = (resp[0] == self.SensorType(sensor.Type)) and (resp[1] == sensor.Number)
        return isSucceed

    def GetSensorSample(self, sensorID):
        sensor = self.sensorInfo[sensorID]
        cmd = [self.SensorType(sensor.Type), sensor.Number]
        self.SendCommand(self.functionIDSensorSampleGet, struct.pack('<2B', *cmd))
        result = self.ReadResponse(self.functionIDSensorSampleGet)
        if result[0] != self.SensorType(sensor.Type) or result[1] != sensor.Number:
            raise Exception('Get sensor sample error')
        adcResult = struct.unpack('<H', result[2:])[0]
        return adcResult

    def SensorType(self, typeString):
        switch = {
            'DigitalIN': self.sensorTypeDigitalIN,
            'Light': self.sensorTypeLight,
            'LineIN': self.sensorTypeLineIN,
            'Mic': self.sensorTypeMic,
            'Key': self.sensorTypeKey,
            'Temperature': self.sensorTypeTemperature,
            'Humidity': self.sensorTypeHumidity,
            'Ambientlight': self.sensorTypeAmbientlight,
            'Debug': self.sensorTypeDebug
        }
        try:
            typeNum = switch[typeString]
        except KeyError:
            raise Exception('Undefined sensor type')
        return typeNum

    def SendCommand(self, functionID, command=None):
        if command is not None:
            # process command data structure
            if isinstance(command, int):
                command = struct.pack('<B', command)
            # make sure command finally becomes 'bytes'
            assert isinstance(command, bytes)
            payload = len(command)
        else:
            payload = 0
        value = (self.deviceID, functionID, payload)
        message = struct.pack('<2BH', *value)
        if command is not None:
            message += command
        self.comportHandle.write(message)

    def ReadResponse(self, functionID):
        errorCases = {
            0: 'None',
            1: 'FrameHeader',
            2: 'FramePayload',
            3: 'ChannelNotExist',
            4: 'DeviceID',
            5: 'FunctionID',
            6: 'SensorType'
        }
        message = self.comportHandle.read(4)
        message = struct.unpack('<2BH', message)
        if message[0] != self.deviceID:
            raise Exception('Response error: request deviceID %d, \
                    return deviceID %d', self.deviceID, message[0])
        if message[1] != functionID:
            if message[1] == self.functionIDError:
                errorType = self.comportHandle.read(1)
                try:
                    errorMessage = errorCases[errorType]
                except KeyError:
                    raise Exception('Undefined error type')
                raise Exception('Response error: ', errorMessage)
            else:
                raise Exception('Response error: request functionID %d, \
                        return functionID %d', functionID, message[1])
        payload = message[2]
        DataBuf = self.comportHandle.read(payload)
        return DataBuf
