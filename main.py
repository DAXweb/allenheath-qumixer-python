from mido.sockets import PortServer, connect
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

import threading
from threading import Thread

import globalsvars
import structs
import quzaia
import processing
import protocols
import parservars

import sys


CUSTOM_DEBUG = 1

HOST = "192.168.1.48"  # Standard loopback interface address (localhost)
PORT = 51325        # Port to listen on (non-privileged ports are > 1023)



quZaia = ""        

class Worker(Thread):
    def __init__(self, name, client):
        Thread.__init__(self)
        self.name = name
        self.client = client

    def run(self):
        self.thread_parallelo()

    def kill(self):
        self.client.disconnect()
        raise SystemExit() 

    def thread_parallelo(self):
        print("- Log : Waiting qu-mixer connection...")
        waiting_counter = 0
        delay_counter = 0.25
        waiting_seconds = 15
        while(not self.client.isConnected()):
            sleep(delay_counter)
            print("- Log : ...")
            waiting_counter += 1
            if (waiting_counter >= (waiting_seconds / delay_counter)): #15 secondi diviso
                print("- Log : Qu-Mixer doesn't respond. E' acceso cojò???")
                quZaia.disconnect()
                return
    

        #Una volta che il mixer è connesso procedo con l'identificazione
        self.client.identify()

        print("- Log : Waiting qu-mixer identification packet...")
        waiting_counter = 0
        delay_counter = 0.25
        waiting_seconds = 15
        while(not self.client.isIdentified()):
            sleep(delay_counter)
            print("- Log : ...")
            waiting_counter += 1
            if (waiting_counter >= (waiting_seconds / delay_counter)): #15 secondi diviso
                print("- Log : Qu-Mixer doesn't respond. Ce dev'esse n'erore Pierì")
                self.client.disconnect()
                return

    
        print("- Log : Mixer identificato correttamente")
        quMixer = self.client.getQuMixerClass()
        if (quMixer == None):
            print("- ERRORE : il memebro quMixer della classe QuZaia è nullo.")
            self.client.disconnect()
            return
        quMixer.dump()


        line = sys.stdin.readline()
        while (len(line) >= 0 and line[0] != "q"):
            if (line[0] == "a"):
                print("- Log : Pressed A")
                buffo = self.client.prepare_fader(0x20, 0x7C)[0]
                buffo += self.client.prepare_fader(0x21, 0x7C)[0]
                buffo += self.client.prepare_fader(0x22, 0x7C)[0]
                buffo += self.client.prepare_fader(0x24, 0x7C)[0]
                self.client.sock.send(buffo)
            elif (line[0] == "b"):
                print("- Debug : Pressed B")
                buffo = self.client.prepare_fader(0x20, 0x0C)[0]
                buffo += self.client.prepare_fader(0x21, 0x0C)[0]
                buffo += self.client.prepare_fader(0x22, 0x0C)[0]
                buffo += self.client.prepare_fader(0x24, 0x0C)[0]
                self.client.sock.send(buffo)
            elif (line.find("vegas") != -1):
                print("- Debug : Vegas Mode Attivata")
                complete = False
                vegas_chan = 0x20
                vegas_delay = 0.4 #un secondo
                vegas_volume = 0x7C
                while(not complete):
                    for i in range(0,16):
                        self.client.test_notte_fonda_OBSOLETO(vegas_chan, vegas_volume)
                        #avanzo il canale
                        vegas_chan += 1
                        sleep(vegas_delay)
                    
                    vegas_volume = 0x0C
                    vegas_chan-=1
                    for i in range(0,16):
                        self.client.test_notte_fonda_OBSOLETO(vegas_chan, vegas_volume)
                        #avanzo il canale
                        vegas_chan -= 1
                        sleep(vegas_delay)
                    
                    complete = True
                print("- Debug : Vegas Mode completato")
            else:
                print("- Debug : line : {}".format(line))

            line = sys.stdin.readline()
            


        print("- Log : Per ora fine processo ... ")
        self.client.disconnect()

        



class QuClientThread(Thread):
    def __init__(self, name, client):
        Thread.__init__(self)
        self.name = name
        self.client = client

    def kill(self):
        raise SystemExit() 

    def run(self):
        self.client.connect()
        


def main():
    quZaia = quzaia.QuZaia(HOST, PORT)

    client_thread = QuClientThread("Client", quZaia)
    client_thread.start()

    worker_thread = Worker("Working", quZaia)
    worker_thread.start()
    worker_thread.join()


    
if __name__ == "__main__":
    main()