from MN_queue import *

def printf(s):
	global WRITE
	for i in range(len(s)):
		MN_queue_PMU.write(Message(msg=WRITE,data=s[i],rx=CAST_PMU))
