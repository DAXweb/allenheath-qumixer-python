import socket
import threading
import sys
from enum import IntEnum

class QU_MIXER_MODELS(IntEnum):
    QU_16_MODEL = 1
    QU_24_MODEL = 2
    QU_32_MODEL = 3
    QU_PAC_MODEL = 4


#Questi sono pacchetti che il Mixer Invia al Client
class QU_PACKET_TYPE(IntEnum):
    ACTIVE_SENSE_PACKET = 0 #Il Mixer invia una richiesta di active sens che deve essere gestita entro 12 secondi
    IDENTIFY_PACKET = 1
    SYNC_PACKET = 2
    NPRN_PACKET = 3
    UNKNOW_PACKET = 99


class QU_PROTOCOL_STATE(IntEnum):
    PROTOCOL_UNDEFINED = 99
    MIXER_NOT_IDENTIFIED = 0
    WAITING_QUMIXER_IDENTIFY_RESPONSE = 1
    RECEIVED_MIXER_IDENTIFICATION = 2


class QU_NPRN_MESSAGE_STATE(IntEnum):
    NRPN_UNDEFINED = 99
    NPRN_HEADER_MSB_STATE = 0
    NPRN_HEADER_LSB_STATE = 1
    NPRN_DATA_MSB_STATE = 2
    NPRN_DATA_LSB_STATE = 3


class NRPN_MESSAGE_SPECIFIER(IntEnum):
    NRPN_HEAD_MSB = 0x63
    NRPN_HEAD_LSB = 0x62
    NRPN_DATA_MSB = 0x06
    NRPN_DATA_LSB = 0x26

class QuMixer:

    def __init__(self):
        self.quMidiChan = 0
        self.quMixVersionMajor = 0
        self.quMixVersionMinor = 0
        self.quMixFirmwareMajor = 0
        self.quMixFirmwareMinor = 0
        self.quMixModel = 0

    def dump(self):
        print("")
        print("--------DUMP Mixer-----------")
        print("- Model : {}".format(str(self.quMixModel)))
        print("- Midi Chan : {}".format(str(self.quMidiChan)))
        print("- Firmware : {}.{}".format(str(self.quMixFirmwareMajor), str(self.quMixFirmwareMinor)))

class NrpnCommand:

    def __init__(self):
        self.channelID = 0
        self.channelTypeEnum = 0
        self.paramID = 0
        self.paramTypeEnum = 0
        self.paramValue = 0
        self.extraParamValue = 0

    def dump(self):
        print("\n-------DUMP NrpnCommand-------")
        print("- channelID : {}".format(hex(self.channelID)))
        print("- channelTypeEnum : {}".format(str(self.channelTypeEnum)))
        print("- paramID : {}".format(hex(self.paramID)))
        print("- paramTypeEnum : {}".format(str(self.paramTypeEnum)))
        print("- paramValue : {}".format(hex(self.paramValue)))
        print("- extraParam : {}".format(hex(self.extraParamValue)))
        print("\n")


class QU_PARAM_LIST(IntEnum):
    QU_GROUP_MODE = 0x5E
    QU_FADER = 0x17
    QU_PAN = 0x16
    QU_LR_ASSIGN = 0x18
    QU_MIX_ASSIGN = 0x55
    QU_MUTE_GROUP_ASSIGN = 0x5C
    QU_DCA_GROUP_ASSIGN = 0x40
    QU_MIX_PRE_POST = 0x50
    QU_SEND_LEVEL = 0x20
    QU_PAFL_SELECT = 0x51
    QU_USB_SOURCE = 0x12
    QU_PREAMP_SOURCE = 0x57
    QU_DSNAKE_PATCH = 0x5D
    QU_LOCAL_PREAMP_GAIN = 0x19
    QU_LOCAL_PREAMP_48V = 0x69
    QU_DSNAKE_PREAMP_GAIN = 0x58
    QU_DSNAKE_PREAMP_PAD = 0x59
    QU_DSNAKE_PREAMP_48V = 0x5A
    QU_DIGITAL_TRIM = 0x52
    QU_STEREO_TRIM = 0x54
    QU_POLARITY = 0x6A
    QU_INSERT_IN_OUT = 0x6B
    QU_PEQ_LF_GAIN = 0x01
    QU_PEQ_LF_FREQ = 0x02
    QU_PEQ_LF_WIDTH = 0x03
    QU_PEQ_LF_TYPE = 0x04
    QU_PEQ_LM_GAIN = 0x05
    QU_PEQ_LM_FREQ = 0x06
    QU_PEQ_LM_WIDTH = 0x07
    QU_PEQ_HM_GAIN = 0x09
    QU_PEQ_HM_FREQ = 0x0A
    QU_PEQ_HM_WIDTH = 0x0B
    QU_PEQ_HF_GAIN = 0x0D
    QU_PEQ_HF_FREQ = 0x0E
    QU_PEQ_HF_WIDTH = 0x0F
    QU_PEQ_HF_TYPE = 0x10
    QU_PEQ_IN_OUT = 0x11
    QU_HPF_FREQ = 0x13
    QU_HPF_IN_OUT = 0x14
    QU_GEQ_GAIN = 0x70
    QU_GEQ_IN_OUT = 0x71
    QU_GATE_ATTACK = 0x41
    QU_GATE_RELEASE = 0x42
    QU_GATE_HOLD = 0x43
    QU_GATE_THRESHOLD = 0x44
    QU_GATE_DEPTH = 0x45
    QU_GATE_IN_OUT = 0x46
    QU_COMP_TYPE = 0x61
    QU_COMP_ATTACK = 0x62
    QU_COMP_RELEASE = 0x63
    QU_COMP_KNEE = 0x64
    QU_COMP_RATIO = 0x65
    QU_COMP_THRESHOLD = 0x66
    QU_COMP_GAIN = 0x67
    QU_COMP_IN_OUT = 0x68
    QU_DELAY_TIME = 0x6C
    QU_DELAY_IN_OUT = 0x6D
    QU_UNKNOW_UNO = 0x56
    QU_UNKNOW_DUE = 0x47
    QU_UNKNOW_TRE = 0x48
    QU_UNKNOW_QUATTRO = 0x49


class QU_CHANNELS_LIST(IntEnum):
    QU_CHAN_1 = 0x20 
    QU_CHAN_2 = 0x21
    QU_CHAN_3 = 0x22
    QU_CHAN_4 = 0x23
    QU_CHAN_5 = 0x24
    QU_CHAN_6 = 0x25
    QU_CHAN_7 = 0x26
    QU_CHAN_8 = 0x27
    QU_CHAN_9 = 0x28
    QU_CHAN_10 = 0x29
    QU_CHAN_11 = 0x2A
    QU_CHAN_12 = 0x2B
    QU_CHAN_13 = 0x2C
    QU_CHAN_14 = 0x2D
    QU_CHAN_15 = 0x2E
    QU_CHAN_16 = 0x2F
    QU_CHAN_17 = 0x30
    QU_CHAN_18 = 0x31
    QU_CHAN_19 = 0x32
    QU_CHAN_20 = 0x33
    QU_CHAN_21 = 0x34
    QU_CHAN_22 = 0x35
    QU_CHAN_23 = 0x36
    QU_CHAN_24 = 0x37
    QU_CHAN_25 = 0x38
    QU_CHAN_26 = 0x39
    QU_CHAN_27 = 0x3A
    QU_CHAN_28 = 0x3B
    QU_CHAN_29 = 0x3C
    QU_CHAN_30 = 0x3D
    QU_CHAN_31 = 0x3E
    QU_CHAN_32 = 0x3F
    QU_CHAN_ST1 = 0x40
    QU_CHAN_ST2 = 0x41
    QU_CHAN_ST3 = 0x42
    
    QU_FX_RET_1 = 0x08
    QU_FX_RET_2 = 0x09
    QU_FX_RET_3 = 0x0A
    QU_FX_RET_4 = 0x0B

    QU_FX_SEND_1 = 0x00
    QU_FX_SEND_2 = 0x01
    QU_FX_SEND_3 = 0x02
    QU_FX_SEND_4 = 0x03

    QU_MIX_1 = 0x60
    QU_MIX_2 = 0x61
    QU_MIX_3 = 0x62
    QU_MIX_4 = 0x63
    QU_MIX_5_6 = 0x64
    QU_MIX_7_8 = 0x65
    QU_MIX_9_10 = 0x66
    QU_MIX_LR = 0x67

    QU_GROUP_1_2 = 0x68
    QU_GROUP_3_4 = 0x69
    QU_GROUP_5_6 = 0x6A
    QU_GROUP_7_8 = 0x6B

    QU_MTX_1_2 = 0x6C
    QU_MTX_3_4 = 0x6D

    QU_MUTE_1 = 0x50
    QU_MUTE_2 = 0x51
    QU_MUTE_3 = 0x52
    QU_MUTE_4 = 0x53

    QU_DCA_1 = 0x10
    QU_DCA_2 = 0x11
    QU_DCA_3 = 0x12
    QU_DCA_4 = 0x13


