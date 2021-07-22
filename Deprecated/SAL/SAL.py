# SAL layer class model
import sys
import os
import random

sys.path.append("../")
from lib.MN_Queue import Parts,MN_queue,MN_commons
from LLS.LLS import DSAST, GAST


# TODO: CAST translation table that resides in PN(DP->DS_C) //Adaptation layer?
# TODO: CAST translation cache that resides in PN(DP->DS_T)
# TODO: DSAST terminates when all of its associate bast terminates

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
    def __init__(self,thread_counts=1,gast=GAST()):
        self.sys_config = SysConfig()  # program sysconfig
        self.index = random.getrandbits(20)  # actual CAST is this 20-bit tag
        self.mn_commons = MN_commons() # collection of all mn_queues
        self.threads = [ThreadCAST(gast=gast) for idx in range(thread_counts)] # list of ongoing threads - start with 1
        self.thread_ids = [id(thread) for thread in threads] # list of ordered thread ids
        self.dpast_to_dsast = {} # dpast to dsast translation table
        #self.dsast = mapBASTtoDSAST(DSAST(),gast=None)


        #SNE features
        self.npast_to_nsast = [] * self.sys_config.max_socket
        self.network_addr = 0
        self.network_data = 0
        self.port_PN = 0

        self.stdin = GAST()
        self.stdout = GAST()
        self.strerr = GAST()

    #def init_program(self):
    # get the gast dsast info etc.

    def read_port(self):
        self.port_PN = data


    def write_port(self):
        self.port_PN = data

    def get_threads(self) -> list:
        return self.threads

    def get_thread_ids(self) -> list:
        return self.thread_ids


class ThreadCAST:
    def __init__(self, dsast=DSAST(), gast=GAST(), dpast=DPAST()):
        self.ID = id(self)  # need clearification on id
        self.status = 0  # waiting = 0, running = 1, sleeping = 2
        #self.dsast = mapBASTtoDSAST(dsast=dsast,gast=gast) # from LLS
        self.gast = gast
        self.dpast = DPAST(size=0, DSAST=self.dsast)
        self.program_counter = None
        # look into thread system notification

if __name__ == '__main__':
    pass