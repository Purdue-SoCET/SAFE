# Socket Messaged Notification model
# MN used to tell other socket readers that socket is being written to

# LLS NOTES
# make buffer hold 256 notifications (around 4k), each message containing 16 bytes (most bytes just say source,
# when msg arrived (metadata)) 256 is a nice number, as head/tail management can be done with just a uchar
# if msg is larger than 11bytes, ther is a shared memory buffer between any processes (eg LLS and PMU)
# they are pair shared memory, each component has their own read/write
# write into buffer larger amount of buffer, MN msg has pointers to the shared memory and size for shared data
# PMU reads memory from shared memory
# 8 + 3 bytes for data (3 from header)
from threading import Lock
from enum import Enum
import queue
import time


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


class Message:
    def __init__(self, msg=bytes(16), data=None, data_size=0, rx_cast=None, tx_cast=None, need_response=False):
        self.msg = msg  ## message
        self.rx_cast = rx_cast  ## receiver's CAST
        self.tx_cast = tx_cast  ## sender's CAST
        self.data_size = data_size  ## size of data (if any)
        self.data = data  ## data buffer
        self.need_response = need_response  ## indicator for feedback
        self.is_ack = False  ## if the receiver reads the message
        self.is_read = not need_response  ## read flag
        # self.priority = SYSTEM_LOW


class MN_queue:
    def __init__(self):
        self.stream = [None] * SIZE_QUEUE * 4  # First 256 notification belongs to sys_h, then sys_l, usr_h, usr_l;

        self.head_ptr = [0, 256, 512, 768]  # 4 channels
        self.tail_ptr = [0, 256, 512, 768]
        self.lock = Lock()  # lock for queue

    def write(self, message: Message, channel: int = SYSTEM_LOW):
        # default channel system low
        # return True for successful write, False for unsuccessful write
        # Do not use this func directly as it's not thread safe, use MN_Commons instead
        if self.checks_overwrite(channel):
            return False
        tail_value = self.tail_ptr[channel]
        self.stream[tail_value] = message
        self.tail_ptr[channel] = self.ring_counter(tail_value, channel)
        return True

    def read(self):
        # primitive operations which includes test
        # Return the message when a new one is found, return None when not found.
        # Do not use this func directly as it's not thread safe, use MN_Commons instead
        for channel,head_value in enumerate(self.head_ptr):
            if head_value != self.tail_ptr[channel]:
                msg = self.stream[head_value] ## equivalent to tail_ptr - 1
                self.head_ptr[channel] = self.ring_counter(head_value, channel)
                return msg
        return None


    def ring_counter(self, ptr: int, channel: int) -> int:
        # counts upward by one within each channel's perspective range
        return (ptr + 1) % SIZE_QUEUE + (channel * SIZE_QUEUE)


    def continuous_read(self):
        # Continuously read the stream and returns any new message as a generator
        while True:
            self.lock.acquire()
            if self.tail_ptr != self.head_ptr:
                yield self.read()
            self.lock.release()

    def checks_overwrite(self, channel: int) -> None:
        # primitive overwrite warning
        curr_msg = self.stream[self.tail_ptr[channel]]
        if type(curr_msg) == Message and curr_msg.is_ack == False and curr_msg.is_read == False:
            return True
            #raise ("Warning,an unread msg at channel" + channel + "is overwritten, check mn_queue \"checks_overwrite\" function")
        return False


class MN_commons:
    # @staticmethod
    def __init__(self):
        def __create_all_channels() -> list:
            __create_all_dest = lambda src : [MN_queue() if src != dest else None for dest in range(TOTAL_PARTS)]
            return [__create_all_dest(src) for src in range(TOTAL_PARTS)]

        self.total_queue = __create_all_channels()
        ## self.total_queue[in the view of (LLS/PMU/CH...)][message from this component]


    def read(self, src: int, dest: int):
        desired_queue = self.total_queue[src][dest]
        desired_queue.lock.acquire()
        message = desired_queue.read()
        desired_queue.lock.release()
        return message


    def write(self, src: int, dest: int, message, channel: int = SYSTEM_LOW):
        desired_queue = self.total_queue[dest][src]
        desired_queue.lock.acquire()
        write_status = desired_queue.write(message,channel)
        desired_queue.lock.release()
        return write_status

    # have a queue (list) for messages waiting for response. In read() method have cases to catch responses and mark
    # waiting messages in the list as read (pop them out of the list and return to original function)
    def wait_msg(self, src: int, dest: int):
        # Only returns msg when is new message is found
        yield from self.total_queue[src][dest].continuous_read()


    #def wait_msg_for_all(self, src:int):

    # def response(self,src,dest):

if __name__ == '__main__':
    test_commons = MN_commons()

    ## Fetch data
    test_commons.write(Parts.PMU.value, Parts.LLS.value, Message(data="Low priority data"), channel=USER_LOW)
    test_commons.write(Parts.PMU.value, Parts.LLS.value, Message(data="Random Data1"))
    test_commons.write(Parts.PMU.value, Parts.LLS.value, Message(data="Random Data2"))
    test_commons.write(Parts.PMU.value, Parts.LLS.value, Message(data="Random Data3"))
    test_commons.write(Parts.PMU.value, Parts.LLS.value, Message(data="Random Data4"))
    test_commons.write(Parts.PMU.value, Parts.LLS.value, Message(data="Top priority data"),channel=SYSTEM_HIGH)
    idx = 0
    for msg in test_commons.wait_msg(Parts.LLS.value,Parts.PMU.value):
        print(msg.data)
        # Do whatever we want with the message
        #time.sleep(2)
        idx += 1
        if (idx > 5):
            test_commons.total_queue[Parts.LLS.value][Parts.PMU.value].lock.release()
            break

    # communication with response -- through communication within mn_queue
    test_commons.write(Parts.PMU.value, Parts.LLS.value, Message(data="Can I have your attention?",need_response=True))
    for msg in test_commons.wait_msg(Parts.LLS.value,Parts.PMU.value):

        if msg.need_response == True:
            print(msg.data)
            msg.data = "Yes what can I do for you?"
            test_commons.write(Parts.LLS.value,Parts.PMU.value,msg)
            break

    for msg in test_commons.wait_msg(Parts.PMU.value,Parts.LLS.value):
        if msg.need_response == True:
            print(msg.data)
            msg.data = "Thank you"
            msg.need_response = False
            test_commons.write(Parts.PMU.value,Parts.LLS.value,msg)
            break

    for msg in test_commons.wait_msg(Parts.LLS.value,Parts.PMU.value):
        print(msg.data)
        test_commons.write(Parts.LLS.value,Parts.PMU.value,msg)
        break



