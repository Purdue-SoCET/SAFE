#Socket Messaged Notification model
#MN used to tell other socket readers that socket is being written to
#Blocking of other sockets
#SSR number of additional bytes 
#need to more about SSR
#test for fill up
#need to decide if equal is empty
SIZE_BUFFER = (1 << 16) * 16#to avoid overflow
class MN_queue:
    def __init__(self):
        self.stream = [None] * SIZE_BUFFER 
        self.head_pointer = 0
        self.tail_pointer = 0
    def write(self,byte):
        self.stream[self.tail_pointer] = byte
        self.tail_pointer += 1
    def read(self): 
        #primitive operations which includes test
        self.test()
        temp = self.stream[self.head_pointer]
        self.head_pointer += 1
        print(temp)
        return temp
    def test(self):
        #test ahead of time to get rid of state and return head != tail
        #if (test) then read
        return (self.head_pointer != self.tail_pointer)
         

    