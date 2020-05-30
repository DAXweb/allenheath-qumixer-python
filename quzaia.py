import socket
import sys
from random import randrange
import logging
import struct
import math
from enum import IntEnum
import selectors
import types
import random
from time import sleep

import processing
import protocols
import structs
import binascii
import parservars

class QuZaia:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.sock = None

        self.quProtocolState = 99

        #questa variabile viene popolata a True quando il mixer risponde con il pacchetto di identificazione
        self.identified = False

        #questa variabile viene popolata dalla funzione di parsing alla ricezione del pacchetto di identifiazione
        self.quMixer = None
        
        #selector
        self.sel = selectors.DefaultSelector()

        #counter
        self.counter = 1

        self.connected = False

        self.parsingEngine = parservars.QuParsing()
        self.processingEngine = processing.QuProcessing()



    def getQuMixerClass(self):
        return self.quMixer

    def isConnected(self):
        return self.connected

    
    def isIdentified(self):
        return self.identified


    def setProtocolState(self, state):
        if (isinstance(state, structs.QU_PROTOCOL_STATE) == False):
            print("- ERRORE: setPRotocolState, il valore passato non appartiene alla classe QU_PROTOCOL_STATE")
            return
        print("- Debug : Settato protocol state {}".format(str(state)))
        self.quProtocolState = state

    def getProtocolState():
        return self.quProtocolState

    def getSocket(self):
        return self.sock

    def counter_increment(self):
        self.counter += 1

    def get_counter(self):
        return self.counter

    def _start_connection(self):

        server_addr = (self.host, self.port)
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(True)
        self.sock.connect_ex(server_addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(inb=b'', outb=b'')
        self.sel.register(self.sock, events, data=data)

        while True:
            events = self.sel.select(timeout=None)
            for key, mask in events:
                if key.data is not None:
                    self._service_connection(key, mask)

    def _service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(4098)  # Should be ready to read
            if recv_data:
                data.outb += recv_data
            else:
                logging.debug('Close connection to')
                self.sel.unregister(sock)
                sock.close()
                self.connected = False

        if mask & selectors.EVENT_WRITE:
            if data.outb:
                # print('echoing', repr(data.outb))
                #sent = sock.send(data.outb)  # Should be ready to write
                self._process_data(data.outb)
                self.connected = True
                data.outb = b''

    def _connect(self):
        self._start_connection()

    def _process_data(self, data):
        # print("ricevuto data")
        # print("DUMP")
        # print("----")
        if (data[0] != 0xfe):
            print("\n-------------------------\nReceived : ", end="")
            for i in range(0, len(data)):
                print("{} ".format(hex(data[i])), end='')
            print("\n")

        packet_type, err = self.processingEngine.get_received_packet_type(data, self)
        if (err < 0):
            print("- ERRORE : get_received_packet_type : Ricevuto errore codice {} dalla funzione get_received_packet_type.".format(err))
            return

        err = self.processingEngine.process_packets(packet_type, data, self)
        if (err < 0):
            print("- ERRORE : process_apckets ... Ricevuto errore codice {}".format(err))

        




    def disconnect(self):
        #invia la richiesta di disconnessione
        pass

    def connect(self):
        print("- Debug : Connetto al server {}:{}".format(self.host, str(self.port)))
        self._connect()

    def identify(self):
        #midiChan sconosciuto, creiamo un sysex generico
        sysex_header, err = protocols.create_sysex_header(True, 0)
        if (err < 0):
            print("- ERRORE : protocols.create_sysex_header, uscita codice : {}".format(str(err)))
            return

        packet, err = protocols.create_initial_request_packet(sysex_header, 1)
        if (err < 0):
            print("- ERRORE : protocols.create_initial_request_packet. Codice : {}".format(str(err)))
            return

        self.getSocket().send(packet)

        self.setProtocolState(structs.QU_PROTOCOL_STATE.WAITING_QUMIXER_IDENTIFY_RESPONSE)
        
        print("- Debug : Inviata identificazione al client. In attesa di risposta")


    #@brief:
    #   La funzione crea il byte iniziale dei 3 necessario per ogni comando nrpn
    #   Accetta il parametro left_nibble e right_nibble..il right_nibble è il midi chan
    def buildNRPNHead(self, hex_lNibble, hex_rNibble):
        lNibble = (0b00001111 & hex_lNibble) << 4
        rNibble = (0b00001111 & hex_rNibble)
        res = lNibble + rNibble
        # print("- Debug : Valore risultante da {} e {} : {}".format(hex(hex_lNibble), hex(hex_rNibble), hex(res)))
        return res

    
    def test_notte_fonda_OBSOLETO(self, hexChan, hexVolume):
        print("Provo ad inviare qualcosa")
        delay = 0.02

        print("- Debug : MidiChan : {}".format(str(self.quMixer.quMidiChan)))
        nrpn_head = self.buildNRPNHead(0xb, self.quMixer.quMidiChan)
        print("- Debug : Repr Binario : {:b}".format(nrpn_head))
        
        sysex_header, err = protocols.create_sysex_header(False, self.quMixer.quMidiChan)
        if (err < 0):
            print("- ERRORE : create_sysex_header, problemi con la preparazione dell'header con canale midi popolato. Codice : {}".format(str(err)))
            return
        #                               B(N)
        packet1 = sysex_header + bytes([nrpn_head]) + bytes([0x63]) + bytes([hexChan])
        self.sock.send(packet1)
        sleep(delay)

        packet2 = sysex_header + bytes([nrpn_head]) + bytes([0x62]) + bytes([0x17])
        self.sock.send(packet2)
        sleep(delay)

        packet3 = sysex_header + bytes([nrpn_head]) + bytes([0x06]) + bytes([hexVolume])
        self.sock.send(packet3)
        sleep(delay)

        packet4 = sysex_header + bytes([nrpn_head]) + bytes([0x26]) + bytes([0x07])
        self.sock.send(packet4)
        sleep(delay)


    def test_sera_due(self, hexChan, hexVolume):
        print("Provo ad inviare qualcosa")
        delay = 0.02

        print("- Debug : MidiChan : {}".format(str(self.quMixer.quMidiChan)))
        nrpn_head = self.buildNRPNHead(0xb, self.quMixer.quMidiChan)
        print("- Debug : Repr Binario : {:b}".format(nrpn_head))
        
        sysex_header, err = protocols.create_sysex_header(False, self.quMixer.quMidiChan)
        if (err < 0):
            print("- ERRORE : create_sysex_header, problemi con la preparazione dell'header con canale midi popolato. Codice : {}".format(str(err)))
            return
        #                               B(N)
        packet1 = sysex_header + bytes([nrpn_head]) + bytes([0x63]) + bytes([hexChan])
        
        packet2 = sysex_header + bytes([nrpn_head]) + bytes([0x62]) + bytes([0x17])
        
        packet3 = sysex_header + bytes([nrpn_head]) + bytes([0x06]) + bytes([hexVolume])
        
        packet4 = sysex_header + bytes([nrpn_head]) + bytes([0x26]) + bytes([0x07])
        
        self.sock.send(packet1 + packet2 + packet3 + packet4)
        sleep(delay)


    #@brief:
    #   Questa funzione prepara un pacchetto nprn e lo restituisce come output
    #
    #@return:
    #   bytes       Ritorna il pacchetto composto dai 4 blocchi
    #   int         0 OK, <0 errore
    def prepare_fader(self, hexChan, hexVolume):
        # print("Provo ad inviare qualcosa")
        # delay = 0.02

        # print("- Debug : MidiChan : {}".format(str(self.quMixer.quMidiChan)))
        nrpn_head = self.buildNRPNHead(0xb, self.quMixer.quMidiChan)
        # print("- Debug : Repr Binario : {:b}".format(nrpn_head))
        
        sysex_header, err = protocols.create_sysex_header(False, self.quMixer.quMidiChan)
        if (err < 0):
            print("- ERRORE : create_sysex_header, problemi con la preparazione dell'header con canale midi popolato. Codice : {}".format(str(err)))
            return
        #                               B(N)
        packet1 = sysex_header + bytes([nrpn_head]) + bytes([0x63]) + bytes([hexChan])
        
        packet2 = sysex_header + bytes([nrpn_head]) + bytes([0x62]) + bytes([0x17])
        
        packet3 = sysex_header + bytes([nrpn_head]) + bytes([0x06]) + bytes([hexVolume])
        
        packet4 = sysex_header + bytes([nrpn_head]) + bytes([0x26]) + bytes([0x07])
        
        # self.sock.send(packet1 + packet2 + packet3 + packet4)
        # sleep(delay)
        return packet1 + packet2 + packet3 + packet4 , 0


        
