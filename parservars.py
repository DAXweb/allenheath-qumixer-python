import socket
import threading
import sys
from enum import IntEnum

import structs
from globalsvars import *
from structs import *
import quzaia



class QuParsing:

    def __init__(self):
                
        #questa variabile memorizza gli step del protocollo che sono avvenuti nel corretto ordine
        self.nrpn_state_recvs = 0
        #il tipo dell'ultimo pacchetto ricevuto
        # self.nrpn_state = structs.QU_NPRN_MESSAGE_STATE.NRPN_UNDEFINED
        #il buffer che conserva i 4 blocchi
        self.nrpn_cmd_buffer = [bytes(),bytes(),bytes(),bytes()]    #array di soli 4 elementi
        #la sequenza da rispettare
        self.nrpn_sequence = [
                        structs.NRPN_MESSAGE_SPECIFIER.NRPN_HEAD_MSB, 
                        structs.NRPN_MESSAGE_SPECIFIER.NRPN_HEAD_LSB,
                        structs.NRPN_MESSAGE_SPECIFIER.NRPN_DATA_MSB,
                        structs.NRPN_MESSAGE_SPECIFIER.NRPN_DATA_LSB]

    #@brief:
    #   Parsa la risposta del mixer e crea la classe QuMixer popolata
    #
    #@return:
    #   QuMixer     la classe QuMixer popolata, oppure None in caso di errori
    #   int         0 OK, <0 errore
    def parse_qumixer_response(self,buffer):
        error = 0
        quMixer = QuMixer()
        #print("- Qu Mixer A : " + str(data[4]))
        #quMi = data[4]
        #print("- Qu Mixer B : " + str(data[5]))
        #quMixB = data[5]
        
        #print("- Qu Mixer Major Version : " + str(data[6]))
        quMixer.quMixVersionMajor = buffer[6]
        #print("- Qu Mixer Minor Version : " + str(data[7]))
        quMixer.quMixVersionMinor = buffer[7]
        #print("- Qu Mixer Midi Chan : " + str(data[8]))
        quMixer.quMidiChan = buffer[8]
        
        if (buffer[9] != 0x11):
            print("Errore , atteso 0x11 e invece ricevuto : " + str(hex(buffer[9])))
            error += 1

        quMixer.quMixModel = QU_MIXER_MODELS(buffer[10])
        #print("- Qu Model : " + str(data[10]))
        quMixer.quMixFirmwareMajor = buffer[11]
        quMixer.quMixFirmwareMinor = buffer[12]
        #print("- Qu Firmware : " + str(data[11]) + "." + str(data[12]))

        if (buffer[13] != 0xF7):
            print("Errore , atteso 0xF7 e invece ricevuto : " + str(hex(data[13])))
            error += 1

        if (error == 0):
                print("- Debug : OK - Mixer riconosciuto correttamente")
                return quMixer, 0
        else:
            print("- Log : ERRORE - Mixer non ha risposto correttamente al pacchetto iniziale di identificazione")
            return None, -1


    #@brief:
    #   La funzione riceve un buffer di byte e scorre tutto il contenuto
    #   cercando i comandi nrpn nel messaggio
    #   quando lo trova crea la classe NrpnCommands
    #   e la aggiunge all'array
    #
    #@return:
    #   list        array di nrpncommands
    #   int         numero di comandi completi parsati
    #   int         0 OK, <0 errore
    def parse_nrpn_commands(self,buffer, client):
        
        cursor = 0
        len_buffer = len(buffer)
        
        commands = []

        nrpn_head = client.buildNRPNHead(0x0b, client.quMixer.quMidiChan)

        warning_count = 0

        #trova un bu
        #0xb5 0x63 0x20
        #0xb5 0x63 0x20     0xb5 0x62 0x17 

        #fin quando il cursore è all'interno del buffer
        while ((cursor + 2) < len_buffer):
            # print("- Debug : Inizio ciclo cursore posizione {}".format(str(cursor)))
            block = buffer[cursor:cursor+3]
            specifier = buffer[cursor + 1]
            
            last_index = 0
            nrpn_found = False
            for i in range(0,4):
                #cerca di itentificare lo specificatore del comando nrpn in modo da capirne il blocco
                if (specifier == self.nrpn_sequence[i]):
                    # print("- Debug : trovato specificatore nrpn . Valore {}".format(hex(specifier)))
                    
                    # self.nrpn_state = i
                    # print("- Debug : impostato state a  {}".format(str(self.nrpn_state)))

                    #memorizza il blocco
                    self.nrpn_cmd_buffer[i] = block
                    nrpn_found = True

                    last_index = i
            
            if (not nrpn_found):
                cursor += 1
                # print("- ERROR : specificatore {} non identificato nella sequenza. avanzo il cursore di 1 e ricomincio.".format(str(cursor)))
                # warning_count += 1
                self.nrpn_state_recvs = 0
                self.nrpn_cmd_buffer = [bytes(),bytes(),bytes(),bytes()]
                self.nrpn_state = structs.QU_NPRN_MESSAGE_STATE.NRPN_UNDEFINED
                continue
                
            #-----SPECIFICATORE RICONOSCIUTO----------
            #controlla se gli step sono stati rispettati prima di incrementare il valore
            #se i è = 0, vuol dire che è il primo step
            if (last_index == 0):
                self.nrpn_state_recvs = 1
                # print("- Debug : primo step identificato. incremento nrpn_state_recvs. Valore attuale : {}".format(str(self.nrpn_state_recvs)))
            elif (last_index >= 1 and last_index <= 3):
                # print("- Debug : step tra 1 e 3. Valore {}".format(str(last_index)))
                #cioè..dal secondo step fino al 4..controlla che lo step precedente sia stato ricevuto
                if (self.nrpn_state_recvs == last_index):
                    self.nrpn_state_recvs += 1
                else:
                    print("- ERROR : sequenza nrpn non rispettata. nrpn_state_Recvs doveva essere {} invece è {}".format(last_index,self.nrpn_state_recvs))
                    cursor += 1
                    warning_count += 1
                    self.nrpn_state_recvs = 0
                    self.nrpn_cmd_buffer = [bytes(),bytes(),bytes(),bytes()]
                    self.nrpn_state = structs.QU_NPRN_MESSAGE_STATE.NRPN_UNDEFINED
                    continue


            #controlla se il valore nrpn_state_recvs ha raggiunto 4 e nel caso parsa il comando
            if (self.nrpn_state_recvs == 4):
                # print("- Debug : nrpn_state_recvs arrivato a 4...tutti gli step sono stati ricevuti")
                # print("- Debug : Parsing del buffer")

                #assert dimensione buffer dei sotto comandi
                if (len(self.nrpn_cmd_buffer) != 4):
                    print("- ERRORE : nrpn_cmd_buffer deve essere 4, invece la dimensione attuale è : {}".format(len(self.nrpn_cmd_buffer)))
                    warning_count += 1
                    cursor += 3
                    self.nrpn_state_recvs = 0
                    self.nrpn_cmd_buffer = [bytes(),bytes(),bytes(),bytes()]
                    self.nrpn_state = structs.QU_NPRN_MESSAGE_STATE.NRPN_UNDEFINED
                    continue

                #controllo sicurezza che ogni blocco sia di 3 byte
                wrong_size = False
                for k in range(0,4):
                    if ( len(self.nrpn_cmd_buffer[k]) != 3):
                        print("- ERRORE : il block buffer di ogni step nrpn deve essere composto da 3 byte. L'elemento {} " \
                                "del nrpn_cmd_buffer ha {} bytes".format(str(k), len(self.nrpn_cmd_buffer[k])))
                        wrong_size = True

                if (wrong_size):        
                    cursor += 3
                    warning_count += 1
                    self.nrpn_state_recvs = 0
                    self.nrpn_cmd_buffer = [bytes(),bytes(),bytes(),bytes()]
                    self.nrpn_state = structs.QU_NPRN_MESSAGE_STATE.NRPN_UNDEFINED
                    continue
                        

                # print("- Debug : Dimensione nrpn_cmd_buffer : {}".format(str(len(self.nrpn_cmd_buffer))))
                #parso i parametri
                new_cmd = NrpnCommand()
                new_cmd.channelID = self.nrpn_cmd_buffer[0][2]
                new_cmd.channelTypeEnum = structs.QU_CHANNELS_LIST(self.nrpn_cmd_buffer[0][2])
                new_cmd.paramID = self.nrpn_cmd_buffer[1][2]
                new_cmd.paramTypeEnum = structs.QU_PARAM_LIST(self.nrpn_cmd_buffer[1][2])
                new_cmd.paramValue = self.nrpn_cmd_buffer[2][2]
                new_cmd.extraParamValue = self.nrpn_cmd_buffer[3][2]

                commands.append(new_cmd)
                # print("- Debug : Aggiunto nuovo comando")

            #incrementa cursore
            # print("- Debug : Fine ciclo - cursore + 3")
            cursor += 3
                

            

        return commands, len(commands), 0 + warning_count