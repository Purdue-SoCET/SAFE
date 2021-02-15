#Learn multithreading from https://gist.github.com/oleksiiBobko/43d33b3c25c03bcc9b2b 
#Learn multithreading from https://github.com/Purdue-SoCET/ici 
import socket
import threading
global NPRtoNSR_table
global NAStable
BUFFER_SIZE = 1000
MAX_SOCKETS_PROCESS = 5
MAX_SOCKETS_SYSTEM = 3

class NAS:
    def __init__(self,NPR,senderCAST,receiverCAST):
        self.buffer = [] * BUFFER_SIZE
        self.NSAST = NPRtoNSRtable[NPR.NPAST]
        self.offset = NPR.offset
        self.senderCAST = sender
        self.receiverCAST = receiver
        self.headpointer = 0
        self.tailpointer = 0
        self.MN_queue = []
        #unicast, so only two sockets one for inbound and other for outbound
        senderSocket = NSASTtoSocket[CAS[senderCAST].NSAST]
        receiverSocket = NSASTtoSocket[CAS[receiverCAST].NSAST]
                    
    def readbyte():
        byte = buffer[self.headpointer % BUFFER_SIZE]
        self.headpointer = self.headpointer + 1
        return byte

    def writebyte(byte):
        buffer[(self.tailpointer + 1) % BUFFER_SIZE] = byte
        self.tailpointer = self.tailpointer + 1
        return self.tailpointer

def writetoNAS(byte, NPAST, writer_CAST):
    NSAST = CAS[CAST].socketTranslationTable[NPAST].NSAST
    offset = CAS[CAST].socketTranslationTable[NPAST].tailpointer
    tailpointer = NAStable[NSAST].writebyte(byte)
    update(CAS[CAST], tailpointer)
    NPRaddr = (NPAST,offset)

def readfromNAS(NPAST, reader_CAST):
    NSAST = CAS[CAST].socketTranslationTable[NPAST].NSAST
    offset = CAS[CAST].socketTranslationTable[NPAST].headpointer
    return NAStable[NSAST].readbyte()


class MN_Queue:
    def __init__(self):
        self.buffer = []
        self.head_pointer = 0
        self.tail_pointer = 0
        self.message = 0
    def insert(data):
        self.buffer[tail_pointer] = data
        self.tail_pointer += 1
    def remove(data):
        self.head_pointer -= 1
        return self.buffer[self.head_pointer]

global MAX_PROCESS_PMU
MAX_PROCESS_PMU = 5
class SNE:
    def __init__(self,num_socket):
        self.MN_queue = MN_Queue()                                   #Single MN Queue of SNE
        self.NAS = [[None] * 1024] * MAX_SOCKETS_SYSTEM              #NAS buffer (socket)
        self.socket_table = [[[[None] * MAX_SOCKETS_SYSTEM] * MAX_SOCKETS_PROCESS] * MAX_PROCESS_PMU]   #[NSAST, NPAST, CAST]
        self.thread_list = []                               #active threads of each socket
        self.run(num_socket)
    def thread_function(self,socket_index, data):
        while True:        
            self.NAS[socket_index].append(data)
    def run(self,num_threads):
        for i in range(num_threads):
            self.thread_list.append(threading.Thread(thread_function,args=(self,i,data),name=str(i))
            self.thread_list[i].start()
        for i in range(num_threads):
            self.thread_list[i].join()

def lookup_CAS(NPAST):
    CAS[NPAST]

class Socket:
    buff = []
    def __init__(self):
        self.buff
        self.headpointer = 0


class NSR:
    #Table 16 (1x)
    def __init__(self,NSAST,offset):
        self.NSAST = NSAST
        self.offset = offset
        self.sneindex = 0 #one SNE in system
        self.index = NSAST
        self.ST = 0 #source/target
        self.type = 0 #has to be 0 to be an NSR

class NPR:
    def __init__(self,NPAST,offset,ST):
        self.NPAST = NPAST
        self.offset = offset
        self.sneindex = 0 #one SNE in system
        self.index = NSAST
        self.AB = 0 #source/target
        if ST is 0:
            self.type = 510 #has to be 510 to be a source NPR
            self.AB = 0 #none of the cache lines are discarded
        else:
            self.type = hex(3FFFFBFFFFFF)

#def NPR_to_NSR():
class MNMessage():
    def __init__(self,sourceCAST,metadata,data)
class MNSR:
    def __init__(self,sourceCAST,targetCAST,metadata,data):


