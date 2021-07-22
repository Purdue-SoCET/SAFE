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
def main():
    createFiles(300)
    initFiles(300, 80000)

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

