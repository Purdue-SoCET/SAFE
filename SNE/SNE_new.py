#SNE simulation @author: Raghul Prakash
import threading
from CH_param_sim import *
import L4_cache
from pwn import *
import time

global MAX_SYS_SOCKET = 2
global CAST_PMU = 1
global CAST_SNE = 8
global CAST_SAL = 16
global READ = 0
global WRITE = 1
global ACK
global buff

#semaphores of each thread/socket/NAS
ACK = [threading.Semaphore(value=1)] * MAX_SYS_SOCKET

#message format: NPAST, CAST, NSAST
"""
SNE:
the SNE is a network proxy that is managed by a separate embedded system. This containerization makes it more secure than
running the networking stack the kernel.
Currently supports IPC across two processes. Next, need to connect to external IP with HTTP methods
"""
class SNE:
	"""
	__init__:
	Constructor that initializes the SNE. The SNE has an MN queue for message notifications indicating either setup/packet send/ teardown. It has a control table
	that indicates which NAS is busy/active and a local L3 cache. It has multiple threads running per NAS that iteract with the TCP/IP stack
	"""
	def __init__(self):
		self.MN_Queue = MN_Queue() #Message Notification q ueue of the SNE
		self.control_table = [0] * MAX_SYS_SOCKET #The state of the socket/NAS. is it active/idle.
		self.CAST_SNE = 17 #The CAST/PID of the SNE
		self.L3_cache = L3cache() #The local L3 cache
		self.system_sockets =[threading.Thread(thread_function,args=(sys_NSAST,message),name=str(i)) for i in range(2 * MAX_SYS_SOCKET)] #2x because two address spaces. one for rx and tx
		self.message = 0 #the current message that is being read by the SNE.
		#Socket remote connection. MAX_SYS_SOCKET number of threads are being run and started by __init__. The argument passed is the socket
		#handle.
		#multiply MAX by 2 since there is two address spaces that are orthogonal. one for rx and the other for tx
		for NSAST in range(2 * MAX_SYS_SOCKET):
			socket_NSAST = remote('127.0.0.1', 3000 + NSAST)
			ACK[NSAST].acquire()
			self.system_sockets[NSAST].start(self, NSAST)
		self.main()
	"""
	thread_function:
	each socket/NSAST runs a parallel thread that receives a packet via the L3 cache from the SAL.
	this packet is passed into the TCP/IP stack and a new packet coming from it (IP packet) is passed in to the NAS.
	the NAS has a local copy in the L3 cache. the new packet is written into this address space.
	"""
	def thread_function(self, NSAST):
		while (True):
			ACK[NSAST].acquire()
				buff = Cache_Hierarchy(READ,NSAST,None)		#read from the NAS address of the Cache Hierarchy. this is the packet coming from the PN via the SAL
				self.system_sockets[NSAST].send(buff) #send this packet into the TCP/IP stack for it to become a TCP/IP packet
				time.sleep(1) #wait for the packet to be sent into the stack
				inv_NSAST = 3000 + MAX_SYS_SOCKET + NSAST #use the other orthogonal address space a.k.a invert it
				buff_ip = self.system_sockets[inv_NSAST].recv(buff) #receive the ip packet from TCP/IP stack and pass it into a buffer
				Cache_Hierarchy(WRITE,inv_NSAST,buff_ip)  #write this buffer into the Cache Hierarchy
			ACK[NSAST].release()	
	"""
	main:
	Needs to be called to start the SNE. This is the entry point. It first reads valid message from the MN queue.
	Then checks if the message is a setup or a read/write.   
	"""
	def main(self):
		while (True):
			message = MN_decode(Cache_Hierarchy(READ,CAST_SNE, None)) #read the MN address space of SNE and decode the message
			if (MN_decode(message).valid == True): # check if the message is valid
				if (MN_decode(message).setup == True): #check if it is a setup message or an actual read/write message
					for i in range(MAX_SYS_SOCKET): #find available socket and enable/activate it
						if (self.control_table[MAX_SYS_SOCKET].enable == 0):
							self.control_table[MAX_SYS_SOCKET].enable = 1
							break
						NSAST = i
						self.control_table[i].NPAST = MN_decode(message).NPAST #the control table should also store the NPAST that is used for this socket
						self.control_table[i].CAST = MN_decode(message).CAST #it should also store which CAST/PID this socket is attached to now
					Cache_Hierarchy(WRITE,CAST_PMU,MN_encode(NSAST)) #it should send/write the NSAST that the SNE selected to the PMU
				#setup is done
				else if (MN_decode(message).read): #for read/write 
					if MN_decode(message).read: #the message is a read and the message also contains the NSAST 
						if (message.valid):
							NSAST = MN_decode(message).NSAST
							ACK[NSAST].release() #release the lock so that the thread can acquire in an run its code
					#writes are tougher and more complicated. needs more work for writes
					#else if MN_decode(message).write:
					#	Cache_Hierarchy(WRITE,MN_encode(NSAST, CAST_SNE, NPAST) + ,None)	
					#	Cache_Hierarchy(WRITE,MN_decode(message).NSAST,None)								


if (__name__ == "__main__"):
	SNE = SNE()
