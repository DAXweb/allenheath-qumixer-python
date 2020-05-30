import socket
import threading
import sys
from enum import IntEnum


#@brief
#   Crea un header sys ex ,se il parametro midiChan è diverso da 0
#   Inserisce il canale midi nel systex altrimenti genera una
#   sysex header (All Call) che usiamo la prima volta che contattiamo
#   il mixer per conoscere il canale midi da usare
#
#@return
#   buffer byte, il buffer byte sysex
#   int    0 OK, -1 annullato
def create_sysex_header(isAllMidi, midiChan):
    if (midiChan < 0):
        print("- ERRORE : midiChan valore minore di 0")
        return None, -1

    if (isAllMidi):
        return b'\xF0\x00\x00\x1A\x50\x11\x01\x00\x7F', 0
    
    #midichan è diverso da zero
    sysex_header_bytes = b'\xF0\x00\x00\x1A\x50\x11\x01\x00' + bytes([midiChan])
    

    # print("Stringa syshex header creata : {!r}".format(sysex_header_bytes))

    return sysex_header_bytes , 0


#@brief:
#   La funzione crea il pacchetto di identificazione con il 
#   sysex_header e l'ipad flag
#
#@return:
#   bytes   Ritorna un buffer byte 
#   int     Azione 0 OK, <0 errori
def create_initial_request_packet(sysex_header, iPadFlag):
    if (len(sysex_header) != 9):
        print("- ERRORE : create_initial_request_packet, attesa sysex header di 9 bytes. Ricevuto pacchetto con {} bytes".format(len(sysex_header)))
        return None, -1

    if (iPadFlag != 1):
        print("- WARNING : il valore iPadFlag è diverso da 1")

    packet = sysex_header + b'\x10' + bytes([iPadFlag]) + b'\xF7'

    # print("- Debug : Initial packet : {!r}".format(packet))

    return packet, 0



