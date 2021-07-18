import random
import os

#LLS maps DSAST
#DAStable = [] #list of DAS 
DPASTDSAST = {} # DSAST -> DPAST hash table
DPAST_process = [] #list of ongoing processes 
#TODO: DPAST_process really is CAST consistening of ongoing DPAST processes
#TODO: CAST translation table that resides in PN(DP->DS_C) //Adaptation layer?
#TODO: CAST translation cache that resides in PN(DP->DS_T)
#TODO: DSAST terminates when all of its associate bast terminates

# process needs data objects. cant be system data objects. heap/stack might be in DPAST
# if there was not associated tag for stack, it would be hard to map 
# dpast is like virtual memory, 

WAY_LIMIT = 0# determined by pc
LARGE_LINE_LIMIT = 0# determined by pc
SMALL_LINE_LIMIT = 0# determined by pc
INVALID_TRANSLATION = 0x00000000 # 32 bits of zero

class DPAST:
    def __init__(self,size,DSAST):
    # Size: 0 = Large DPAST, 1 = Small DPAST
        self.size = size
        self.dsast = DSAST
        if (size): #small DPAST
            self.offset = random.getrandbits(40)
            self.data = random.getrandbits(18)#  randomize address to keep track of or the actual data address from DSAST? 
        else:
            self.offset = random.getrandbits(50)
            self.data = random.getrandbits(8)
        DPAST_process.append(self.data)    

def mapDSASTtoDPAST(aDSAST):
    if (aDSAST in DPASTDSAST):
        return
    aDPAST = DPAST(aDSAST.size,aDSAST)  
    DPASTDSAST[aDSAST] = aDPAST
    # print(DPASTDSAST)
    return 


def DP_translation(aDSAST):
    aDPAST = DPASTDSAST[aDSAST]
    if (aDPAST == None):
        return INVALID_TRANSLATION
    return aDPAST


### convert DSAST to binary DSR that cache uses
### returns a 72bit DSR
def DSAST_to_binary(aDSAST): 
    binary = WAY_LIMIT << 70
    # 69th bit 0 is a large dsast, bit 1 is a small dsast
    if (aDPAST.size): #small dsast
        binary |= (0 << 69) | (SMALL_LINE_LIMIT << 65)
        binary |= (aDSAST.index << 50) | (aDPAST.offset) 
    else: #large dsast
        binary |= (1 << 69) | (LARGE_LINE_LIMIT << 64) 
        binary |= (aDSAST.index << 40) | (aDST.offset)
    return binary
    
### vice-versa of DSAST_to_binary
### returns an object DSAST
def binary_to_DSAST(binary): 
    size = binary & (1 << 69)
    if(size): #sm all dsast
        index = binary & (0x7fff << 50) 
        offset = (binary << 22) >> 22
        linelimit = SMALL_LINE_LIMIT
    else: #large dsast
        index = binary & (0x1ffffff << 40)
        offset = (binary << 32) >> 32
        linelimit = LARGE_LINE_LIMIT
    aDPAST = DPAST(index,linelimit,size,WAY_LIMIT,offset)
    return aDPAST
    

