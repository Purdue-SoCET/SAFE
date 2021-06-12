import math
import random
from LLS import *
from createfiles import createFiles, initFiles

MAX_DSAST_OFFSET = 0
dsastlist = []

class cache:
    def __init__(self, level): 
        self.level = level
        self.ways = 4
        self.line_size = 6 + self.level + self.level
        self.block_size = int((2) * math.pow(4, self.level))    ##Block size in word  L1 = 2 word L2 is 8 word
        self.block_shift = 1 + self.level * 2
        self.reserve_bit = 2 + 4 * self.level
        if(self.level == 0):
            self.direct_size = 8 
        elif(self.level == 1):
            self.direct_size = 12 
        elif(level == 2):
            self.direct_size = 22 
        elif(self.level == 3):
            self.direct_size = 5 #26 #  L4 #self.cache_size - log2(self.ways) #10
        elif(self.level == 4):
            self.direct_size = 8 #27 # L5 #self.cache_size - log2(self.ways) #10
        self.up = level - 1 
        self.down = level + 1       
        self.cache_mask = (1 << (self.line_size + self.block_shift + 2 )) - 1
        self.block_mask = (self.block_size) - 1
        self.line_tag = [[0 for y in range(self.ways)] for x in range(1 << self.line_size)] #[0] * (1 << self.cache_size)
        self.tag_offset = 2 + self.block_shift + self.line_size         #here might be an issue
        #Data segment of cache block TODO:Need change so that I can access word on each offset (set the block as word)
        self.line_data = [[[0 for z in range(self.block_size)] for y in range(self.ways)] for x in range(1 << self.line_size)] #[0] * (1 << self.cache_size)
        #Dirty Bit and invalid bit segment of cache block
        #0 means valid non dirty, 1 means valid dirty, 2 mean invalid cache_line
        self.line_state = [[0 for y in range(self.ways)] for x in range(1 << self.line_size)] #[0] * (1 << self.cache_size)
        for i in range(0, self.ways):
            for j in range(0, 1 << self.line_size):
                self.line_state[j][i] = 2

    def index(self, addr):
        return ((addr) & self.cache_mask) >> (self.block_shift + 2)

    def block(self, addr):
        return (addr >> 2) & self.block_mask

    def get_way(self, addr):
        hit_way = -1
        idx = self.index(addr)
        for i in range(self.ways):
                if((addr >> self.tag_offset) == self.line_tag[idx][i]):
                    hit_way = i
        return hit_way 

    def lookup(self, addr):
        idx = self.index(addr) 
        return_way = self.get_way(addr)
        if return_way != -1 :
            return self.line_state[idx][return_way] != 2
        else:
            return False

    def find_way(self, addr, idx):
        way_list = []
        for i in range(0, self.ways):
            if(self.line_state[idx][i] != 1) :
                way_list.append(i)
        if(len(way_list) > 0):
            return random.choice(way_list)
        return random.randint(0, self.ways - 1)

    def replace(self,addr):
        global MAX_DSAST_OFFSET
        global dsastlist
        x = self.index(addr)
        block_index = self.block(addr)
        way_to_replace = self.find_way(addr, x)
        if(self.line_state[x][way_to_replace] == 1):
            if(self.level != 4):
                for i in range(0, self.block_size):
                    block_addr = addr & ~(self.block_mask << 2) ^ (i << 2)  # need testing
                    caches[self.down].put(addr, self.line_data[x][way_to_replace][i])
                self.line_state[x][way_to_replace] = 0
            else:
                for i in range(0, self.block_size):
                    block_addr = addr & ~(self.block_mask << 2) ^ (i << 2)  # need testing
                    # NOTE: for now, consider bits 31:0 as the offset of the DSAST until we extend the 
                    #       cache address to 72 bits. 63:32 is the DSAST
                    adsast_offset = block_addr & 0x0000FFFF
                    global_dsast = DSAST(address=block_addr, wayLimit=way_to_replace, lineLimit=self.line_size, size=1, offset=adsast_offset)
                    # line_data[x][way_to_replace][i] = writeLLS(global_dsast, line_data[x][way_to_replace][i])
                    if(global_dsast.offset > MAX_DSAST_OFFSET):
                        MAX_DSAST_OFFSET = global_dsast.offset 
                    writeLLS(global_dsast, 0x5555)
                    found = 0
                    for dsast in dsastlist:
                        if(global_dsast.dsast == dsast):
                            found = 1
                            break
                    if not found:
                        dsastlist.append(global_dsast.dsast)
                    # print("Writing to LLS, line: {}".format(line_data[x][way_to_replace][i]))
                    #               caches[self.down].put(line_tag[x][way_to_replace],line_data[x][way_to_replace][block_index])
                    #
                    #caches[self.down].put(addr, self.line_data[x][way_to_replace][block_addr])
    #                print("Miss in all Cache Levels. Going to LLS, dirty data", self.line_data[x][way_to_replace][block_addr], " is written")
                self.line_state[x][way_to_replace] = 0

        if(self.level != 4):
            self.line_tag[x][way_to_replace] = addr >> self.tag_offset
    #        print("Replacing tag ", self.line_tag[x][way_to_replace])
            for i in range(0, self.block_size):
                block_addr = addr & ~(self.block_mask << 2) ^ (i << 2)      #need testing
                self.line_data[x][way_to_replace][i] = caches[self.down].get(block_addr)
        #        print("Writing addr ", hex(addr), " with data ", self.line_data[x][way_to_replace][i], " among replacement in Cache level ", self.level)
        else:
            ##open the file , outbox for LLS, read, write req, out box 
        #    print("Miss in all Cache Levels. Going to LLS, dummy data received")
            #DSAST use = 71-50 bit of ADDR
            #61-20
            # print("Block size {}".format(self.block_size))
            # 512
            for i in range(0, self.block_size):
                block_addr = addr & ~(self.block_mask << 2) ^ (i << 2)  # need testing
                adsast_offset = block_addr & 0x0000FFFF
                global_dsast = DSAST(address=block_addr, wayLimit=way_to_replace, lineLimit=self.line_size, size=1, offset=adsast_offset)
                
                if(global_dsast.offset > MAX_DSAST_OFFSET):
                    MAX_DSAST_OFFSET = global_dsast.offset 
                self.line_data[x][way_to_replace][i] = readLLS(global_dsast)
                found = 0
                for dsast in dsastlist:
                    if(global_dsast.dsast == dsast):
                        found = 1
                        break
                if not found:
                    dsastlist.append(global_dsast.dsast)
                # print("dsast: {}".format(global_dsast))
                # print("Reading from LLS, line: {}".format(self.line_data[x][way_to_replace][i]))
                
            self.line_state[x][way_to_replace] = 0
        self.line_tag[self.index(addr)][way_to_replace] = addr >> self.tag_offset
        return way_to_replace

    def get(self, addr):
     #   print(addr)
        if(not self.lookup(addr)):
         #  print("It's a miss in level", self.level)
           #Miss list 
           miss[self.level] += 1
           insrt_way = self.replace(addr)
           return self.line_data[self.index(addr)][insrt_way][self.block(addr)] 
        else:
         #   print("It's a hit in level ", self.level)
            hits[self.level] += 1
            hit_way = self.get_way(addr)          
            return self.line_data[self.index(addr)][hit_way][self.block(addr)]

    def put(self,addr,data):
        write_way = -1
        self.addr = addr
        #self.data = data
        if not self.lookup(self.addr):  
           insrt_way = self.replace(self.addr)
           write_way = insrt_way   
        else:
            write_way = self.get_way(addr)
        print("Insert at index ",self.index(self.addr))
        self.line_data[self.index(addr)][write_way][self.block(addr)] = data
        self.line_state[self.index(addr)][write_way] = 1
        print("Writing addr ", hex(addr), " with data " , data," among put in Cache level ", self.level, "at way ", write_way)
    
    def hit_rate(self):
        print("Hit rate at level", self.level)
        print(hits[0])
        print(" L1 Hit Rate = ", hits[0] /(hits[0] + miss[0]))
        print(" L2 Hit Rate = ", hits[1] /(hits[1] + miss[1]))
        print(" L3 Hit Rate = ", hits[2] /(hits[2] + miss[2]))
        print(" L4 Hit Rate = ", hits[3] /(hits[3] + miss[3]))
        if(hits[4] > 0):
            print(" L5 Hit Rate = ", hits[4] /(hits[4] + miss[4]))
        else:
            print(" L5 Hit Rate = 0")

# class LLScache:
    
#     def __init__(self, cache_size, block_size):
#        #L2cache.i += 1
#        self.LLShits = 0
#        self.LLSmiss = 0
#     # def make_dsast(self, addr):
#     #     return(DSAST(size=0, index=addr, linelimit=0, waylimit=1))

#     def get(self, addr):
#         self.LLShits += 1
#         return readLLS(addr)
#         # adsast = DSAST()

#     def put(self,addr,data):
#         return writeLLS(addr, data)

#     def hit_count(self):
#         print(" LLS Hits = ", self.LLShits)


caches = []
miss = []
hits = []
global_dsast = DSAST()
mapBASTtoDSAST(global_dsast)
#SNE#
from SNE import *
MAX_SYS_SOCKET = 2
CAST_PMU = 1
CAST_SNE = 8
CAST_SAL = 16
READ = 0
WRITE = 1
global ACK
#semaphores of each thread/socket/NAS
#semaphores of each thread/socket/NAS
ACK = [threading.Semaphore(value=1)] * MAX_SYS_SOCKET

#message format: NPAST, CAST, NSAST
"""
SNE:
the SNE is a network proxy that is managed by a separate embedded system. This containerization makes it more secure than
running the networking stack the kernel.
Currently supports IPC across two processes. Next, need to connect to external IP with HTTP methods
"""
class SNE:
	"""
	__init__:
	Constructor that initializes the SNE. The SNE has an MN queue for message notifications indicating either setup/packet send/ teardown. It has a control table
	that indicates which NAS is busy/active and a local L3 cache. It has multiple threads running per NAS that iteract with the TCP/IP stack
	"""
	def __init__(self):
		self.MN_Queue = MN_queue() #Message Notification q ueue of the SNE
		self.control_table = [0] * MAX_SYS_SOCKET #The state of the socket/NAS. is it active/idle.
		self.CAST_SNE = 17 #The CAST/PID of the SNE
		#self.L3_cache = L3cache() #The local L3 cache
		self.system_sockets =[threading.Thread(thread_function,args=(self,NSAST),name=str(i)) for i in range(2 * MAX_SYS_SOCKET)] #2x because two address spaces. one for rx and tx
		self.message = 0 #the current message that is being read by the SNE.
		#Socket remote connection. MAX_SYS_SOCKET number of threads are being run and started by __init__. The argument passed is the socket
		#handle.
		#multiply MAX by 2 since there is two address spaces that are orthogonal. one for rx and the other for tx
		for NSAST in range(2 * MAX_SYS_SOCKET):
			socket_NSAST = remote('127.0.0.1', 3000 + NSAST)
			ACK[NSAST].acquire()
			self.system_sockets[NSAST].start(self, NSAST)
		self.main()
	"""
	thread_function:
	each socket/NSAST runs a parallel thread that receives a packet via the L3 cache from the SAL.
	this packet is passed into the TCP/IP stack and a new packet coming from it (IP packet) is passed in to the NAS.
	the NAS has a local copy in the L3 cache. the new packet is written into this address space.
	"""
	def thread_function(self, NSAST):
		while (True):
			ACK[NSAST].acquire()
			#buff = cache.get(NSAST << )
			buff = Cache_Hierarchy(READ,NSAST,None)		#read from the NAS address of the Cache Hierarchy. this is the packet coming from the PN via the SAL
			self.system_sockets[NSAST].send(buff) #send this packet into the TCP/IP stack for it to become a TCP/IP packet
			time.sleep(1) #wait for the packet to be sent into the stack
			inv_NSAST = 3000 + MAX_SYS_SOCKET + NSAST #use the other orthogonal address space a.k.a invert it
			buff_ip = self.system_sockets[inv_NSAST].recv(buff) #receive the ip packet from TCP/IP stack and pass it into a buffer
			#cache.put(NSAST << ,buff_ip)
			Cache_Hierarchy(WRITE,inv_NSAST,buff_ip)  #write this buffer into the Cache Hierarchy
			ACK[NSAST].release()	
	"""
	main:
	Needs to be called to start the SNE. This is the entry point. It first reads valid message from the MN queue.
	Then checks if the message is a setup or a read/write.   
	"""
	def main(self):
		while (True):
			#message = MN_decode(cache.get(CAST_SNE << 2))
			message = MN_decode(Cache_Hierarchy(READ,CAST_SNE, None)) #read the MN address space of SNE and decode the message
			if (MN_decode(message).valid == True): # check if the message is valid
				if (MN_decode(message).setup == True): #check if it is a setup message or an actual read/write message
					for i in range(MAX_SYS_SOCKET): #find available socket and enable/activate it
						if (self.control_table[MAX_SYS_SOCKET].enable == 0):
							self.control_table[MAX_SYS_SOCKET].enable = 1
							break
						NSAST = i
						self.control_table[i].NPAST = MN_decode(message).NPAST #the control table should also store the NPAST that is used for this socket
						self.control_table[i].CAST = MN_decode(message).CAST #it should also store which CAST/PID this socket is attached to now
					#cache.put(CAST_PMU << 2, MN_encode(NSAST))
					Cache_Hierarchy(WRITE,CAST_PMU,MN_encode(NSAST)) #it should send/write the NSAST that the SNE selected to the PMU
				#setup is done
				elif (MN_decode(message).read): #for read/write 
					if MN_decode(message).read: #the message is a read and the message also contains the NSAST 
						if (message.valid):
							NSAST = MN_decode(message).NSAST
							ACK[NSAST].release() #release the lock so that the thread can acquire in an run its code
					#writes are tougher and more complicated. needs more work for writes
					#else if MN_decode(message).write:
					#	Cache_Hierarchy(WRITE,MN_encode(NSAST, CAST_SNE, NPAST) + ,None)	
					#	Cache_Hierarchy(WRITE,MN_decode(message).NSAST,None)				
#SNE#
def main():
    createFiles(300)
    initFiles(300, 80000)
	SNE()
    global caches
    for i in range(5):
        caches.append(cache(i))
    global miss
    global hits
    miss = [0 for x in range(5)]
    hits = [0 for x in range(5)]
    #filename = "gcc_ld_trace.txt"
    input_addr = 0x1110
    print("test1")
    caches[0].put(0x1110,230) #Do testing # Generate random address #Add another core # Generate rand addr #
    #L1 block 0, index 34, tag 8
    #l2 block 8 index 68 , tag 0
    caches[0].put(0x1114,250)
    caches[0].put(0x1118, 255)
    caches[0].put(0x111C, 260)
    print(caches[0].get(0x1110))
    print(caches[0].get(0x1114))
    print(caches[0].get(0x1118))
    print(caches[0].get(0x111C))
    caches[0].put(0x8001110, 1000)
    caches[0].put(0x8001114,1024)
    caches[0].put(0x8001118, 1034)
    caches[0].put(0x800111C, 2000)
    print(caches[0].get(0x8001110))
    print(caches[0].get(0x8001114))
    print(caches[0].get(0x8001118))
    print(caches[0].get(0x800111C))
    caches[0].put(0x4001110, 3000)
    caches[0].put(0x4001114,3024)
    caches[0].put(0x4001118, 3034)
    caches[0].put(0x400111C, 3500)
    print(caches[0].get(0x4001110))
    print(caches[0].get(0x4001114))
    print(caches[0].get(0x4001118))
    print(caches[0].get(0x400111C))
    caches[0].put(0xa001110, 5000)
    caches[0].put(0xa001114,5024)
    caches[0].put(0xa001118, 5034)
    caches[0].put(0xa00111C, 5500)
    print(caches[0].get(0xa001110))
    print(caches[0].get(0xa001114))
    print(caches[0].get(0xa001118))
    print(caches[0].get(0xa00111C))
    caches[0].put(0xd001110, 8000)
    caches[0].put(0xd001114, 8024)
    caches[0].put(0xd001118, 8034)
    caches[0].put(0xd00111C, 8500)
    print(caches[0].get(0xd001110))
    print(caches[0].get(0xd001114))
    print(caches[0].get(0xd001118))
    print(caches[0].get(0xd00111C))
    print(caches[0].get(0x1110))
    print(caches[0].get(0x1114))
    print(caches[0].get(0x1118))
    print(caches[0].get(0x111C))
#    with open("go_ld_trace.txt") as f:
#        content = f.readlines()
    # remove whitespace characters at the end of each line
#    content = [x.strip() for x in content]
 #   for i in range(int(len(content))):
 #            caches[0].get(int(content[i], 16))
    caches[0].hit_rate()
    print("Number of hits in L1", hits[0])
    print("Number of misses in L1", miss[0])
    print("Number of hits in L2", hits[1])
    print("Number of misses in L2", miss[1])
    print("Number of hits in L3", hits[2])
    print("Number of misses in L3", miss[2])
    print("Number of hits in L4", hits[3])
    print("Number of misses in L4", miss[3])
    print("Number of hits in L5", hits[4])
    print("Number of misses in L5", miss[4])

    global MAX_DSAST_OFFSET
    print("MAX_DSAST_OFFSET: {}".format(MAX_DSAST_OFFSET))

    global dsastlist
    for dsast in dsastlist:
        print("dsast: {}".format(dsast))
if __name__ == "__main__":
    main()

