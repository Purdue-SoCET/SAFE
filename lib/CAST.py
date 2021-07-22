# SAL layer class model
import sys
import random

sys.path.append("../")
from lib.MN_Queue import Parts,MN_queue,MN_commons
from lib.DAST import DSAST, DPAST
#from LLS.LLS import mapBASTtoDSAST

WAY_LIMIT = 0  # determined by pc
LARGE_LINE_LIMIT = 0  # determined by pc
SMALL_LINE_LIMIT = 0  # determined by pc
INVALID_TRANSLATION = 0x00000000  # 32 bits of zero
MAX_SOCKET = 3

class SysConfig:
    def __init__(self, way_limit=WAY_LIMIT, large_line_limit=LARGE_LINE_LIMIT, small_line_limit=SMALL_LINE_LIMIT,
                 invalid_translation=INVALID_TRANSLATION,max_socket=MAX_SOCKET):
        self.way_limit = way_limit
        self.large_line_limit = large_line_limit
        self.small_line_limit = small_line_limit
        self.invalid_translation = invalid_translation
        self.max_socket = max_socket

class ProgramCAST:
    ## Remember to pass in the function "mapBASTtoDSAST" when init ProgramCAST
    def __init__(self,mapBASTtoDSAST,thread_counts=1,gast=None):
        self.sys_config = SysConfig()  # program sysconfig
        self.index = random.getrandbits(20)  # actual CAST is this 20-bit tag
        self.mn_commons = MN_commons() # collection of all mn_queues
        self.threads = [ThreadCAST(self) for idx in range(thread_counts)] # list of ongoing threads - start with 1
        #TODO: thread cast needs gast
        self.thread_ids = [id(thread) for thread in self.threads] # list of ordered thread ids
        self.dpast_to_dsast = {} # dpast to dsast translation table
        self.dsast = mapBASTtoDSAST(DSAST(),gast=gast)
        self.gast = gast
        #TODO: Generate a dpast associated with the particular dsast
        self.dpast = None

        #SNE features
        self.npast_to_nsast = [] * self.sys_config.max_socket
        self.network_addr = 0
        self.network_data = 0
        self.port_PN = 0

        #TODO:
        #self.stdin = GAST()
        #self.stdout = GAST()
        #self.strerr = GAST()

    def read_port(self,data):
        self.port_PN = data

    def write_port(self,data):
        self.port_PN = data

    def get_threads(self) -> list:
        return self.threads

    def get_thread_ids(self) -> list:
        return self.thread_ids


class ThreadCAST:
    def __init__(self,ProgramCAST):
        self.ID = id(self)  # need clearification on id
        self.status = 0  # waiting = 0, running = 1, sleeping = 2
        self.PC = None
        #self.dsast = mapBASTtoDSAST(dsast=dsast,gast=gast) # from LLS
        #self.gast = GAST()
        #self.dpast = DPAST(size=0, DSAST=self.dsast) # is it necessary?
        #self.dsast = DSAST()
        self.gast = None
        self.dsast = None
        self.dpast = None
        self.p_cast = ProgramCAST

        # look into thread system notification

if __name__ == '__main__':
    pass