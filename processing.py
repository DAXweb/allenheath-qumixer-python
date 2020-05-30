import socket
import threading
import sys
import enum
from enum import IntEnum

import globalsvars
import structs
import quzaia
import parservars

from structs import QuMixer


class QuProcessing:

    def __init__(self):
        pass
        

    #@brief:
    #   La funzione riceve come parametro un buffer ricevuto dal client
    #   e restituisce il tipo di pacchetto ricevuto
    #   in modo da poter essere successivamente gestito
    #
    #@return:
    #   QU_PACKET_TYPE  Il tipo del pacchetto o None in caso di errore
    #   int             0 OK, <0 Errore
    def get_received_packet_type(self,buffer, client):
        if (len(buffer) <= 0):
            print("- ERRORE : Errore funzione get_received_packet_type, il buffer ha dimensione {}. Atteso valore maggiore di 0".format(len(buffer)))
            return None, -1

        if (isinstance(client, quzaia.QuZaia) == False):
            printf("- ERRORE : parametro client non classe QuZaia")
            return None -1

        if (len(buffer) == 1 and buffer[0] == (0xfe)):
            return structs.QU_PACKET_TYPE.ACTIVE_SENSE_PACKET, 0
        
        if (len(buffer) == 14 and buffer[0] == (0xf0) and buffer[1] == 0x00 and buffer[2] == 0x00 and buffer[3] == 0x1A):
            return structs.QU_PACKET_TYPE.IDENTIFY_PACKET, 0

        #pacchetto di SYNC
        if (len(buffer) == 11 and buffer[0] == 0xf0 and buffer[1] == 0x00 and buffer[2] == 0x00 and buffer[3] == 0x1A 
                and buffer[9] == (0x14) and buffer[10] == 0xF7):
            return structs.QU_PACKET_TYPE.SYNC_PACKET, 0


        nrpnhead = client.buildNRPNHead(0xb, client.quMixer.quMidiChan)

        if (len(buffer) >=3 and buffer[0] == nrpnhead and (buffer[1] == 0x63 or buffer[1] == 0x62 or buffer[1] == 0x06 or buffer[1] == 0x26)):
            return structs.QU_PACKET_TYPE.NPRN_PACKET, 0 

        



        
                

        # print("- Debug : UNKNOW PACKET")
        return structs.QU_PACKET_TYPE.UNKNOW_PACKET, 0


    #@brief:
    #   Questa funzione è una funzione di alto livello
    #   gestisce il processamento dei vari pacchetti in base al tipo di
    #   pacchetto ricevuto
    #
    #@params:
    #   QU_PACKET_TYPE      Il tipo di pacchetto identificato
    #   bytes               Il buffer 
    #   QuZaia             Questo non mi piace molto, come è una referenza alla classe principale
    #
    #@return:
    #   int         0 OK, <0 Problemi
    def process_packets(self,packet_type, buffer, client):
        if (isinstance(packet_type, structs.QU_PACKET_TYPE) == False): return -1
        if (len(buffer) < 0): return -2
        if (isinstance(client, quzaia.QuZaia) == False): return -3

        sock = client.getSocket()
        
        if (packet_type == structs.QU_PACKET_TYPE.ACTIVE_SENSE_PACKET):
            # print("test pong")
            sock.send(b'\xfe')
            #tonzo = tonzo + 1
        

        #print("data len : {}" + str(len(data)))
        if (packet_type == structs.QU_PACKET_TYPE.IDENTIFY_PACKET):
            quMixerLocal, err = client.parsingEngine.parse_qumixer_response(buffer)
            if (err < 0):
                print("- ERRORE : Problema funzione parse_qumixer_response. Codice : {}".format(err))
                return -4

            print("- Debug : Pacchetto identificativo di risposta ricevuto")

            client.quMixer = quMixerLocal
            client.identified = True

            client.setProtocolState(structs.QU_PROTOCOL_STATE.RECEIVED_MIXER_IDENTIFICATION)

        #pacchetto sync ricevuto dal mixer
        if (packet_type == structs.QU_PACKET_TYPE.SYNC_PACKET):
            print("- Debug : Sync packet ricevuto")


        if (packet_type == structs.QU_PACKET_TYPE.NPRN_PACKET):
            #print("- Debug : Nrpn Packet. Numero comandi : {}".format(len(buffer) / 12))
            commands, count, err = client.parsingEngine.parse_nrpn_commands(buffer, client)
            if (err < 0):
                print("- ERRORE : parse_nrpn_commands ha avuto un errore. Codice : {}".format(str(err)))
                return

            if (err > 0):
                print("\n\n--------------------------------------------------\n- WARNING : Nella fase di parsing sono stati generati : {} " \
                    "warning.".format(str(err)))
            
            if (count >= 1):
                print("- Debug : OK - parsed {} cmd".format(str(count)))
                # print("- Debug : Comandi parsati da buffer : {}".format(str(len(commands))))
                for cmd in commands:
                    cmd.dump()
                    if (cmd.paramTypeEnum == structs.QU_PARAM_LIST.QU_FADER):
                        print("- Debug : Volume Chan {} - {} db".format(str(cmd.channelID),str(cmd.paramValue)))
            
            
        return 0
        

