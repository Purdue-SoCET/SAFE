import threading
from CH_param_sim import*
import L4_cache
import pwntools

global MAX_SYS_SOCKET = 2
global CAST_PMU = 1
global CAST_SNE = 8
global CAST_SAL = 16
global READ = 0
global WRITE = 1

class L3cache:
    def __init__(self, cache_size, block_size):
        self.block_size = block_size
        self.cache_size = cache_size #12
        self.cache_mask = (1 << self.cache_size) - 1
        self.line_tag = [0] * (1 << self.cache_size)
        self.tag_offset = self.cache_size + self.block_size
        self.line_data = [0] * (1 << self.cache_size)
        self.line_state = [0] * (1 << self.cache_size)
    
    def index(self, addr):
        return (addr >> self.block_size) & self.cache_mask
    
    def lookup(self, addr):
        idx = self.index(addr)
        print("Look up in L1 cache at {} for address {}".format(idx, hex(addr)))
        return (addr >> self.tag_offset) == self.line_tag[idx]
    
    def replace(self,addr):
        x = self.index(addr)
        if(self.line_state[x] == 1):
            L4_cache.put(line_tag[x],line_data[x])  
            self.line_state[x] = 0    
        self.line_data[self.index(addr)] = L4_cache.get(addr)
        self.line_tag[self.index(addr)] = addr >> self.tag_offset
        
    def get(self, addr):
        if(not self.lookup(addr)):
           print("It's a L3 miss")
           self.replace(addr) 
        else:
            print("It's a L3 hit")           
        return self.line_data[self.index(addr)]
        
    def put(self,addr,data):
        self.addr = addr
        if not self.lookup(self.addr):
           print("It's a L3 write miss in put")  
           self.replace(self.addr)   
        print("Insert at index ",self.index(self.addr))   
        self.line_data[self.index(self.addr)] = data

global ACK
global buff
ACK = threading.Semaphore(value=1)
#sleep thread if no data
def thread_function(sys_NSAST):
	r = sys_NSAST
	if (sys_NSAST.tx):
		buff = Cache_Hierarchy(READ,sys_NSAST,None)		
		while (True):
			if (buff.valid):
				r.send(buff)		
			ACK.release()
	else:
		while (True):
			ACK.acquire()
			if (buff.valid):
				r.recvn(buff)
		Cache_Hierarchy(WRITE,sys_NSAST,None)		

#message format: NPAST, CAST, NSAST
class SNE:
	def __init__(self):
		self.MN_Queue = MN_Queue()
		self.control_table = [0] * MAX_SYS_SOCKET
		self.CAST_SNE = 17
		self.L3_cache = L3cache()
		self.system_sockets =[threading.Thread(thread_function,args=(sys_NSAST,message),name=str(i)) for i in range(MAX_SYS_SOCKET)]
		self.message = 0
		for NSAST in range(MAX_SYS_SOCKET):
			sys_NSAST = remote('127.0.0.1', 3000 + NSAST)
			self.system_sockets[NSAST].start(sys_NSAST,self.message)
			
	def main(self):
		while (True):
			message = MN_decode(Cache_Hierarchy(WRITE,CAST_PMU))
			if (MN_decode(message).valid == True):
				if (MN_decode(message).setup == True):
					#best case: binary search
					for i in range(MAX_SYS_SOCKET):
						if (self.control_table[MAX_SYS_SOCKET].enable == 0):
							self.control_table[MAX_SYS_SOCKET].enable = 1
							break
						NSAST = i
						self.control_table[i].NPAST = MN_decode(message).NPAST
						self.control_table[i].CAST = MN_decode(message).CAST
					Cache_Hierarchy(WRITE,CAST_PMU,MN_encode(NSAST)
				else if (MN_decode(message).readwrite == True):
					if MN_decode(message).read:
						message = Cache_Hierarchy(READ,MN_decode(message).NSAST,None)	
						NSAST = MN_decode(message).NSAST
						if (message.valid):
							buff = data = Cache_Hierarchy(READ,NSAST,None)	
							if (buff.valid):
								wait()
							buff = self.system_sockets[NSAST].
					else if MN_decode(message).write:
						Cache_Hierarchy(WRITE,MN_encode(NSAST, CAST_SNE, NPAST) + ,None)	
						Cache_Hierarchy(WRITE,MN_decode(message).NSAST,None)								
				
