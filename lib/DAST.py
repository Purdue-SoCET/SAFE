import random

# TODO: hardcoded spec, need to change it to read sysconfig instead
WAY_LIMIT = 0  # determined by pc
LARGE_LINE_LIMIT = 0  # determined by pc
SMALL_LINE_LIMIT = 0  # determined by pc
INVALID_TRANSLATION = 0x00000000  # 32 bits of zero

class DSAST:
    # NOTE: this DSAST struct represents the entire DSR as described in page 29 of the manual_1y,
    # 		thus self.offset and self.dsast compose the entire DSR struc and each DSAST field can
    #		be accessed individually as well
    # Structure(MSB to LSB): Way Limit, Size, Line Limit, Index. Part of DSR: Offset, prob useless for python simulations
    def __init__(self, address=None, index=0, lineLimit=0, size=1, wayLimit=0, offset=0):
        # Size: 0 = Large DSAST, 1 = Small DSAST
        # Offset: 40 bits for small, 50 bit for large
        # Index: (mb kinda the file name) indexing in a list of DSASTs
        # only cache fields
        # Line limit: The least significant set-bit of the this field determines the partition size and the remaining
        # upper bits of the field determine to which of the possible ranges, of the indicated size, the DSAST is restricted.
        # Way Limit: cache restrictions. 0=RESERVED, 1=no restriction, 2=only 1st half of the cache, 3=only second half of the cache
        if(address==None):  # make new dsast
            self.size = size
            if(index != 0):
                self.index = index
            elif(size==0): # large dsast
                self.index = random.getrandbits(15)
            elif(size==1): # small dsast
                self.index = random.getrandbits(24)
            self.linelimit = lineLimit
            self.waylimit = wayLimit
            if(offset != 0):
                self.offset = offset
            else:
                if(size): # small DSAST
                    self.offset = random.getrandbits(40)
                else:
                    self.offset = random.getrandbits(50)
            self.dsast = self.index | (self.linelimit << 24) | (self.size << 29) | (self.waylimit << 30)
        else:  # address passed from CH
            self.size = size
            self.waylimit = wayLimit
            self.linelimit = lineLimit
            if(self.size): # small DSAST
                self.index = (address >> 39) & 0xffffff # 24 bits
                self.offset = address & 0xffffffffff # 40 bits
                self.dsast = self.index | (self.linelimit << 24) | (self.size << 29) | (self.waylimit << 30)
            else:
                self.index = (address >> 49) & 0x3fff # 14 bits
                self.offset = address & 0x3ffffffffffff # 50 bits
                self.dsast = self.index | (self.linelimit << 14) | (self.size << 19) | (self.waylimit << 20)


# CH function to map block address to DSAST
# parameters: 	addr(64-bit value): block address from CH
# returns:		corresponding dsast that has same offset and index or false if no matching dsast is found
def mapAddrToDSAST(addr):
    global sastBast
    for dsast, bast in sastBast.items():
        if(dsast.offset == (addr & 0xffffffffff) and dsast.index == (addr & 0xffffff)):
            return dsast
    return False


class DPAST:
    def __init__(self, size=0, dsast=None):
        # Size: 0 = Large DPAST, 1 = Small DPAST
        self.size = size
        self.dsast = dsast
        if (size):  # small DPAST
            self.offset = random.getrandbits(40)
            self.data = random.getrandbits(
                18)  # randomize address to keep track of or the actual data address from DSAST?
        else:
            self.offset = random.getrandbits(50)
            self.data = random.getrandbits(8)
        DPAST_process.append(self.data)


def mapDSASTtoDPAST(aDSAST):
    pass
    #if (aDSAST in DPASTDSAST):
    #    return
    #aDPAST = DPAST(aDSAST.size, aDSAST)
    #DPASTDSAST[aDSAST] = aDPAST
    #return


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
    if (aDPAST.size):  # small dsast
        binary |= (0 << 69) | (SMALL_LINE_LIMIT << 65)
        binary |= (aDSAST.index << 50) | (aDPAST.offset)
    else:  # large dsast
        binary |= (1 << 69) | (LARGE_LINE_LIMIT << 64)
        binary |= (aDSAST.index << 40) | (aDST.offset)
    return binary


### vice-versa of DSAST_to_binary
### returns an object DSAST
def binary_to_DSAST(binary):
    size = binary & (1 << 69)
    if (size):  # sm all dsast
        index = binary & (0x7fff << 50)
        offset = (binary << 22) >> 22
        linelimit = SMALL_LINE_LIMIT
    else:  # large dsast
        index = binary & (0x1ffffff << 40)
        offset = (binary << 32) >> 32
        linelimit = LARGE_LINE_LIMIT
    aDPAST = DPAST(index, linelimit, size, WAY_LIMIT, offset)
    return aDPAST