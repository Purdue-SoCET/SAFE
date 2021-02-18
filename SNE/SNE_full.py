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

global QUEUE_SIZE
QUEUE_SIZE = 100
class MN_Queue:
    def __init__(self):
        self.buffer = []
        self.head_pointer = 0
        self.tail_pointer = 0
    def insert(message):
		if (tail_pointer < QUEUE_SIZE):
        	self.buffer[tail_pointer] = message
		else:
			return False
        self.tail_pointer += 1
		return True
    def remove(data):
        self.head_pointer -= 1
		if (self.head_pointer >= 0):
        	return self.buffer[self.head_pointer]
		else:
			return False
#MN Notification format where tx means sender else receiver
# the sender's CAST is present in the MN packet
# the payload is attached
class MN_Notification:
    def __init__(self, tx = True, time, senderCAST, payload):
        self.tx = tx
        self.time = time
        self.senderCAST = senderCAST
        self.payload = payload
        self.buffer = None
        if tx is False:
            self.dissect()			
    def packetize(self):
        self.buffer = (self.time, self.senderCAST, self.payload)
        return self.buffer
    def dissect(self):
        self.time = self.buffer[2]
        self.senderCAST = self.buffer[1]
        self.payload = self.buffer[0]
	

global MAX_PROCESS_PMU
MAX_PROCESS_PMU = 5
#Let process A interact with 5 NPASTs
#5 NPASTs map to 3 NSASTS
#this mapping is stored in a table
#Process A(CAST) is assoc with 5 NPAST is assoc with 3 NSASTs
#maybe an interaction with MN queue, when data is received and MN queue has a read 
#PMU would add to MN queue until the queue is fulled. 
#no need handshake, fixed buffer of lets say 6 bytes, sync byte to say its done
class SNE:
    def __init__(self,num_socket):
        self.MN_queue = MN_Queue()                                   #Single MN Queue of SNE
        self.NAS = [[None] * 1024] * MAX_SOCKETS_SYSTEM              #NAS buffer (socket)
        self.socket_table = [[[[None] * MAX_SOCKETS_SYSTEM] * MAX_SOCKETS_PROCESS] * MAX_PROCESS_PMU]   #[NSAST, NPAST, CAST]
        self.thread_list = []                               #active threads of each socket
        self.run(MAX_SOCKETS_SYSTEM)
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
    return CAS[NPAST]



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

