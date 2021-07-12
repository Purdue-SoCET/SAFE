from MN_queue import *

def printf(s):
	global WRITE
	MN_queue_PMU.write(Message(msg=WRITE,data=s,rx=CAST_PMU))
