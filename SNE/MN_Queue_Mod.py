# Socket Messaged Notification model
# MN used to tell other socket readers that socket is being written to
# Blocking of other sockets
# SSR number of additional bytes
# need to more about SSR
# test for fill up
# need to decide if equal is empty
from multiprocessing import Lock
from enum import Enum
from typing import Union

SIZE_QUEUE = 256
SIZE_BUFFER = (1 << 16) * 16  # to avoid overflow
SYSTEM_HIGH = 0  # 4 separate channels, 0 has the highest priority, 4 is the lowest
SYSTEM_LOW = 1
USER_HIGH = 2
USER_LOW = 3

TOTAL_PARTS = 6
class Parts(Enum):
    PMU = 0
    SNE = 1
    LLS = 2
    SAL = 3
    PN = 4
    CH = 5


# LLS NOTES
# make buffer hold 256 notifications (around 4k), each message containing 16 bytes (most bytes just say source,
# when msg arrived (metadata)) 256 is a nice number, as head/tail management can be done with just a uchar
# if msg is larger than 11bytes, ther is a shared memory buffer between any processes (eg LLS and PMU)
# they are pair shared memory, each component has their own read/write
# write into buffer larger amount of buffer, MN msg has pointers to the shared memory and size for shared data
# PMU reads memory from shared memory
# 8 + 3 bytes for data (3 from header)

class Message:
    def __init__(self, msg=bytes(16), data=None, data_size=0, rx_cast=None, tx_cast=None, need_response=False):
        self.msg = msg  ## message
        self.rx_cast = rx_cast  ## receiver's CAST
        self.tx_cast = tx_cast  ## sender's CAST
        self.data_size = data_size  ## size of data (if any)
        self.data = data  ## data buffer
        self.need_response = need_response ## indicator for feedback
        self.is_ack = False  ## received by the MN_Queue flag
        self.is_read = not need_response ## read flag
        # self.priority = SYSTEM_LOW


class MN_queue:
    def __init__(self):
        self.stream = [None] * SIZE_QUEUE * 4  # First 256 notification belongs to sys_h, then sys_l, usr_h, usr_l;

        self.head_ptr = [0, 256, 512, 768]  # 4 channels
        self.tail_ptr = [0, 256, 512, 768]
        self.lock = Lock()  # lock for queue

    def write(self, msg, channel:int=SYSTEM_LOW):
        # default channel system low
        self.lock.acquire()
        checks_overwrite(channel)
        self.stream[self.tail_ptr[channel]] = msg
        self.tail_ptr = ring_counter(self.tail_ptr, channel)
        self.lock.release()

    def read(self):
        # primitive operations which includes test
        self.lock.acquire()
        for channel in self.tail_ptr:
            if (head_ptr(channel) != tail_ptr(channel)):
                msg = self.stream[self.tail_ptr[channel]]
                msg.is_ack = True
                self.head_ptr = ring_counter(self.head_ptr, channel)
                self.lock.release()
                print(msg)
                return msg
        self.lock.release()
        return None
    
    #def response(self):
        
    
    def ring_counter(self, ptr:int, channel:int) -> int:
        # counts upward by one within each channel's perspective range
        return (ptr + 1) % SIZE_QUEUE + (channel * SIZE_QUEUE)

    def checks_overwrite(self, channel:int) -> None:
        # primitive overwrite warning
        curr_msg = self.stream[self.tail_ptr[channel]]
        if (type(curr_msg) == Message and curr_msg.is_ack == False and curr_msg.is_read == False):
            raise("Warning,an unread msg at channel" + channel + "is overwritten, check mn_queue \"checks_overwrite\" function")
        return None

    # def is_full(self):
    #    #test ahead of time to get rid of state and return head != tail
    #    #if (test) then read
    #    return (self.head_pointer != self.tail_pointer)

class MN_commons:
    #@staticmethod
    def __init__(self):
        def __create_all_channels() -> list:
            def __create_all_dest(src:int) -> list:
                #return [list().append(MN_queue()) for dest in range(TOTAL_PARTS) if src != dest]
                return [list().append(MN_queue()) if src != dest else list().append([]) for dest in range(TOTAL_PARTS)]
            return [__create_all_dest(src) for src in range(TOTAL_PARTS)]
        self.total_queue = __create_all_channels()

    def read(self,src:int,dest:int):
        return self.total_queue[src][dest].read()

    def write(self,src:int,dest:int,msg,channel:int=SYSTEM_LOW):
        return self.total_queue[src][dest].write(msg,channel)

    #def response(self,src,dest):

if __name__ == '__main__':
