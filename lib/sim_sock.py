import socket
import select

class DSAST:
	# Structure(MSB to LSB): Way Limit, Size, Line Limit, Index, Offset, prob useless for python simulations
	def __init__(self, index=0, lineLimit=0, size=0, wayLimit=0):
		# Size: 0 = Large DSAST, 1 = Small DSAST
		# Offset: 40 bits for small, 50 bit for large
		# Index: (mb kinda the file name) indexing in a list of DSASTs
		# only cache fields
		# Line limit: The least significant set-bit of the this field determines the partition size and the remaining 
		# upper bits of the field determine to which of the possible ranges, of the indicated size, the DSAST is restricted.
		# Way Limit: cache restrictions. 0=RESERVED, 1=no restriction, 2=only 1st half of the cache, 3=only second half of the cache

		self.size = size
		self.index = index
		self.linelimit = lineLimit
		self.waylimit = wayLimit
		if(size): # small DSAST
			self.offset = random.getrandbits(40)
		else:
			self.offset = random.getrandbits(50)

class GAST:
	global bastTable
	def __init__(self, permissions=bytes(2), encrypt=None, addr=None):
		# permissions: permissions for given GAST, are the first half of the domain
		# encrypt: is a flag for whether or not to encrypt the GAST
		# addr: is the location where the GAST's data will be stored,
		# assuming the processor or process manager is what allocated 
		# a GAST to a given process
		aOIT = OIT(permissions)
		# dividing the domain in half: permissions and the actual domain
		self.permissions = aOIT.permissions
		self.domain = aOIT.domain
		self.key = aOIT.key
		aBAST = BAST() # address for tagged data
		bastTable[(self.domain, self.key)] = aBAST

# Packet struct. Refer to John's Notes for component id and extra details on connections
class Pack:
	def __init__(self, origin, destination, content):
		self.origin = origin
		self.destination = destination
		self.content = content

def open_listenfd(port, host=''):
	# port: port to bind to, need to specify a port
	# host: host to bind to, default is any host
		
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
	s.bind((host, port))
	s.listen(5)
	return s

def on_new_client(clientsocket,addr):
    while True:
        msg = clientsocket.recv(1024)
        #do some checks and if msg == someWeirdSignal: break:
        print addr, ' >> ', msg
        #msg = raw_input('SERVER >> ')
        #Maybe some code to compute the last digit of PI, play game or anything else can go here and when you are done.
        #clientsocket.send(msg)
    clientsocket.close()

def start_listen_conns(components=[]):
	# components: list of tuples containing port and host values for each component to connect
	#			  components = [(port, host)]
    # open socket for each component and listen to all ports
    socks = []
	for component in components:
		socks.append(open_listenfd(port=component[0], host=component[1]))

	while True:
		rdy_socks,_,_ = select.select(socks, None, None)
		for sock in rdy_socks:
			(conn, address) = sock.accept()
			thread.start_new_thread(on_new_client,(c,addr))

	for sock in socks:
		sock.close()