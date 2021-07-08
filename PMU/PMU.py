import random
import sys
import os
import typing
import MN_queue
sys.path.append("../")
from LLS.LLS import DSAST, mapBASTtoDSAST, GAST
from LLS.DAS import DPAST, mapDSASTtoDPAST

gastTable = {} 
mn_q = MN_queue()
running_queue = []
waiting_queue = []
sleeping_queue = []

class PMU:
	def __init__(self, permissions=bytes(2), encrypt=None, addr=None, CAST):
		global gastTable
		global procID
		global dsastTable
		global procsActive
		global procsWaiting
	
	
	blocked_queue = [] # queue for processes that become blocked
	time_queue = [] # queue for processes that become initially created
	work_queue = [] # queue for processes that are waiting to be executed and running
	cpu_process = Process(-1, "test")

	def check_normal_distribution():
  		x = np.arange(-4,4, 0.001)
  		fig, ax = plt.subplots()
		ax.plot(x, norm.pdf(x) * 100)
		plt.xlabel('Range of values picked')
  		plt.ylabel('Process time delay (seconds)')
  		plt.title('Normal Distribution for how long a process should run in Running state')
  		plt.show()

	def generate_random_normal():
  		x = np.arange(-4,4,0.001)
  		return math.ceil(norm.pdf(random.choice(x)) * 100)

	def check_exponential_distribution():
  		x = np.arange(0,6, 0.001)
  		fig, ax = plt.subplots()
  		ax.plot(x, expon.pdf(x) * 100)
  		plt.xlabel('Range of values picked')
  		plt.ylabel('Process time delay (seconds)')
  		plt.title('Exponential Distribution for how long before the next process starts')
  		plt.show()

	def generate_random_expon():
  		x = np.arange(0,6, 0.001)
  		return math.ceil(expon.pdf(random.choice(x)) * 100)

	def initial_processes(): # function to create all the initial processes
  		# for i in range(iterations):
  		#   print('Time period of %s seconds' % (generate_random_normal()))
  		time_queue.append(Process(1, "ARM")) # create a new process and insert into the initial time queue
  		current_delay = generate_random_expon()
  		# time.sleep(1) # sleep for a random period of time
  		print('It took %s seconds for this process to be created' % (current_delay))
  		time_queue.append(Process(2, "x86"))
  		current_delay = generate_random_expon()
  		# time.sleep(1)
 		print('It took %s seconds for this process to be created' % (current_delay))
  		time_queue.append(Process(3, "RISC-V"))
  		current_delay = generate_random_expon()
  		# time.sleep(1)
  		print('It took %s seconds for this process to be created' % (current_delay))
  		time_queue.append(Process(4, "MIPS"))
  		current_delay = generate_random_expon()
  		# time.sleep(1)
  		print('It took %s seconds for this process to be created' % (current_delay))
  		for i in range(4):
    			work_queue.append(time_queue.pop())

	def Process_run(env, process, resource, i):
		# Simulate driving to the BCS
		yield env.timeout(5*i)
		# TODO: Determine if I need a timeout initially
		# yield env.timeout(process.getReadyTime()) # timeout represents a delay for environment
		# # Make a request
		print('Process ID %s ready at %d' % (process.getProcessID(), env.now))
		global cpu_process # global since there is only 1 cpu process
		# account for context switches
		if (generate_random_expon() < cpu_process.getExecutionTime() and resource.count == 1): # time for next process is longer than time allocated for current process
  		print('CONTEXT SWITCH!') 
  		resource.release(resource.users.pop()) # remove the currently running process
  		work_queue.append(cpu_process)
  		print("Putting CPU process %s at end of list" % (cpu_process.getProcessID())) # stating what occurs at end of list
		with resource.request() as req: # generate an event that lets you wait until the resource becomes available again
	  	yield req # return the process with the current request
		# # Run the program
  		print('Process ID %s running its program at %s' % (process.getProcessID(), env.now))
  		blocked_queue.append(process)
  		cpu_process = process
  		cpu_process.setExecutionTime(generate_random_normal())
  		yield env.timeout(cpu_process.getExecutionTime()) # insert delay
  		print('Process ID %s completed at %s' % (process.getProcessID(), env.now))
  		### FIXME: Insert blocking/interrupts later

	def test_process_scheduler(): # function to test the process scheduler
  		env = simpy.Environment() # execution environment for event-based simulation
  		resource = simpy.Resource(env, capacity=1) # resources for environment with a capacity of processes
  		initial_processes()
  		for i in range(4):
    			env.process(Process_run(env, work_queue.pop(), resource, i))
  		env.run(until=80)
		
class Proc:
	def __init__(self, ID, DSAST, GAST=GAST()):
		self.ID = 0 #need to figure out CAS values
		self.status = 0 # waiting = 0, running = 1, sleeping = 2
		self.DSAST = DSAST() #from LLS
		self.GAST = GAST 
		self.DPAST = DPAST(size=0, DSAST=self.DSAST)
		self.priority = 0 #influences how much run time it gets 
		# need to figure out values for these
		self.data = 0
		self.heap = 0
		self.stack = 0
	
#Functions suggested by John (get on same page before deleting)
#	def respondToPN(self, count):
#		message = (data, wait, interrupt, acknowledge)
#		return message
#	# Wait - actual delay 
#	# Acknowledge - PMU receives process
	
#	def requestCache(self, value, offset):
#		return acknowledged

#Step 1
	#def receiveGAST(self, offset): 
	#PN sends GAST to PMU would eventually be a message that comes from the PN
	# when PMU gets this message, it executes the next steps
	#testGAST = GAST() # in future we need actual GAST from PN/LLS
	#	return acknowledged

#Step 2
	def sendGAST(self): 
	#call mapBASTtoDSAST (dsast=null,gast=dumby from step 1) in LLS.py does step 2 and 3
		self.DSAST = mapBASTtoDSAST(DSAST=self.DSAST, GAST=self.GAST)
		return 

#Step 3+4
	#function creates an entry in the DPAST->DSAST table 
	#The DPAST would be generated by the PMU (have to confirm with Dave) 
	#The DSAST is the one returned from the LLS

	def updateCAS(self): 
		mapDSASTtoDPAST(self.DSAST)
		return 
	
#Step 5
	def sendDPAST(self): 
	#PMU sends DPAST to PN
	#Would be a call to the PN simulator with the associated DPAST program
	#Raghul will help with		
		return 

if __name__ == '__main__':
