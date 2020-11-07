import socket
from MN_queue import *
# import thread module 
from thread import *
import threading    
import random
import sys         
 #threading 
# next create a socket object
#dump the socket number into a named file (e.g what is lls socket number)
#others read from it 
#give all systems names, they open up sockets on bootup and write the socket numbers to files
#each HW comp has 2 sockets (if datagram, then add header e.g if cache trans or message notific)
print_lock = threading.Lock() 
#CAST and SSR implementation
  
# reserve a port on your computer in our 
# case it is 12345 but it can be anything 
port = random.randint(2000,5000)  
file_o = open("PMU.txt","w")              
file_o.write("{}".format(port))
file_o.close()  
#Listening
###############

def client_connection():
	slisten = socket.socket()     
	file_name =  sys.argv[1]
	file_i = open(file_name+".txt",'r')
	portlisten = int(file_i.read())
	slisten.connect(('127.0.0.1', portlisten)) 
	# receive data from the server 
	print("Receving data from SNE")
	print slisten.recv(1024) 
	# close the connection 
	slisten.close()   
	print("Received data")

client_connection()

s = socket.socket()          
print "Socket successfully created"
# connect to the server on local computer 

     
############  
# thread function 
def threaded(c): 
    while True: 
  
        # data received from client 
        data = c.recv(1024) 
        if not data: 
            print('Bye') 
              
            # lock released on exit 
            print_lock.release() 
            break
  
        # reverse the given string from client 
        data = data[::-1] 
  
        # send back reversed string to client 
        c.send(data) 
  
    # connection closed 
    c.close()  
  
  
# Next bind to the port 
# we have not typed any ip in the ip field 
# instead we have inputted an empty string 
# this makes the server listen to requests  
# coming from other computers on the network 
s.bind(('', port))         
print "socket binded to %s" %(port) 
  
# put the socket into listening mode 
s.listen(5)      
print "socket is listening"            
  
# a forever loop until we interrupt it or  
# an error occurs 
while True: 
  
   # Establish connection with client. 
   c, addr = s.accept()      
   print 'Got connection from', addr 
   print_lock.acquire() 
   # send a thank you message to the client.  
   c.send('Thank you for connecting to PMU') 
  
   # Close the connection with the client 
   start_new_thread(threaded, (c,)) 
s.close() 
