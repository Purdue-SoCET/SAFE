import math
import random
#from LLS import *
#from createfiles import createFiles
class cache:
    def __init__(self, level): 
        self.level = level
        self.ways = 4
        self.line_size = 6 + self.level + self.level
        self.l1_block_size = 2
        self.subline_size = 1
        self.block_size = int((self.l1_block_size) * math.pow(4, self.level))    ##Block size in word  L1 = 2 word L2 is 8 word
        self.block_shift = 1 + self.level * 2
        self.reserve_bit = 2 + 4 * self.level
        self.valid = 0
        self.invalid = 2
        self.dirty = 1

        #######################
        self.highest_level = 2 - 1  #Highest level cache is L2

        #number of cache in multicore for each level
        self.cache_num = [2, 1, 1, 1, 1]        ## number of cache in each level from left to right would be L1 -> L5
        #########################


        self.up = level - 1
        self.down = level + 1
        self.cache_mask = (1 << (self.line_size + self.block_shift + 2 )) - 1
        self.block_mask = (self.block_size) - 1

        if(self.level == 0):
            self.direct_size = 8
            self.subline_size = 1

        elif(self.level == 1):
            self.direct_size = 12
            self.subline_size = int(self.block_size / int((self.l1_block_size) * math.pow(4, self.up)))

        elif(level == 2):
            self.direct_size = 22
            self.subline_size = int(self.block_size / int((self.l1_block_size) * math.pow(4, self.up)))

        elif(self.level == 3):
            self.direct_size = 5 #26 #  L4 #self.cache_size - log2(self.ways) #10
            self.subline_size = int(self.block_size / int((self.l1_block_size) * math.pow(4, self.up)))

        elif(self.level == 4):
            self.direct_size = 8 #27 # L5 #self.cache_size - log2(self.ways) #10
            self.subline_size = int(self.block_size / int((self.l1_block_size) * math.pow(4, self.up)))


        self.line_tag = [[[0 for y in range(self.ways)] for x in range(1 << self.line_size)]for xx in range(self.cache_num[self.level])] #[0] * (1 << self.cache_size)
        self.tag_offset = 2 + self.block_shift + self.line_size         #here might be an issue

        #Data segment of cache block TODO:Need change so that I can access word on each offset (set the block as word)
        self.line_data = [[[[0 for z in range(self.block_size)] for y in range(self.ways)] for x in range(1 << self.line_size)]for xx in range(self.cache_num[self.level])] #[0] * (1 << self.cache_size)

        #Dirty Bit and invalid bit segment of cache block
        #0 means valid non dirty, 1 means valid dirty, 2 mean invalid cache_line
        self.line_state = [[[0 for y in range(self.ways)] for x in range(1 << self.line_size)]for xx in range(self.cache_num[self.level])] #[0] * (1 << self.cache_size)
        #ownership bit segment of cache block

        #0 means no status, 1 mean virtual_root
        self.virtual_root = [[[[0 for zz in range(self.ways)] for y in range(self.subline_size)] for x in range(1 << self.line_size)] for xx in range(self.cache_num[self.level])]

        # n bit pointer mapping for higher level virtual root location
        self.root_pointer = [[[[0 for zz in range(self.ways)]for y in range(self.subline_size)] for x in range(1 << self.line_size)]for xx in range(self.cache_num[self.level])]

        for xx in range(0, self.cache_num[self.level]):
            for j in range(0, 1 << self.line_size):
                for i in range(0, self.ways):
                    self.line_state[xx][j][i] = self.invalid

        for xx in range(0, self.cache_num[self.level]):
            for j in range(0, 1 << self.line_size):
                for i in range(0, self.subline_size):
                    for yy in range(0, self.ways):
                        self.virtual_root[xx][j][i][yy] = 0

        for xx in range(0, self.cache_num[self.level]):
            for j in range(0, 1 << self.line_size):
                for i in range(0, self.subline_size):
                    for yy in range(0, self.ways):
                        self.root_pointer[xx][j][i][yy] = 0


    def find_lower_cache(self, current_index):
        #print("lower cache: self is cache lv", self.level, " index ", current_index, "up index ", int(current_index * self.cache_num[self.down] / self.cache_num[self.level]))
        return int(current_index * self.cache_num[self.down] / self.cache_num[self.level])
        if self.cache_num[self.up] == 1:
            return 0
        elif(self.cache_num[self.up] == self.cache_num[self.level]):
            return current_index


    def find_upper_cache_list(self, current_index):
        cache_list = list()
        size = self.cache_num[self.level]
        size_upper = self.cache_num[self.up]

        for i in range(0, int(size_upper / size) ):
            cache_list.append(int(current_index) * int(size_upper / size) + i)
        #print(cache_list)
        return cache_list

    def index(self, addr):
#        print(hex(addr))
 #       print(((addr) & self.cache_mask) >> (self.block_shift + 2), self.block_shift)
        return ((addr) & self.cache_mask) >> (self.block_shift + 2)
    
    def block(self, addr):
        return (addr >> 2) & self.block_mask




    ##return the address for certain subline index
    def subline_addr(self, addr, subline_idx):
        idx = self.index(addr)
        block_idx = subline_idx * self.block_size / self.subline_size
        #print(hex(addr), hex(addr & ~(self.block_mask)), (subline_idx))

        return (((addr >> 2) & ~(self.block_mask)) << 2) + (int(block_idx) << 2)

    def get_way(self, cache_idx, addr):
        hit_way = -1
        idx = self.index(addr)
        for i in range(self.ways):
              #  print(int(cache_idx), idx, i, self.cache_num[self.level],self.level)
               # print(self.line_tag[int(cache_idx)][idx][i])
            if((addr >> self.tag_offset) == self.line_tag[int(cache_idx)][idx][i] and not self.line_state[int(cache_idx)][idx][i] == self.invalid):
                    hit_way = i
        return hit_way 

    ##get the index for lower level block range cover    4 -> 2
    def get_subline(self, addr, block):
        return int(block / (self.block_size / self.subline_size))

    def lookup(self, cache_idx, addr):

        idx = self.index(addr)
   #     print("Look up at index ", idx)
   #     print("Line size", self.line_size)
    #    print("in level", self.level)
        return_way = self.get_way(cache_idx, addr)
        if return_way != -1 :
            return self.line_state[int(cache_idx)][int(idx)][int(return_way)] != self.invalid
        else:
            return False


    def check_down_root(self, addr, lower_cache_idx):
        idx = self.index(addr)
        block = self.block(addr)
        write_way = -1
        current_subline = self.get_subline(addr, block)
        if not self.lookup(lower_cache_idx, addr):
           ## print("Error on check_down_root")
            return False
        else:
            write_way = self.get_way(lower_cache_idx, addr)

        virtual_root = self.virtual_root[lower_cache_idx][idx][current_subline][write_way]
        if(virtual_root == 1):
            return True
        return False


    def check_down_unique(self, addr, upper_cache_idx, cache_idx):
        idx = self.index(addr)
        block = self.block(addr)

        write_way = -1
        current_subline = self.get_subline(addr, block)
        if not self.lookup(cache_idx, addr):
            return False, False
        else:
            write_way = self.get_way(cache_idx, addr)

        root_pointer = self.root_pointer[cache_idx][idx][current_subline][write_way]
        if(root_pointer > 0 and root_pointer != 1 << upper_cache_idx):
            #print("down_unique but not self", root_pointer, upper_cache_idx)
            return True, False
        if root_pointer == 0:
            return False, True
        return False, False

    def clean_uniqueness(self, addr, current_cache_idx, first):
        current_block = self.block(addr)
        index = self.index(addr)
        write_way = -1
        current_subline = self.get_subline(addr, current_block)
        upper_cache_list = self.find_upper_cache_list(current_cache_idx)
        lower_cache_idx = self.find_lower_cache(current_cache_idx)
        #print("clean ", self.level, current_cache_idx)
        if not self.lookup(current_cache_idx, addr):
            print("Error on clean_unique assign", self.level, current_cache_idx, index)
            return False
        else:
            write_way = self.get_way(current_cache_idx, addr)
        #print(self.root_pointer[current_cache_idx][index])

        ## separate the functionality between clean uniqueness initiator function and snooped function
        if(first == 1):
            root_pointer = self.root_pointer[current_cache_idx][index][current_subline][write_way]
            virtual_root = self.virtual_root[current_cache_idx][index][current_subline][write_way]
            #print(root_pointer, "root pointer")
            if(root_pointer > 0):
                for upper_cache in upper_cache_list:
                    print(root_pointer)
                    if root_pointer >> upper_cache == 1:
                        if(self.level == 0):
                            print("ERROR:L1 do not have higher level root pointer in clean uniqueness function")

                        subline_addr = self.subline_addr(addr, current_subline)
                        #print("clean_start", root_pointer, current_subline, subline_addr, addr, upper_cache_list)
                        caches[self.up].clean_uniqueness(subline_addr, upper_cache, 0)


                #elif virtual_root == 1:
                #self.virtual_root[current_cache_idx][index][current_subline][write_way] = 1

            ##clean the dirty blocks when
            self.line_state[current_cache_idx][index][write_way] == self.valid
        else:
            for subline_idx in range(0, self.subline_size):
                root_pointer = self.root_pointer[current_cache_idx][index][subline_idx][write_way]
                virtual_root = self.virtual_root[current_cache_idx][index][subline_idx][write_way]
                if (root_pointer > 0 and virtual_root == 0):
                    if(self.level != 0):
                        for upper_cache in upper_cache_list:
                            if root_pointer >> upper_cache == 1:
                                #if (self.level == 0):
                                    #print("ERROR:L1 do not have higher level root pointer in clean uniqueness function")
                                subline_addr = self.subline_addr(addr, subline_idx)
                                #print(root_pointer, subline_addr, addr, "first 1")
                                caches[self.up].clean_uniqueness(subline_addr, upper_cache, 0)
            subline_block_size = int(self.block_size / self.subline_size)
            for subline_idx in range(0, self.subline_size):
                virtual_root = self.virtual_root[current_cache_idx][index][subline_idx][write_way]
                if(virtual_root == 1):
                    for block in range(subline_idx * subline_block_size , subline_idx * subline_block_size + subline_block_size):
                        block_addr = addr & ~(self.block_mask << 2) ^ (block << 2)  # need testing
                        #print("unique clean block", block_addr, self.line_data[current_cache_idx][index][write_way][block], block, "cache index", current_cache_idx)
                        caches[self.down].put_clean(lower_cache_idx, block_addr, self.line_data[current_cache_idx][index][write_way][block], 0)
                        caches[self.down].assign_root_pointer(block_addr, current_cache_idx, lower_cache_idx, 0)
                        self.virtual_root[current_cache_idx][index][subline_idx][write_way] = 0
                        # if(virtual_root == 1 and ((block % ((int)(self.block_size / self.subline_size))) == 0)):





       # print("clean_unique ", current_cache_idx, index, self.line_size, addr)


        return


   #assign or deassert the owenership direction bit map of lower level cache
    def assign_root_pointer(self, addr, higher_cache_idx, current_cache_idx, set):
        current_block = self.block(addr)
        index = self.index(addr)
        write_way = -1
        current_subline = self.get_subline(addr, current_block)
        if not self.lookup(current_cache_idx, addr):
            print("Error on root_pointer assign")
            return False
        else:
            write_way = self.get_way(current_cache_idx, addr)
        if (set == 1):
           # print(current_cache_idx, write_way, current_subline,index)
           # print(self.subline_size, self.level, self.line_size)
            self.virtual_root[current_cache_idx][index][current_subline][write_way] = 0
            self.root_pointer[current_cache_idx][index][current_subline][write_way] = 1 << higher_cache_idx
            #print("assign root point", higher_cache_idx)

        else :
            self.virtual_root[current_cache_idx][index][current_subline][write_way] = 1
            self.root_pointer[current_cache_idx][index][current_subline][write_way] = 0

        #print("assign_root_pointer", self.root_pointer[current_cache_idx][index][current_subline])
        return True



    #recursive lower level search on invalidation
    def invalidation_recursion(self, addr, upper_cache_idx, cache_idx):
        current_block = self.block(addr)
        index = self.index(addr)
        write_way = -1
        current_subline = self.get_subline(addr, current_block)
        upper_cache_list = self.find_upper_cache_list(cache_idx)
        lower_cache_idx = self.find_lower_cache(cache_idx)
        write_way = -1
        if not self.lookup(cache_idx, addr):
            #print("Look up failed in invalidation recursion at level ", self.level, "in addr: ", addr)
            if (self.level != 0):
                for upper_idx in upper_cache_list:
                    # print(upper_idx, self.level)
                    if upper_idx == upper_cache_idx:
                        caches[self.up].invalidation_up_search(addr, upper_idx)
                        return
        else:
            write_way = self.get_way(cache_idx, addr)

            if(self.virtual_root[cache_idx][index][current_subline][write_way] != 1):
                if (self.level != self.highest_level):
                    caches[self.down].invalidation_recursion(addr, cache_idx, lower_cache_idx)


            if(self.level != 0):
                for upper_idx in upper_cache_list:
                    #print(upper_idx, self.level)
                    if upper_idx != upper_cache_idx:
                        caches[self.up].invalidation_up_search(addr, upper_idx)



        return True



    #if there is shared content then go up the other cache branch and invalidate those content
    def invalidation_up_search(self, addr, cache_idx):
        current_block = self.block(addr)
        index = self.index(addr)
        upper_cache_list = self.find_upper_cache_list(cache_idx)
        lower_cache_idx = self.find_lower_cache(cache_idx)
        write_way = -1
        if not self.lookup(cache_idx, addr):
            return
        else:
            write_way = self.get_way(cache_idx, addr)

        ##
        if(self.level != 0):
            for subline in range(0, self.subline_size):
                #print(subline, addr)
                subline_addr = self.subline_addr(addr, subline)
                for upper_idx in upper_cache_list:
                    caches[self.up].invalidation_up_search(subline_addr, cache_idx)


            ##if the invalidation is dirty
        #print(index, cache_idx, write_way,self.level, 1 << self.line_size)
        if(self.line_state[int(cache_idx)][index][write_way] == self.dirty):
            for block in range(0, self.block_size):
                block_addr = addr & ~(self.block_mask << 2) ^ (block << 2)  # need testing
                caches[self.down].put_clean(lower_cache_idx, block_addr, self.line_data[cache_idx][index][write_way][block], 1)

        self.line_state[cache_idx][index][write_way] = self.invalid
        for subline_index in range(0, self.subline_size):
            self.virtual_root[cache_idx][index][subline_index][write_way] = 0
            self.root_pointer[cache_idx][index][subline_index][write_way] = 0

    ##communication with LLS happen here
    def replace(self, cache_idx, addr):
        #print("replace, " , self.level)
        x = self.index(addr)
        lower_cache_idx = self.find_lower_cache(cache_idx)
        upper_cache_list = self.find_upper_cache_list(cache_idx)
  #      print(x)
  #      print(self.line_size)
  #      print(len(self.line_data))
        block_index = self.block(addr)
        subline_index = self.get_subline(addr, block_index)
        #In the future this can be change to LRU
        way_to_replace = random.randint(0, self.ways - 1)


        if(self.line_state[cache_idx][x][way_to_replace] == self.dirty):
            old_tag_addr = self.line_tag[cache_idx][x][way_to_replace]
            if(self.level != self.highest_level):
            ##


                for i in range(0, self.block_size):
                    block_addr = old_tag_addr & ~(self.block_mask << 2) ^ (i << 2)  # need testing
#               caches[self.down].put(line_tag[x][way_to_replace],line_data[x][way_to_replace][block_index])
            #

                    caches[self.down].put(lower_cache_idx, block_addr, self.line_data[cache_idx][x][way_to_replace][i])
                self.line_state[cache_idx][x][way_to_replace] = self.valid

            else:
                for i in range(0, self.block_size):
                    block_addr = old_tag_addr & ~(self.block_mask << 2) ^ (i << 2)  # need testing
                    #line_data[x][way_to_replace][i] = writeLLS(global_dsast, line_data[x][way_to_replace][i])
                    #               caches[self.down].put(line_tag[x][way_to_replace],line_data[x][way_to_replace][block_index])

                    #caches[self.down].put(addr, self.line_data[x][way_to_replace][block_addr])
                    if(i == 0):
                        print("Miss in all Cache Levels. Going to LLS, dirty data 1st addr", addr, " is written")
            self.line_state[cache_idx][x][way_to_replace] = self.valid
            for subline in range(0, self.subline_size):
                self.virtual_root[cache_idx][x][subline_index][way_to_replace] = 0
                self.root_pointer[cache_idx][x][subline_index][way_to_replace] = 0

    #    print("Replace function index", x)
    #    print("Replace function way to replace ", way_to_replace)
    #    print("Replace function down ", self.down)
        if(self.level != self.highest_level):

            self.line_tag[cache_idx][x][way_to_replace] = addr >> self.tag_offset
    #        print("Replacing tag ", self.line_tag[x][way_to_replace])
            down_root = caches[self.down].check_down_root(addr, lower_cache_idx)
            down_unique, up_no_root = caches[self.down].check_down_unique(addr, cache_idx, lower_cache_idx)
            unique_cleaned = 0
            if(not down_root) and (down_unique):
                caches[self.down].clean_uniqueness(addr, lower_cache_idx, 1)
                unique_cleaned = 1
            for i in range(0, self.block_size):

                block_addr = addr & ~(self.block_mask << 2) ^ (i << 2)      #need testing
                self.line_data[cache_idx][x][way_to_replace][i] = caches[self.down].get(lower_cache_idx, block_addr)
                #print("Writing addr ", hex(addr), " with data ", self.line_data[x][way_to_replace][i], " among replacement in Cache level ", self.level)
                if(i % (self.block_size / self.subline_size) == 0):
                    self.root_pointer[cache_idx][x][int(i / (self.block_size / self.subline_size))][way_to_replace] = 0


            down_root = caches[self.down].check_down_root(addr, lower_cache_idx)
            down_unique, up_no_root = caches[self.down].check_down_unique(addr, cache_idx, lower_cache_idx)
            assign_root = 0
            if(down_root and up_no_root):
                assign_root = 1
                caches[self.down].assign_root_pointer(addr, cache_idx, lower_cache_idx, 1)

            for i in range(0, self.block_size):
                block_addr = addr & ~(self.block_mask << 2) ^ (i << 2)
                if (i % (self.block_size / self.subline_size) == 0):
                    self.virtual_root[cache_idx][x][int(i / (self.block_size / self.subline_size))][way_to_replace] = assign_root
        else:
            ##open the file , outbox for LLS, read, write req, out box 
        #    print("Miss in all Cache Levels. Going to LLS, dummy data received")
            #DSAST use = 71-50 bit of ADDR
            #61-20
            print("read LLS")
            for i in range(0, self.block_size):
                block_addr = addr & ~(self.block_mask << 2) ^ (i << 2)  # need testing
                #self.line_data[x][way_to_replace][i] = readLLS(global_dsast)
                self.line_data[cache_idx][x][way_to_replace][i] = block_addr
                subline_idx = self.get_subline(block_addr, i)
                self.virtual_root[cache_idx][x][subline_idx][way_to_replace] = 1;

                #print(subline_idx, " subline_lls ", self.virtual_root[cache_idx][x][subline_idx])
                self.root_pointer[cache_idx][x][subline_idx][way_to_replace] = 0;
            self.line_state[cache_idx][x][way_to_replace] = self.valid
            #print(self.line_state[cache_idx][x])

        #print("level", self.level, self.root_pointer[cache_idx][x])
        #print("level", self.level, self.virtual_root[cache_idx][x])
        self.line_tag[cache_idx][x][way_to_replace] = addr >> self.tag_offset
        return way_to_replace
        
    def get(self, cache_idx, addr):
    #print(addr)
        index = self.index(addr)
        block_index = self.block(addr)

        if(not self.lookup(cache_idx, addr)):
            #print("It's a miss in level", self.level)
           #Miss list
            miss[self.level] += 1
            insrt_way = self.replace(cache_idx, addr)
            return self.line_data[cache_idx][index][insrt_way][block_index]
        else:
            subline_index = self.get_subline(addr, block_index)
            #upper_cache_list = self.find_upper_cache_list(cache_idx)
         #   print("It's a hit in level ", self.level)

        #print("Its a hit in level", self.level)
        hits[self.level] += 1
        hit_way = self.get_way(cache_idx, addr)
        #print(self.line_data[cache_idx][index][hit_way][block_index])
        #if(self.virtual_root[cache_idx][index][subline_index][hit_way] == 1):
        #    return self.line_data[cache_idx][index][hit_way][block_index]
        #if(self.root_pointer[cache_idx][index][subline_index][hit_way] > 0):
            #for upper_cache in upper_cache_list:
            #self.clean_uniqueness(addr, cache_idx, 1)
                #if(self.root_pointer[cache_idx][index][hit_way][subline_index] == 1 << upper_cache_list):

                #    for i in range(0, self.block_size):
                #        block_addr = addr & ~(self.block_mask << 2) ^ (i << 2)  # need testing
                #        self.line_data[cache_idx][index][hit_way][i] = caches[self.up].get_upper(upper_cache, addr, block_addr)

        return self.line_data[cache_idx][index][hit_way][block_index]


    def put_clean(self, cache_idx, addr, data, set_dirty):
        write_way = -1
        self.addr = addr
        # self.data = data
        block_index = self.block(addr)
        subline_index = self.get_subline(addr, block_index)
        if not self.lookup(cache_idx, self.addr):
            print("ERROR on put clean")
        else:
            write_way = self.get_way(cache_idx, addr)

        #print("Insert at index ", self.index(self.addr))
        self.line_data[cache_idx][self.index(addr)][write_way][block_index] = data
        self.line_state[cache_idx][self.index(addr)][write_way] = set_dirty


    def put(self, cache_idx, addr, data):
        write_way = -1
        self.addr = addr
        lower_cache_idx = self.find_lower_cache(cache_idx)
        #self.data = data
        block_index = self.block(addr)
        subline_index = self.get_subline(addr, block_index)
 #       if (self.level == 0):
 #           print(caches[1].virtual_root[0][caches[1].index(0x0000)][caches[1].get_subline(0x0000, caches[1].block(0x0000))])
 #           print(caches[0].virtual_root[1][caches[0].index(0x0000)][caches[0].get_subline(0x0000, caches[0].block(0x0000))])
 #           print(caches[1].root_pointer[0][caches[1].index(0x0000)][
 #                     caches[1].get_subline(0x0000, caches[1].block(0x0000))])
 #           print(caches[0].root_pointer[1][caches[0].index(0x0000)][
 #                     caches[0].get_subline(0x0000, caches[0].block(0x0000))])
        if not self.lookup(cache_idx, self.addr):
           insrt_way = self.replace(cache_idx, self.addr)
           write_way = insrt_way   
        else:
            write_way = self.get_way(cache_idx, addr)
       
        #print("Insert at index ",self.index(self.addr))
        self.line_data[cache_idx][self.index(addr)][write_way][block_index] = data
        self.line_state[cache_idx][self.index(addr)][write_way] = self.dirty


        if(self.level == 0):
            caches[self.down].invalidation_recursion(addr, cache_idx, lower_cache_idx)
            self.virtual_root[cache_idx][self.index(addr)][subline_index][write_way] = 1
            self.root_pointer[cache_idx][self.index(addr)][subline_index][write_way] = 0
        #    print("Writing addr ", hex(addr), " with data ", data, " among put in Cache level ", self.level, "at way ", write_way, "with index", self.index(addr))

        ##maybe here need invalidation snoop so other can invalidate
        #print("Writing addr ", hex(addr), " with data " , data," among put in Cache level ", self.level, "at way ", write_way)



    def hit_rate(self):
        print("Hit rate at level", self.level)
        print(hits[0])
        if(hits[0] + miss[0] != 0):
            print(" L1 Hit Rate = ", hits[0] /(hits[0] + miss[0]))
        if (hits[1] + miss[1] != 0):
            print(" L2 Hit Rate = ", hits[1] /(hits[1] + miss[1]))
        if (hits[2] + miss[2] != 0):
            print(" L3 Hit Rate = ", hits[2] /(hits[2] + miss[2]))
        if (hits[3] + miss[3] != 0):
            print(" L4 Hit Rate = ", hits[3] /(hits[3] + miss[3]))
        if (hits[4] + miss[4] != 0):
            print(" L5 Hit Rate = ", hits[4] /(hits[4] + miss[4]))

caches = []
miss = []
hits = []
#global_dsast = DSAST()
#mapBASTtoDSAST(global_dsast)
def main():
#    createFiles(1)
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
    caches[0].put(0, 0x0000,230) #Do testing # Generate random address #Add another core # Generate rand addr #
    #print(caches[0].get(0,0x0000), "*")
    #L1 block 0, index 34, tag 8
    #l2 block 8 index 68 , tag 0
    #print("*******************\n")
    caches[0].put(1,0x0004,250)

    #print("*******************\n")

    print(caches[0].get(0, 0x0004), "*")
    caches[0].put(1,0x0008, 255)
    caches[0].put(1, 0x000C, 260)
    #print(caches[0].line_data[1][caches[0].index(0x0008)])
    #print(caches[0].line_state[1][caches[0].index(0x0008)])
   # print(caches[1].line_tag[0][caches[0].index(0x0008)])
  #  print(caches[1].root_pointer[0][caches[1].index(0x0008)][caches[1].get_subline(0x0008, caches[1].block(0x0008))])
   # print(caches[0].virtual_root[1][caches[0].index(0x0008)][caches[0].get_subline(0x0008, caches[0].block(0x0008))])
  #  print("***********")
    print(caches[0].get(0, 0x0008), "*")
 #   print("***********")


 #   print(caches[1].root_pointer[0][caches[1].index(0x0008)][caches[1].get_subline(0x0008, caches[1].block(0x0008))])
  #  print(caches[0].virtual_root[1][caches[0].index(0x0008)][caches[0].get_subline(0x0008, caches[0].block(0x0008))])

    print(caches[0].get(0,0x0008), "*")
    print(caches[0].get(1,0x000C), "*")

   # print(caches[0].get(0, 0x1100))
   # print(caches[0].get(0, 0x1104))
   # print(caches[0].get(0, 0x100c))


   # print(caches[0].get(0, 0x11100))
   # print(caches[0].get(0, 0x11104))
   # print(caches[0].get(0, 0x1110c))
   # print(caches[0].get(0, 0x11100))
   # print(caches[0].get(0, 0x11104))
   # print(caches[0].get(0, 0x1110c))
 #   print(caches[0].get(0,0x0008))
#  print(caches[0].get(1,0x000C))


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
    
    
if __name__ == "__main__":
    main()