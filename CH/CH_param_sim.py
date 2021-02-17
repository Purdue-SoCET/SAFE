import math
import random

class cache:
    def __init__(self, level): 
        self.level = level
        self.ways = 4
        self.line_size = 6 + self.level + self.level
        self.block_size = (1 << self.line_size) >> 5

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
        self.cache_mask = (1 << self.direct_size) - 1
        self.block_mask = (1 << self.direct_size) - 1
        
        
        self.line_tag = [[0 for y in range(self.ways)] for x in range(1 << self.direct_size)] #[0] * (1 << self.cache_size)
        self.tag_offset = self.direct_size + self.line_size
        
        #Data segment of cache block TODO:Need change so that I can access word on each offset (set the block as word)
        self.line_data = [[0 for z in range(self.block_size)] for y in range(self.ways)] for x in range(1 << self.direct_size)] #[0] * (1 << self.cache_size)

        #Dirty Bit segment of cache block
        self.line_state = [[0 for y in range(self.ways)] for x in range(1 << self.direct_size)] #[0] * (1 << self.cache_size)
        

    def index(self, addr):
        return (addr >> self.line_size) & self.cache_mask
    
    def get_way(self, addr):
        hit_way = -1
        idx = self.index(addr)
        for i in range(self.ways):
                if((addr >> self.tag_offset) == self.line_tag[idx][i]):
                    hit_way = i
        return hit_way 

    def lookup(self, addr):
        idx = self.index(addr) 
        print("Look up at index ", idx)
        print("in level", self.level)
        for i in range(self.ways):            
            return (addr >> self.tag_offset) == self.line_tag[idx][i] #Get the way in which it hits
    
    def replace(self,addr):
        x = self.index(addr)
        way_to_replace = random.randint(0, self.ways - 1)
        if(self.line_state[x][way_to_replace] == 1):
            caches[self.down].put(line_tag[x][way_to_replace],line_data[x][way_to_replace])  
            self.line_state[x][way_to_replace] = 0    
        print("Replace function index", self.index(addr))
        print("Replace function way to replace ", way_to_replace)
        print("Replace function down ", self.down)
        if(self.level != 3):
            self.line_data[self.index(addr)][way_to_replace] = caches[self.down].get(addr)
        else:
            print("Miss in all Cache Levels. Going to LLS, dummy data received")
            self.line_data[self.index(addr)][way_to_replace] = 5555 
        
        self.line_tag[self.index(addr)][way_to_replace] = addr >> self.tag_offset
        return way_to_replace
        
    def get(self, addr):
        if(not self.lookup(addr)):
           print("It's a miss in level", self.level)
           #Miss list 
           miss[self.level] += 1
           insrt_way = self.replace(addr)
           return self.line_data[self.index(addr)][insrt_way] 
        else:
            
            print("It's a hit in level ", self.level)
            hits[self.level] += 1
            hit_way = self.get_way(addr)          
            return self.line_data[self.index(addr)][hit_way]
        
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
        self.line_data[self.index(addr)][write_way] = data
  
    def hit_rate(self):
        print("Hit rate at level", self.level)
        print(hits[0])
        print(" L1 Hit Rate = ", hits[0] /(hits[0] + miss[0]))
        print(" L2 Hit Rate = ", hits[1] /(hits[1] + miss[1]))
        print(" L3 Hit Rate = ", hits[2] /(hits[2] + miss[2]))
        print(" L4 Hit Rate = ", hits[3] /(hits[3] + miss[3]))
        print(" L5 Hit Rate = ", hits[4] /(hits[4] + miss[4]))

caches = []
miss = []
hits = []

def main():
    global caches
    for i in range(5):
        caches.append(cache(i))
    
    global miss
    global hits
    miss = [0 for x in range(5)]
    hits = [0 for x in range(5)]
    
    #filename = "gcc_ld_trace.txt"
    
    with open("go_ld_trace.txt") as f:
        content = f.readlines()

    # remove whitespace characters at the end of each line
    content = [x.strip() for x in content]
    
    
    for i in range(int(len(content))):
             caches[0].get(int(content[i], 16))
    
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
    
    
if __name__ == "__main__":
    main()