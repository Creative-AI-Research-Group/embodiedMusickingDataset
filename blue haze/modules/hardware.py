'''
to fix the "OSError: [WinError 126] when importing a library":
https://stackoverflow.com/questions/61218285/oserror-winerror-126-when-importing-a-library-in-python
"I had the same problem using a conda env. Demos worked but not the python sample.
I explicitly added %CUBEMOS_SKEL_SDK%\bin to my Path environment since I had nothing before.
That got it going. The %CUBEMOS_SKEL_SDK% was set up okay from the start."
'''

from cubemos.skeletontracking.core_wrapper import CM_TargetComputeDevice
from cubemos.skeletontracking.core_wrapper import initialise_logging, CM_LogLevel
from cubemos.skeletontracking.native_wrapper import Api, TrackingContext, SkeletonKeypoints
from cubemos.skeletontracking.native_wrapper import CM_SKEL_TrackingSimilarityMetric, CM_SKEL_TrackingMethod

from brainflow.board_shim import BoardShim, BrainFlowInputParams

import os
import pyrealsense2 as rs
import numpy as np
import platform
import math
import re
import socket
import serial
import struct
import time
import select
import sys

'''
    REALSENSE SKELETON
'''


def default_log_dir():
    if platform.system() == "Windows":
        return os.path.join(os.environ["LOCALAPPDATA"], "Cubemos", "SkeletonTracking", "logs")
    elif platform.system() == "Linux":
        return os.path.join(os.environ["HOME"], ".cubemos", "skeleton_tracking", "logs")
    else:
        raise Exception("{} is not supported".format(platform.system()))


def default_license_dir():
    if platform.system() == "Windows":
        return os.path.join(os.environ["LOCALAPPDATA"], "Cubemos", "SkeletonTracking", "license")
    elif platform.system() == "Linux":
        return os.path.join(os.environ["HOME"], ".cubemos", "skeleton_tracking", "license")
    else:
        raise Exception("{} is not supported".format(platform.system()))


def check_license_and_variables_exist():
    license_path = os.path.join(default_license_dir(), "cubemos_license.json")
    if not os.path.isfile(license_path):
        raise Exception(
            "The license file has not been found at location \"" +
            default_license_dir() + "\". "
                                    "Please have a look at the Getting Started Guide on how to "
                                    "use the post-installation script to generate the license file")
    if "CUBEMOS_SKEL_SDK" not in os.environ:
        raise Exception(
            "The environment Variable \"CUBEMOS_SKEL_SDK\" is not set. "
            "Please check the troubleshooting section in the Getting "
            "Started Guide to resolve this issue."
        )


class skeletontracker:
    def __init__(self, cloud_tracking_api_key=""):
        check_license_and_variables_exist()

        # Get the path of the native libraries and ressource files
        sdk_path = os.environ["CUBEMOS_SKEL_SDK"]
        model_path = os.path.join(
            sdk_path, "models", "skeleton-tracking", "fp32", "skeleton-tracking.cubemos"
        )

        # Initialise the logging
        initialise_logging(sdk_path, CM_LogLevel.CM_LL_ERROR, True, os.path.join(default_log_dir(), "logs"))

        # Initialise the api with a valid license key in default_license_dir()
        self.__api = Api(default_license_dir())

        # Load the neural network model to the CPU as the default device
        self.__api.load_model(CM_TargetComputeDevice.CM_CPU, model_path)

        # Initialise the edge tracker if the cloud tracker wasnt asked for
        if not cloud_tracking_api_key:
            print("Initialising the Skeleton Tracking Pipeline with EDGE tracking.")
            self.__tracker = TrackingContext()
        else:
            print("Initialising the Skeleton Tracking Pipeline with ReID based CLOUD tracking.")
            self.__tracker = TrackingContext(
                similarity_metric=CM_SKEL_TrackingSimilarityMetric.CM_IOU,
                max_frames_id_keepalive=25,
                tracking_method=CM_SKEL_TrackingMethod.CM_TRACKING_FULLBODY_CLOUD,
                cloud_tracking_api_key=cloud_tracking_api_key,
                min_body_percentage_visible=0.85,
                min_keypoint_confidence=0.7,
                num_teach_in_per_person_cloud_tracking=6,
                force_cloud_tracking_every_x_frame=0)

    def track_skeletons(self, color_image):
        # perform inference and update the tracking id
        skeletons = self.__api.estimate_keypoints(color_image, 256)
        try:
            skeletons = self.__api.update_tracking(color_image, self.__tracker, skeletons, False)
        except Exception as ex:
            print("Exception occured while updating tracking IDs: \"{}\"".format(ex))

        return skeletons


class SkeletonReader():
    def __init__(self):
        self.config = rs.config()
        self.config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
        print('Real Sense Depth Camera ready')

    def start(self):
        # Start the realsense pipeline
        self.pipeline = rs.pipeline()
        self.pipeline.start()

        # Create align object to align depth frames to color frames
        self.align = rs.align(rs.stream.color)

        # Get the intrinsics information for calculation of 3D point
        self.unaligned_frames = self.pipeline.wait_for_frames()
        self.frames = self.align.process(self.unaligned_frames)
        self.depth = self.frames.get_depth_frame()
        self.depth_intrinsic = self.depth.profile.as_video_stream_profile().intrinsics

        # Initialize the cubemos api with a valid license key in default_license_dir()
        self.skeletrack = skeletontracker(cloud_tracking_api_key="")
        self.joint_confidence = 0.2

    def read(self):
        # Create a pipeline object. This object configures the streaming camera and owns it's handle
        self.unaligned_frames = self.pipeline.wait_for_frames()
        self.frames = self.align.process(self.unaligned_frames)
        self.depth = self.frames.get_depth_frame()
        self.color = self.frames.get_color_frame()

        # Convert images to numpy arrays
        depth_image = np.asanyarray(self.depth.get_data())
        color_image = np.asanyarray(self.color.get_data())

        # perform inference and update the tracking id
        self.skeletons = self.skeletrack.track_skeletons(color_image)

        return self.skeletons  # removed self.depth, self.depth_intrinsic, self.joint_confidence

    def terminate(self):
        self.pipeline.stop()


'''
    BRAINBIT
'''


class BrainbitReader:
    def __init__(self):

        # Establish all parameters for Brainflow
        self.params = BrainFlowInputParams()

        # Assign the BrainBit as the board
        self.params.board_id = 7

        # set it logging
        BoardShim.enable_dev_board_logger()
        print('BrainBit reader ready')

    def start(self):
        # instantiate the board reading
        self.board = BoardShim(self.params.board_id, self.params)

        self.board.prepare_session ()

        # board.start_stream () # use this for default options
        self.board.start_stream(2) # removed 48000
        print ('BrainBit stream started')

    def read(self):
        self.data = self.board.get_board_data () # get all data and remove it from internal buffer
        return self.data

    def terminate(self):
        self.board.stop_stream()
        self.board.release_session()


'''
    BITALINO
'''


def find():
    """
    :returns: list of (tuples) with name and MAC address of each device found

    Searches for bluetooth devices nearby.
    """
    if platform.system() == 'Windows' or platform.system() == 'Linux':
        try:
            import bluetooth
        except Exception as e:
            raise Exception(ExceptionCode.IMPORT_FAILED + str(e))
        nearby_devices = bluetooth.discover_devices(lookup_names=True)
        return nearby_devices
    else:
        raise Exception(ExceptionCode.INVALID_PLATFORM)


class ExceptionCode():
    INVALID_ADDRESS = "The specified address is invalid."
    INVALID_PLATFORM = "This platform does not support bluetooth connection."
    CONTACTING_DEVICE = "The computer lost communication with the device."
    DEVICE_NOT_IDLE = "The device is not idle."
    DEVICE_NOT_IN_ACQUISITION = "The device is not in acquisition mode."
    INVALID_PARAMETER = "Invalid parameter."
    INVALID_VERSION = "Only available for Bitalino 2.0."
    IMPORT_FAILED = "Please connect using the Virtual COM Port or confirm that PyBluez is installed; bluetooth wrapper failed to import with error: "


class BITalino(object):
    """
    :param macAddress: MAC address or serial port for the bluetooth device
    :type macAddress: str
    :param timeout: maximum amount of time (seconds) elapsed while waiting for the device to respond
    :type timeout: int, float or None
    :raises Exception: invalid MAC address or serial port
    :raises Exception: invalid timeout value

    Connects to the bluetooth device with the MAC address or serial port provided.

    Possible values for parameter *macAddress*:

    * MAC address: e.g. ``00:0a:95:9d:68:16``
    * Serial port - device name: depending on the operating system. e.g. ``COM3`` on Windows; ``/dev/tty.bitalino-DevB`` on Mac OS X; ``/dev/ttyUSB0`` on GNU/Linux.
    * IP address and port - server: e.g. ``192.168.4.1:8001``

    Possible values for *timeout*:

    ===============  ================================================================
    Value            Result
    ===============  ================================================================
    None             Wait forever
    X                Wait X seconds for a response and raises a connection Exception
    ===============  ================================================================
    """

    def __init__(self, macAddress, timeout=None):
        # Bitalino setup parameters
        # The macAddress variable on Windows can be "XX:XX:XX:XX:XX:XX" or "COMX"
        # while on Mac OS can be "/dev/tty.BITalino-XX-XX-DevB" for devices ending with the last 4 digits of the MAC address or "/dev/tty.BITalino-DevB" for the remaining
        # macAddress = macAddress

        regCompiled = re.compile('^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        checkMatch = re.match(regCompiled, macAddress)
        self.isPython2 = True if sys.version_info[0] == 2 else False
        self.blocking = True if timeout == None else False
        if not self.blocking:
            try:
                self.timeout = float(timeout)
            except Exception:
                raise Exception(ExceptionCode.INVALID_PARAMETER)
        if (checkMatch):
            if platform.system() == 'Windows' or platform.system() == 'Linux':
                try:
                    import bluetooth
                except Exception as e:
                    raise Exception(ExceptionCode.IMPORT_FAILED + str(e))
                self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                self.socket.connect((macAddress, 1))
                self.wifi = False
                self.serial = False
            else:
                raise Exception(ExceptionCode.INVALID_PLATFORM)
        elif (macAddress[0:3] == 'COM' and platform.system() == 'Windows') or (
                macAddress[0:5] == '/dev/' and platform.system() != 'Windows'):
            self.socket = serial.Serial(macAddress, 115200)
            self.wifi = False
            self.serial = True
        elif (macAddress.count(':') == 1):
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((macAddress.split(':')[0], int(macAddress.split(':')[1])))
            self.wifi = True
            self.serial = False
        else:
            raise Exception(ExceptionCode.INVALID_ADDRESS)
        self.started = False
        self.macAddress = macAddress
        split_string = '_v'
        split_string_old = 'V'
        version = self.version()
        if split_string in version:
            version_nbr = float(version.split(split_string)[1][:3])
        else:
            version_nbr = float(version.split(split_string_old)[1][:3])
        self.isBitalino2 = True if version_nbr >= 4.2 else False
        print('Bitalino ready')

    def start(self, SamplingRate=10, analogChannels=[0, 1, 2, 3, 4, 5]):
        """
        :param SamplingRate: sampling frequency (Hz)
        :type SamplingRate: int
        :param analogChannels: channels to be acquired
        :type analogChannels: array, tuple or list of int
        :raises Exception: device already in acquisition (not IDLE)
        :raises Exception: sampling rate not valid
        :raises Exception: list of analog channels not valid

        Sets the sampling rate and starts acquisition in the analog channels set.
        Setting the sampling rate and starting the acquisition implies the use of the method :meth:`send`.

        Possible values for parameter *SamplingRate*:

        * 1
        * 10
        * 100
        * 1000

        Possible values, types, configurations and examples for parameter *analogChannels*:

        ===============  ====================================
        Values           0, 1, 2, 3, 4, 5
        Types            list ``[]``, tuple ``()``, array ``[[]]``
        Configurations   Any number of channels, identified by their value
        Examples         ``[0, 3, 4]``, ``(1, 2, 3, 5)``
        ===============  ====================================

        .. note:: To obtain the samples, use the method :meth:`read`.
        """
        if (self.started == False):
            if int(SamplingRate) not in [1, 10, 100, 1000]:
                raise Exception(ExceptionCode.INVALID_PARAMETER)

            # CommandSRate: <Fs>  0  0  0  0  1  1
            if int(SamplingRate) == 1000:
                commandSRate = 3
            elif int(SamplingRate) == 100:
                commandSRate = 2
            elif int(SamplingRate) == 10:
                commandSRate = 1
            elif int(SamplingRate) == 1:
                commandSRate = 0

            if isinstance(analogChannels, list):
                analogChannels = analogChannels
            elif isinstance(analogChannels, tuple):
                analogChannels = list(analogChannels)
            elif isinstance(analogChannels, numpy.ndarray):
                analogChannels = analogChannels.astype('int').tolist()
            else:
                raise Exception(ExceptionCode.INVALID_PARAMETER)

            analogChannels = list(set(analogChannels))

            if len(analogChannels) == 0 or len(analogChannels) > 6 or any(
                    [item not in range(6) or type(item) != int for item in analogChannels]):
                raise Exception(ExceptionCode.INVALID_PARAMETER)

            self.send((commandSRate << 6) | 0x03)

            # CommandStart: A6 A5 A4 A3 A2 A1 0  1
            commandStart = 1
            for i in analogChannels:
                commandStart = commandStart | 1 << (2 + i)

            self.send(commandStart)
            self.started = True
            self.analogChannels = analogChannels
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IDLE)

    def stop(self):
        """
        :raises Exception: device not in acquisition (IDLE)

        Stops the acquisition. Stoping the acquisition implies the use of the method :meth:`send`.
        """
        if (self.started):
            self.send(0)
        else:
            if self.isBitalino2:
                # Command: 1  1  1  1  1  1  1  1 - Go to idle mode from all modes.
                self.send(255)
            else:
                raise Exception(ExceptionCode.DEVICE_NOT_IN_ACQUISITION)
        self.started = False

    def close(self):
        """
        Closes the bluetooth or serial port socket.
        """
        if self.wifi:
            self.socket.settimeout(1.0)  # force a timeout on TCP/IP sockets
            try:
                self.receive(1024)  # receive any pending data
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except socket.timeout:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
        else:
            self.socket.close()

    def send(self, data):
        """
        Sends a command to the BITalino device.
        """
        time.sleep(0.1)
        if self.serial:
            if self.isPython2:
                self.socket.write(chr(data))
            else:
                self.socket.write(bytes([data]))
        else:
            if self.isPython2:
                self.socket.send(chr(data))
            else:
                self.socket.send(bytes([data]))

    def battery(self, value=0):
        """
        :param value: threshold value
        :type value: int
        :raises Exception: device in acquisition (not IDLE)
        :raises Exception: threshold value is invalid

        Sets the battery threshold for the BITalino device. Setting the battery threshold implies the use of the method :meth:`send`.

        Possible values for parameter *value*:

        ===============  =======  =====================
        Range            *value*  Corresponding threshold (Volts)
        ===============  =======  =====================
        Minimum *value*  0        3.4 Volts
        Maximum *value*  63       3.8 Volts
        ===============  =======  =====================
        """
        if (self.started == False):
            if 0 <= int(value) <= 63:
                # CommandBattery: <bat   threshold> 0  0
                commandBattery = int(value) << 2
                self.send(commandBattery)
            else:
                raise Exception(ExceptionCode.INVALID_PARAMETER)
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IDLE)

    def pwm(self, pwmOutput=100):
        """
        :param pwmOutput: value for the pwm output
        :type pwmOutput: int
        :raises Exception: invalid pwm output value
        :raises Exception: device is not a BITalino 2.0

        Sets the pwm output for the BITalino 2.0 device. Implies the use of the method :meth:`send`.

        Possible values for parameter *pwmOutput*: 0 - 255.
        """
        if (self.isBitalino2):
            if 0 <= int(pwmOutput) <= 255:
                self.send(163)
                self.send(pwmOutput)
            else:
                raise Exception(ExceptionCode.INVALID_PARAMETER)
        else:
            raise Exception(ExceptionCode.INVALID_VERSION)

    def state(self):
        """
        :returns: dictionary with the state of all channels
        :raises Exception: device is not a BITalino version 2.0
        :raises Exception: device in acquisition (not IDLE)
        :raises Exception: lost communication with the device when data is corrupted

        Returns the state of all analog and digital channels. Reading channel State from BITalino implies the use of the method :meth:`send` and :meth:`receive`.
        The returned dictionary structure contains the following key-value pairs:

        =================  ================================ ============== =====================
        Key                Value                            Type           Examples
        =================  ================================ ============== =====================
        analogChannels     Value of all analog channels     Array of int   [A1 A2 A3 A4 A5 A6]
        battery            Value of the battery channel     int
        batteryThreshold   Value of the battery threshold   int            :meth:`battery`
        digitalChannels    Value of all digital channels    Array of int   [I1 I2 O1 O2]
        =================  ================================ ============== =====================
        """
        if (self.isBitalino2):
            if (self.started == False):
                # CommandState: 0  0  0  0  1  0  1  1
                # Response: <A1 (2 bytes: 0..1023)> <A2 (2 bytes: 0..1023)> <A3 (2 bytes: 0..1023)>
                #           <A4 (2 bytes: 0..1023)> <A5 (2 bytes: 0..1023)> <A6 (2 bytes: 0..1023)>
                #           <ABAT (2 bytes: 0..1023)>
                #           <Battery threshold (1 byte: 0..63)>
                #           <Digital ports + CRC (1 byte: I1 I2 O1 O2 <CRC 4-bit>)>
                self.send(11)
                number_bytes = 16
                Data = self.receive(number_bytes)
                decodedData = list(struct.unpack(number_bytes * "B ", Data))
                crc = decodedData[-1] & 0x0F
                decodedData[-1] = decodedData[-1] & 0xF0
                x = 0
                for i in range(number_bytes):
                    for bit in range(7, -1, -1):
                        x = x << 1
                        if (x & 0x10):
                            x = x ^ 0x03
                        x = x ^ ((decodedData[i] >> bit) & 0x01)
                if (crc == x & 0x0F):
                    digitalPorts = []
                    digitalPorts.append(decodedData[-1] >> 7 & 0x01)
                    digitalPorts.append(decodedData[-1] >> 6 & 0x01)
                    digitalPorts.append(decodedData[-1] >> 5 & 0x01)
                    digitalPorts.append(decodedData[-1] >> 4 & 0x01)
                    batteryThreshold = decodedData[-2]
                    battery = decodedData[-3] << 8 | decodedData[-4]
                    A6 = decodedData[-5] << 8 | decodedData[-6]
                    A5 = decodedData[-7] << 8 | decodedData[-8]
                    A4 = decodedData[-9] << 8 | decodedData[-10]
                    A3 = decodedData[-11] << 8 | decodedData[-12]
                    A2 = decodedData[-13] << 8 | decodedData[-14]
                    A1 = decodedData[-15] << 8 | decodedData[-16]
                    acquiredData = {}
                    acquiredData['analogChannels'] = [A1, A2, A3, A4, A5, A6]
                    acquiredData['battery'] = battery
                    acquiredData['batteryThreshold'] = batteryThreshold
                    acquiredData['digitalChannels'] = digitalPorts
                    return acquiredData
                else:
                    raise Exception(ExceptionCode.CONTACTING_DEVICE)
            else:
                raise Exception(ExceptionCode.DEVICE_NOT_IDLE)
        else:
            raise Exception(ExceptionCode.INVALID_VERSION)

    def trigger(self, digitalArray=None):
        """
        :param digitalArray: array which acts on digital outputs according to the value: 0 or 1
        :type digitalArray: array, tuple or list of int
        :raises Exception: list of digital channel output is not valid
        :raises Exception: device not in acquisition (IDLE) (for BITalino 1.0)

        Acts on digital output channels of the BITalino device. Triggering these digital outputs implies the use of the method :meth:`send`.
        Digital Outputs can be set on IDLE or while in acquisition for BITalino 2.0.

        Each position of the array *digitalArray* corresponds to a digital output, in ascending order. Possible values, types, configurations and examples for parameter *digitalArray*:

        ===============  ============================================== ==============================================
        Meta             BITalino 1.0                                   BITalino 2.0
        ===============  ============================================== ==============================================
        Values           0 or 1                                         0 or 1
        Types            list ``[]``, tuple ``()``, array ``[[]]``      list ``[]``, tuple ``()``, array ``[[]]``
        Configurations   4 values, one for each digital channel output  2 values, one for each digital channel output
        Examples         ``[1, 0, 1, 0]``                               ``[1, 0]``
        ===============  ============================================== ==============================================
        """
        arraySize = 2 if self.isBitalino2 else 4
        if not self.isBitalino2 and not self.started:
            raise Exception(ExceptionCode.DEVICE_NOT_IN_ACQUISITION)
        else:
            digitalArray = [0 for i in range(arraySize)] if digitalArray == None else digitalArray
            if isinstance(digitalArray, list):
                digitalArray = digitalArray
            elif isinstance(digitalArray, tuple):
                digitalArray = list(digitalArray)
            elif isinstance(digitalArray, numpy.ndarray):
                digitalArray = digitalArray.astype('int').tolist()
            else:
                raise Exception(ExceptionCode.INVALID_PARAMETER)

            pValues = [0, 1]
            if len(digitalArray) != arraySize or any(
                    [item not in pValues or type(item) != int for item in digitalArray]):
                raise Exception(ExceptionCode.INVALID_PARAMETER)

            if self.isBitalino2:
                # CommandDigital: 1  0  1  1  O2 O1 1  1 - Set digital outputs
                data = 179
            else:
                # CommandDigital: 1  0  O4  O3  O2 O1 1  1 - Set digital outputs
                data = 3

            for i, j in enumerate(digitalArray):
                data = data | j << (2 + i)
            self.send(data)

    def read(self, nSamples=100):
        """
        :param nSamples: number of samples to acquire
        :type nSamples: int
        :returns: array with the acquired data
        :raises Exception: device not in acquisition (in IDLE)
        :raises Exception: lost communication with the device when data is corrupted

        Acquires `nSamples` from BITalino. Reading samples from BITalino implies the use of the method :meth:`receive`.

        Requiring a low number of samples (e.g. ``nSamples = 1``) may be computationally expensive; it is recommended to acquire batches of samples (e.g. ``nSamples = 100``).

        The data acquired is organized in a matrix whose lines correspond to samples and the columns are as follows:

        * Sequence Number
        * 4 Digital Channels (always present)
        * 1-6 Analog Channels (as defined in the :meth:`start` method)

        Example matrix for ``analogChannels = [0, 1, 3]`` used in :meth:`start` method:

        ==================  ========= ========= ========= ========= ======== ======== ========
        Sequence Number*    Digital 0 Digital 1 Digital 2 Digital 3 Analog 0 Analog 1 Analog 3
        ==================  ========= ========= ========= ========= ======== ======== ========
        0
        1
        (...)
        15
        0
        1
        (...)
        ==================  ========= ========= ========= ========= ======== ======== ========

        .. note:: *The sequence number overflows at 15
        """
        if (self.started):
            nChannels = len(self.analogChannels)

            if nChannels <= 4:
                number_bytes = int(math.ceil((12. + 10. * nChannels) / 8.))
            else:
                number_bytes = int(math.ceil((52. + 6. * (nChannels - 4)) / 8.))

            dataAcquired = numpy.zeros((nSamples, 5 + nChannels), dtype=int)
            for sample in range(nSamples):
                Data = self.receive(number_bytes)
                decodedData = list(struct.unpack(number_bytes * "B ", Data))
                crc = decodedData[-1] & 0x0F
                decodedData[-1] = decodedData[-1] & 0xF0
                x = 0
                for i in range(number_bytes):
                    for bit in range(7, -1, -1):
                        x = x << 1
                        if (x & 0x10):
                            x = x ^ 0x03
                        x = x ^ ((decodedData[i] >> bit) & 0x01)
                if (crc == x & 0x0F):
                    dataAcquired[sample, 0] = decodedData[-1] >> 4
                    dataAcquired[sample, 1] = decodedData[-2] >> 7 & 0x01
                    dataAcquired[sample, 2] = decodedData[-2] >> 6 & 0x01
                    dataAcquired[sample, 3] = decodedData[-2] >> 5 & 0x01
                    dataAcquired[sample, 4] = decodedData[-2] >> 4 & 0x01
                    if nChannels > 0:
                        dataAcquired[sample, 5] = ((decodedData[-2] & 0x0F) << 6) | (decodedData[-3] >> 2)
                    if nChannels > 1:
                        dataAcquired[sample, 6] = ((decodedData[-3] & 0x03) << 8) | decodedData[-4]
                    if nChannels > 2:
                        dataAcquired[sample, 7] = (decodedData[-5] << 2) | (decodedData[-6] >> 6)
                    if nChannels > 3:
                        dataAcquired[sample, 8] = ((decodedData[-6] & 0x3F) << 4) | (decodedData[-7] >> 4)
                    if nChannels > 4:
                        dataAcquired[sample, 9] = ((decodedData[-7] & 0x0F) << 2) | (decodedData[-8] >> 6)
                    if nChannels > 5:
                        dataAcquired[sample, 10] = decodedData[-8] & 0x3F
                else:
                    raise Exception(ExceptionCode.CONTACTING_DEVICE)
            return dataAcquired
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IN_ACQUISITION)

    def version(self):
        """
        :returns: str with the version of BITalino
        :raises Exception: device in acquisition (not IDLE)

        Retrieves the BITalino version. Retrieving the version implies the use of the methods :meth:`send` and :meth:`receive`.
        """
        if (self.started == False):
            # CommandVersion: 0  0  0  0  0  1  1  1
            self.send(7)
            version_str = ''
            while True:
                if self.isPython2:
                    version_str += self.receive(1)
                else:
                    version_str += self.receive(1).decode('utf-8')
                if version_str[-1] == '\n' and 'BITalino' in version_str:
                    break
            return version_str[version_str.index("BITalino"):-1]
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IDLE)

    def receive(self, nbytes):
        """
        :param nbytes: number of bytes to retrieve
        :type nbytes: int
        :return: string packed binary data
        :raises Exception: lost communication with the device when timeout is reached

        Retrieves `nbytes` from the BITalino device and returns it as a string pack with length of `nbytes`. The timeout is defined on instantiation.
        """
        if self.isPython2:
            data = ''
        else:
            data = b''
        if self.serial:
            while len(data) < nbytes:
                if not self.blocking:
                    initTime = time.time()
                    while self.socket.inWaiting() < 1:
                        finTime = time.time()
                        if (finTime - initTime) > self.timeout:
                            raise Exception(ExceptionCode.CONTACTING_DEVICE)
                data += self.socket.read(1)
        else:
            while len(data) < nbytes:
                if not self.blocking:
                    ready = select.select([self.socket], [], [], self.timeout)
                    if ready[0]:
                        pass
                    else:
                        raise Exception(ExceptionCode.CONTACTING_DEVICE)
                data += self.socket.recv(1)
        return data
