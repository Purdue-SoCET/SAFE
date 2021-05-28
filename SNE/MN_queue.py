#Socket Messaged Notification model
#MN used to tell other socket readers that socket is being written to
#Blocking of other sockets
#SSR number of additional bytes 
#need to more about SSR
#test for fill up
#need to decide if equal is empty
from multiprocessing import Lock

SIZE_QUEUE = 256 * 16
SIZE_BUFFER = (1 << 16) * 16  #to avoid overflow
# LLS NOTES
# make buffer hold 256 notifications (around 4k), each message containing 16 bytes (most bytes just say source, 
# when msg arrived (metadata)) 256 is a nice number, as head/tail management can be done with just a uchar
# if msg is larger than 11bytes, ther is a shared memory buffer between any processes (eg LLS and PMU)
# they are pair shared memory, each component has their own read/write 
# write into buffer larger amount of buffer, MN msg has pointers to the shared memory and size for shared data
# PMU reads memory from shared memory
# 8 + 3 bytes for data (3 from header)

class Message:
	def __init__(self, msg=bytes(16), data=None):
		self.msg = msg
		self.data = data

class MN_queue:
    def __init__(self):
        self.stream = [None] * SIZE_QUEUE 
        self.head_pointer = 0
        self.tail_pointer = 0
        self.lock = Lock()  # lock for queue

    def write(self, msg):
        self.lock.acquire()
        self.stream[self.tail_pointer] = msg
        self.tail_pointer += 1
        self.lock.release()

    def read(self): 
        #primitive operations which includes test
        self.lock.acquire()
        if not (self.is_full()):
            msg = self.stream[self.head_pointer]
            self.head_pointer += 1
            self.lock.release()
            print(msg)
            return msg

        self.lock.release()
        return None

    def is_full(self):
        #test ahead of time to get rid of state and return head != tail
        #if (test) then read
        return (self.head_pointer != self.tail_pointer)
         

    