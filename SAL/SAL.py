#y is the addr space which is alloc to A to talk to B
#y is the system addr space
#A writes its stuff. Then, it writes a message notification to CAST_B
#B has an MN queue to pull from it and it also has a thread to pull from that address space by waking up
MAX_SOCKET = 3
class CAST_SAL:
	def __init__(self):
		self.MN_queue = MN_Queue()
		self.NPASTtoNSAST = [0] * MAX_SOCKET
		self.pc = 0
		self.DPASTtoDSAST = [0]
		self.addr = 0
		self.data = 0
		self.port_PN = 0
	def read_port(self):
		self.port_PN = data
	def write_port(self):
		self.port_PN = data
	def read_cache(self):
		return 
