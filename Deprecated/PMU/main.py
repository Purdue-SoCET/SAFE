from process import *

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





PN_buffer = []
PMU_buffer = []
LLS_buffer = []
SAL_buffer = []

# def syscalls(items):
#   call = items.pop()
#   if (call == "write"):

# def receive(sender, receiver, mode, items):
#   if receiver == 0: # PMU is reading
#     mode = items.pop()
#     if mode == "syscall":
#       syscalls(items)

def Step1():
  # PMU_buffer.append(["DPAST", 3])
  # GAST info includes 448-bit key and 32-bit Domain 
  PMU_buffer.append(["GAST", "0xd6382592", "0x54fa0ef382237953ab0e136439970f18d2ff5a812cc2bcac3ed9c033a58358051fa3c89c7c342995f0a26c6042f4dc64cab8e37109b4447f"])
  print("GAST key: ", PMU_buffer[0][1])

def Step2():
  LLS_buffer.append(PMU_buffer[0])

def Step3(): # PMU sends DSAST with GAST info to SAL (map GAST to DSAST)
  GAST_info = LLS_buffer.pop()
  GAST_key = GAST_info[1]
  # List of all GASTs. First value 0 means that GAST is not available. Second value 0 means currently in-use by different PN
  GAST_Table = [[1, 1, "0xd6382592"], [1, 0, "0xc3976200"], [0, 1, "0x915b9e1d"], [1, 1, "0x784a832a"], [1, 1, "0xb63df1bf"], [0, 0, "0x983b6edf"], [1, 1, "0x8d58631a"], [1, 1, "0x01e39188"]]
  flag = 0 # flag indicates if GAST is in current table

  for entry in GAST_Table:
    if entry[2] == GAST_key:
      flag = 1
      GAST_entry = entry
      break

  if flag == 0:
    return -1

  if GAST_entry[0] == 0:
    return -1
  elif GAST_entry[1] == 0:
    PMU_buffer.append(["DSAST", "in-use"])
    return 0
  else:
    PMU_buffer.append(["DSAST", "0xFF531276"])
    PMU_buffer.append(["BAST", "0x001254AB"])
    print("DSAST returned is: ", PMU_buffer[1][1])
    print("BAST assigned is: ", PMU_buffer[2][1])
    return 1

def Step3_SAL():
  SAL_buffer.append(PMU_buffer[0])
  SAL_buffer.append(PMU_buffer[1])

def Step4():
  # CAS table with DPAST->DSAST translations
  # 8 total DSASTs available with 3 bits of DPAST to specify
  # First value is 1 if DPAST is mapped to a DSAST
  CAS_Table = [[1, "0x0"], [1, "0x0"], [0, "0x0"], [0, "0x0"], [0, "0x0"], [0, "0x0"], [0, "0x0"], [0, "0x0"]]
  for i in range(len(CAS_Table)):
    if (CAS_Table[i][0] == 0):
      CAS_Table[i][0] = 1
      CAS_Table[i][1] = PMU_buffer[0][1] # store DSAST value in
      return i # DPAST value()


def Step5(DPAST_value):
  # Send DPAST back to PN
  PN_buffer.append(["DPAST", DPAST_value])
      


def test_hello_world():
  sleep(.5)
  Step1()
  print("Step 1: PN sends GAST to PMU")
  
  sleep(.5)
  Step2()
  print("Step 2: PMU sends GAST to LLS")

  sleep(.5)
  Step3()
  print("Step 3: LLS makes decision on returning DSAST based on GAST")
  
  sleep(.5)
  Step3_SAL()
  print("Step 3: PMU sends GAST and DSAST to SAL")
  
  sleep(.5)
  DPAST = Step4()
  print("Step 4: Place DPAST -> DSAST in CAS")
  print("DPAST index: ", DPAST)
  
  sleep(.5)
  Step5(DPAST)
  print("Step 5: PMU sends DPAST to PN")
  print("PN now has access to proper address to perform reads and writes.")

if __name__ == '__main__' :
  test_hello_world()



