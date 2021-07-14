import random
import sys
import os
import typing

sys.path.append("../")
from LLS.LLS import DSAST, mapBASTtoDSAST, GAST
from LLS.DAS import DPAST, mapDSASTtoDPAST
from lib.MN_Queue import MN_queue

gastTable = {} 
mn_q = MN_queue()
running_queue = []
waiting_queue = []
sleeping_queue = []
'''
class PMU:
	def __init__(self, permissions=bytes(2), encrypt=None, addr=None, CAST=None):
		global gastTable
		global procID
		global dsastTable
		global procsActive
		global procsWaiting
	
	
	blocked_queue = [] # queue for processes that become blocked
	time_queue = [] # queue for processes that become initially created
	work_queue = [] # queue for processes that are waiting to be executed and running
	cpu_process = Process(-1, "test")
'''
# program and thread CASTs (CDOT)
class CAST:  # (CDOT)
	def __init__(self, gast=None):
		self.index = random.getrandbits(22)  # actual tag is this 20-bit index
		self.mnq = MN_queue()
		self.dsasts = []
		self.src_nsasts = []
		self.dst_nsasts = []

	
	#def __next__(self)
	#TODO: if we do need a generic CAST, we could define CAST with its own iterator
	# that would iterate through the desired List/Tree which contains what we want (ie. msg, processes, tags and etc.)
	# the purpose for this is so CAST object could be more streamlined when used in other components

# PMU only communicates using SAST
# context data object IS the process
# 65k system data objects, each PAST is one of these 
# process data objects are ephemeral, only names, not "real"
# SAL just caches the tables of the CAST 
# CASTs are just processes
# 2 types of CASTs, one for threads and one for programs
# 1 CAST for program CAST, multiple for each thread CAST

class Proc:
	def __init__(self, ID=0, DSAST=DSAST(), GAST=GAST()):
		self.ID = 0 #need to figure out CAS values
		self.status = 0 # waiting = 0, running = 1, sleeping = 2
		self.DSAST = DSAST #from LLS
		self.GAST = GAST  # gast received from PN
		self.DPAST = DPAST(size=0, DSAST=self.DSAST)
		self.prog = CAST(gast=GAST)
		self.threads = [CAST(gast=GAST)]  ## need to determine how many CASTS to initialize, maybe more casts are added at runtime. one for each thread
		self.priority = 0 #influences how much run time it gets 
		self.stdin = GAST()
		self.stdout = GAST()
		self.strerr = GAST()
		self.DSAST = mapBASTtoDSAST(DSAST=self.DSAST, GAST=self.GAST)
		mapDSASTtoDPAST(self.DSAST)
		
	# def sendDPAST(self): 
	#PMU sends DPAST to PN
	#Would be a call to the PN simulator with the associated DPAST program
	#Raghul will help with		
		# return 


def createDPAST(gast):
	newproc = Proc(GAST=gast)
	return newproc

if __name__ == '__main__':
	pass