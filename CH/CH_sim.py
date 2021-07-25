import fcntl
class L1cache:
    def __init__(self, cache_size, block_size):
        self.block_size = block_size #6
        self.cache_size = cache_size #10
        self.cache_mask = (1 << self.cache_size) - 1
        #self.tag = [0 for x in range((1 << self.cache_size))]
        self.line_tag = [0] * (1 << self.cache_size)
        self.tag_offset = self.cache_size + self.block_size
        #self.data = [0 for x in range((1 << self.cache_size))]
        self.line_data = [0] * (1 << self.cache_size)
        self.line_state = [0] * (1 << self.cache_size)
        self.L1hits = 0 
        self.L1miss = 0
    
    def index(self, addr):
        return (addr >> self.block_size) & self.cache_mask
    
    def lookup(self, addr):
        idx = self.index(addr) #(addr >> cache_line_size) & cache_mask
        print("Look up in L1 cache at {} for address {}".format(idx, hex(addr)))
        return (addr >> self.tag_offset) == self.line_tag[idx]
    
    def replace(self,addr):
        x = self.index(addr)
        if(self.line_state[x] == 1):
            L2_cache.put(line_tag[x],line_data[x])  
            self.line_state[x] = 0    
        #print("Replace function ", self.index(addr))
        self.line_data[self.index(addr)] = L2_cache.get(addr)
        self.line_tag[self.index(addr)] = addr >> self.tag_offset
        
    def get(self, addr):
        if(not self.lookup(addr)):
           print("It's a L1 miss")
           self.L1miss += 1  
           self.replace(addr) 
        else:
            print("It's a L1 hit")
            self.L1hits += 1              
        return self.line_data[self.index(addr)]
        
    def put(self,addr,data):
        self.addr = addr
        #self.data = data
        if not self.lookup(self.addr):
           print("It's a L1 write miss in put")  
           self.replace(self.addr)   
        print("Insert at index ",self.index(self.addr))   
        self.line_data[self.index(self.addr)] = data
  
    def hit_rate(self):
        print(" L1 Hit Rate = ", self.L1hits/(self.L1hits+self.L1miss))


class L2cache:  
    def __init__(self, cache_size, block_size):
        self.block_size = block_size #8
        self.cache_size = cache_size #16
        self.cache_mask = (1 << self.cache_size) - 1
        #self.tag = [0 for x in range((1 << self.cache_size))]
        self.line_tag = [0] * (1 << self.cache_size)
        self.tag_offset = self.cache_size + self.block_size
        #self.data = [0 for x in range((1 << self.cache_size))]
        self.line_data = [0] * (1 << self.cache_size)
        self.line_state = [0] * (1 << self.cache_size)
        #self.state = [0 for x in range((1 << self.cache_size))]
        self.L2hits = 0 
        self.L2miss = 0

    
    def index(self, addr):
        return (addr >> self.block_size) & self.cache_mask
    
    def lookup(self, addr):
        idx = self.index(addr) #(addr >> cache_line_size) & cache_mask
        print("Look up in L2 cache at {} for address {}".format(idx, hex(addr)))
        return (addr >> self.tag_offset) == self.line_tag[idx]
    
    def replace(self,addr):
        x = self.index(addr)
        if(self.line_state[x] == 1):
            L3_cache.put(line_tag[x],line_data[x])  
            self.line_state[x] = 0    
        #print("Replace function ", self.index(addr))
      
        self.line_data[self.index(addr)] = L3_cache.get(addr)
        self.line_tag[self.index(addr)] = addr >> self.tag_offset
        
    def get(self, addr):
        if(not self.lookup(addr)):
           print("It's a L2 miss")
           self.L2miss += 1  
           self.replace(addr) 
        else:
            print("It's a L2 hit")
            self.L2hits += 1              
        return self.line_data[self.index(addr)]
        
    def put(self,addr,data):
        self.addr = addr
        #self.data = data
        if not self.lookup(self.addr):
           print("It's a L2 write miss in put")  
           self.replace(self.addr)   
        print("Insert at index ",self.index(self.addr))   
        self.line_data[self.index(self.addr)] = data
  
    def hit_rate(self):
        print(" L2 Hit Rate = ", self.L2hits/(self.L2hits+self.L2miss))

class L3cache:
    def __init__(self, cache_size, block_size):
        self.block_size = block_size #6
        self.cache_size = cache_size #12
        self.cache_mask = (1 << self.cache_size) - 1
        #self.tag = [0 for x in range((1 << self.cache_size))]
        self.line_tag = [0] * (1 << self.cache_size)
        self.tag_offset = self.cache_size + self.block_size
        #self.data = [0 for x in range((1 << self.cache_size))]
        self.line_data = [0] * (1 << self.cache_size)
        self.line_state = [0] * (1 << self.cache_size)
        self.L3hits = 0 
        self.L3miss = 0
    
    def index(self, addr):
        return (addr >> self.block_size) & self.cache_mask
    
    def lookup(self, addr):
        idx = self.index(addr) #(addr >> cache_line_size) & cache_mask
        print("Look up in L1 cache at {} for address {}".format(idx, hex(addr)))
        return (addr >> self.tag_offset) == self.line_tag[idx]
    
    def replace(self,addr):
        x = self.index(addr)
        if(self.line_state[x] == 1):
            L4_cache.put(line_tag[x],line_data[x])  
            self.line_state[x] = 0    
        #print("Replace function ", self.index(addr))
        self.line_data[self.index(addr)] = L4_cache.get(addr)
        self.line_tag[self.index(addr)] = addr >> self.tag_offset
        
    def get(self, addr):
        if(not self.lookup(addr)):
           print("It's a L3 miss")
           self.L3miss += 1  
           self.replace(addr) 
        else:
            print("It's a L3 hit")
            self.L3hits += 1              
        return self.line_data[self.index(addr)]
        
    def put(self,addr,data):
        self.addr = addr
        #self.data = data
        if not self.lookup(self.addr):
           print("It's a L3 write miss in put")  
           self.replace(self.addr)   
        print("Insert at index ",self.index(self.addr))   
        self.line_data[self.index(self.addr)] = data
  
    def hit_rate(self):
        print(" L3 Hit Rate = ", self.L3hits/(self.L3hits+self.L3miss))

class L4cache:
    def __init__(self, cache_size, block_size):
        self.block_size = block_size #6
        self.cache_size = cache_size #12
        self.cache_mask = (1 << self.cache_size) - 1
        #self.tag = [0 for x in range((1 << self.cache_size))]
        self.line_tag = [0] * (1 << self.cache_size)
        self.tag_offset = self.cache_size + self.block_size
        #self.data = [0 for x in range((1 << self.cache_size))]
        self.line_data = [0] * (1 << self.cache_size)
        self.line_state = [0] * (1 << self.cache_size)
        self.L4hits = 0 
        self.L4miss = 0
    
    def index(self, addr):
        return (addr >> self.block_size) & self.cache_mask
    
    def lookup(self, addr):
        idx = self.index(addr) #(addr >> cache_line_size) & cache_mask
        print("Look up in L4 cache at {} for address {}".format(idx, hex(addr)))
        return (addr >> self.tag_offset) == self.line_tag[idx]
    
    def replace(self,addr):
        x = self.index(addr)
        if(self.line_state[x] == 1):
            L5_cache.put(line_tag[x],line_data[x])  
            self.line_state[x] = 0    
        #print("Replace function ", self.index(addr))
        self.line_data[self.index(addr)] = L5_cache.get(addr)
        self.line_tag[self.index(addr)] = addr >> self.tag_offset
        
    def get(self, addr):
        if(not self.lookup(addr)):
           print("It's a L4 miss")
           self.L4miss += 1  
           self.replace(addr) 
        else:
            print("It's a L4 hit")
            self.L4hits += 1              
        return self.line_data[self.index(addr)]
        
    def put(self,addr,data):
        self.addr = addr
        #self.data = data
        if not self.lookup(self.addr):
           print("It's a L4 write miss in put")  
           self.replace(self.addr)   
        print("Insert at index ",self.index(self.addr))   
        self.line_data[self.index(self.addr)] = data
  
    def hit_rate(self):
        print(" L4 Hit Rate = ", self.L4hits/(self.L4hits+self.L4miss))

class L5cache:
    def __init__(self, cache_size, block_size):
        self.block_size = block_size #6
        self.cache_size = cache_size #12
        self.cache_mask = (1 << self.cache_size) - 1
        #self.tag = [0 for x in range((1 << self.cache_size))]
        self.line_tag = [0] * (1 << self.cache_size)
        self.tag_offset = self.cache_size + self.block_size
        #self.data = [0 for x in range((1 << self.cache_size))]
        self.line_data = [0] * (1 << self.cache_size)
        self.line_state = [0] * (1 << self.cache_size)
        self.L5hits = 0 
        self.L5miss = 0
    
    def index(self, addr):
        return (addr >> self.block_size) & self.cache_mask
    
    def lookup(self, addr):
        idx = self.index(addr) #(addr >> cache_line_size) & cache_mask
        print("Look up in L5 cache at {} for address {}".format(idx, hex(addr)))
        return (addr >> self.tag_offset) == self.line_tag[idx]
    
    def replace(self,addr):
        x = self.index(addr)
        if(self.line_state[x] == 1):
            LLS_cache.put(line_tag[x],line_data[x])  
            self.line_state[x] = 0    
        #print("Replace function ", self.index(addr))
        self.line_data[self.index(addr)] = LLS_cache.get(addr)
        self.line_tag[self.index(addr)] = addr >> self.tag_offset
        
    def get(self, addr):
        if(not self.lookup(addr)):
           print("It's a L5 miss")
           self.L5miss += 1  
           self.replace(addr) 
        else:
            print("It's a L5 hit")
            self.L5hits += 1              
        return self.line_data[self.index(addr)]
        
    def put(self,addr,data):
        self.addr = addr
        #self.data = data
        if not self.lookup(self.addr):
           print("It's a L5 write miss in put")  
           self.replace(self.addr)   
        print("Insert at index ",self.index(self.addr))   
        self.line_data[self.index(self.addr)] = data
  
    def hit_rate(self):
        print(" L5 Hit Rate = ", self.L5hits/(self.L5hits+self.L5miss))

class LLScache:
    
    def __init__(self, cache_size, block_size):
       #L2cache.i += 1
       self.LLShits = 0
       self.LLSmiss = 0 

    def get(self, addr):
        self.LLShits += 1 
        return 5

    def put(self,addr,data):
        pass

    def hit_count(self):
        print(" LLS Hits = ", self.LLShits)
        
L1_cache = L1cache(10,6) # 1024 * 64 bytes
L2_cache = L2cache(18,8) #  2^18 * 256 bytes  
L3_cache = L3cache(25,10) # 25,10   1024 Bytes line      
L4_cache = L4cache(28,12) # 28,12   0 - 1 TB
L5_cache = L5cache(29,14) # 29,14  8 TB Flash     
LLS_cache = LLScache(32,16) # Dummy LLS 

def main():
    global L1_cache
    global L2_cache
    global L3_cache
    global L4_cache
    global L5_cache
    global LLS_cache
    #L1_cache.put(0x11111,230) #Do testing # Generate random address #Add another core # Generate rand addr #  
    #L1_cache.put(0x00001,245)
	#LLS will have a DSAST entry that matches the PN
	#PN on first instruction request from L5 and L5 asks LLS and provide the DSAST
	while (True):
		f = open("send_L1_to_mem", "r")
		fcntl.flock(f, fcntl.LOCK_EX)
		addr = int(f.readlines()[6:])
		value = L5_cache.get(addr)
		print(value)
		fcntl.flock(f, fcntl.LOCK_UN)
		f.close()
		f = open("recv_L1_to_mem", "w")
		fcntl.flock(f, fcntl.LOCK_EX)
		f.write("val: "+str(value))
		fcntl.flock(f, fcntl.LOCK_UN)
		f.close()
    #print(L1_cache.get(0x11111))
    #print(L1_cache.get(0xFFF23124101))
    #print(L1_cache.get(0x1EF2312401))
    #print(L1_cache.get(0xFFF23124101))
    #L1_cache.hit_rate()
    #L2_cache.hit_rate()
    #LLS_cache.hit_count()

if __name__ == "__main__":
    main()
