# import numpy as np
import random
import sys
import os
# import base64
# import hashlib
# from Crypto import Random
# from Crypto.Cipher import AES

gastTable = {} # Hash table, bast to gast mapping, not in use
oitTable = [] # could be a tree indexed by lookup uses, but functionally is just a list 
oatTable = {} # Hash table, index should be OIT's value
bastTable = {} # List of bast, key: GAST key and domain, value: BAST
bastAvail = [] # list of available bast file names
bastCnt = 0 # counter for next bast file if bastavail is empty
sastBast = {} # maps DSAST to a BAST
fpList = [] # Lists file pointers from BASTS, where the index is the BAST value

################################################################################
# TWO WAY DICTIONARY
# https://stackoverflow.com/questions/1456373/two-way-reverse-map
# https://stackoverflow.com/questions/3318625/how-to-implement-an-efficient-bidirectional-hash-table?rq=1
# https://stackoverflow.com/questions/7657457/finding-key-from-value-in-python-dictionary
################################################################################

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

		# TODO: add a function to add entry to OIT tree/table
		if(encrypt):
			# aOAT = OAT(aOIT)
			# gastTable[(self.domain, self.key)] = aOAT.value # not sure about this part, dave said to ignore OAT for the moment
			aBAST = BAST()
			bastTable[(self.domain, self.key)] = aBAST # BAST is the GAST's value
			gastTable[aBAST] = 
		else:
			aBAST = BAST() # address for tagged data
			bastTable[(self.domain, self.key)] = aBAST
		# TODO: also have to add a corresponding BAST/OAT
		
	# TODO: external calls can create, duplicate, and free a particular GAST
	def duplicate(self):
		newGAST = GAST(permissions=self.permissions)
		bastTable[(newGAST.domain, newGAST.key)] = bastTable[(self.domain, self.key)]

		return newGAST

	def free(self):
		del bastTable[(self.domain, self.key)]

# what does the LLS do if the offset provided in the DSR is larger than the file size referenced by the BAST

class BAST:
	def __init__(self):

		global bastCnt
		global bastAvail

		if not bastAvail:
			if(self.checkFileExists(bastCnt)):
				self.value = bastCnt
				bastCnt += 1
			else:
				with open("./b/"+str(hex(bastCnt))) as file:
					file.write()
				self.value = bastCnt
				bastCnt +=1
				pass # TODO: What to do when file does not exist??
		else:
			oldest = bastAvail.pop(0)
			if(self.checkFileExists(oldest)):
				self.value = oldest

	
	def checkFileExists(self, count):
		return os.path.exists("./b/"+str(hex(count)))

	# if offset is larger, create space for the write
	def writeToFile(self, value, offset):
		with open("./b/"+str(hex(self.value)), 'w') as file:
			file.seek(offset)
			file.write(str(value))

	# TODO: make function for partial writes, current one only accepts offset and writes entire packet

	# if offset is larger, raise exception, send back msg to PMU that the process is trying to do funny stuff
	def readFromFile(self, offset):
		with open("./b/"+str(hex(self.value)), 'r') as file:
			# check max offset
			file.seek(0, SEEK_END)
			max_off = file.tell()
			if(offset > max_off):
				raise ValueError
			file.seek(offset)
			return file.read()

	def open(self):
		global fpList
		fp = open("./b/"+str(hex(self.value)), 'r')
		fpList[self] = fp
		return fp

	def close(self):
		global fpList
		fp = fpList[self]
		fp.close()
		return

	def retire(self):
		# remove mapping from gast to bast
		global bastTable
		gastTable = {v: k for k, v in bastTable.items()}
		agast = gastTable[self]
		bastAvail.append(bastTable.pop((agast.domain, agast.key)).value)

		# remove mapping to DSAST
		global sastBast
		bastsast = {v: k for k, v in sastBast.items()}
		dsast = bastsast[self]
		sastBast.pop(dsast)
		return

class OIT:
	def __init__(self, permissions):
		global oitTable
		# first 16 bits of domain indicate permissions and last 16 bits are actual domain.
		self.permissions = permissions
		# establish domains, not random
		# for now, 2 domains: code or data
		self.domain = random.getrandbits(16) 
		self.key = random.getrandbits(448)
		self.value = bytes(4) # 32 bit representation of BAST
		# need to check if key does not exist in domain before addying entry to hash table
		# not sure if this is what goes into the oitTable...
		if (self.domain, self.value) not in oitTable.keys():
			oitTable[(self.domain, self.value)] = self.value

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
		
#################################################################
# PMU asks for a mapping of GAST to some SAST, use this GAST to make
# the SAST to BAST translation. Check if this GAST is mapped to a BAST already
# being in use. Then, we cannot map it to two different SAST. If the 
# BAST is mapped to a SAST, it returns that SAST, otherwise it returns 
# the SAST given by PMU with the given mapping
# dictionary (SAST, BAST)
# GAST only serves to map BAST to a SAST, GAST is ephemeral
#################################################################

# open file when doing this mapping, keep track of opened files
def mapBASTtoDSAST(dsast, gast):
	global bastTable
	global sastBast
	# Check if GAST is mapped to a BAST
	if ((gast.domain, gast.key) in bastTable.keys()):
		aBast = bastTable[(gast.domain, gast.key)]
	elif(not gast):
		aBast = BAST()
	else:
		return "Failed to find BAST"

	# Check if BAST is mapped to a DSAST
	for dsast, bast in sastBast.items():
		if(bast == aBast): # already mapped
			return dsast

	# Did not find a matching DSAST for the BAST
	sastBast[dsast] = aBast
	return dsast

def gastRequest(dsast):
	# randomly pick a gast, map it to the dsast's bast
	pass

# Write cache line to DSAST's BAST
def writeToBAST(dsast):
	global sastBast
	try:
		abast = sastBast[dsast]
		abast.writeToFile(DSAST=dsast, offset=DSAST.offset)
		return
	except:
		print("Could not write to DSAST's BAST\n")

def openFile(dsast, gast):
	global bastTable
	global sastBast
	
	if(gast != None):
		abast = bastTable[gast]
	else:
		agast = GAST()
		abast = bastTable[gast]
# need to address: when gast has an existing mapping, return DSAST mapped
	#########################################################
	# 	NEW NOTE
	# If DSAST is not found in SAST to BAST table and the GAST is null, should we allocate a new BAST? No, this happens in createfile
	# open and create

	if(not sastBast[dsast]):
		abast = BAST()

	bastsast = {v: k for k, v in sastBast.items()}
	bastsast[abast] = dsast
	sastBast[dsast] = abast
	return dsast
	# sastbast = {v: k for k, v in bastsast.items()}
	# return sastbast
	# what happens if no bast is mapped to the provided gast

def createFile(dsast):
	# create a bast associated with the dsast, if there's a mapping already, scrap that
	pass

def closeFile(dsast):
	# just unmap dsast from its bast
	global sastBast
	sastBast.pop(dsast)
	return

def saveFile(dsast, permissions):
	# TODO
	global sastBast
	global gastTable

	agast = GAST(permissions=permissions)
	abast = sastBast[dsast]
	bastTable[agast] = abast
	return agast

def deleteFile(gast):
	# retire the gast. if the gast is the only reference to its bast, also get rid of bast
	global bastTable
	abast = bastTable.pop(gast)
	# now need to check if this gast was the last reference to the bast

	#############################################################################
	# 	NEW NOTES
	# If there are no more DSASTS using a BAST, but there be a GAST tied to it, then are we still alowed to retire the BAST?
	# Does the PMU know which GASTs are tied to which DSASTs
	#############################################################################
	return

def getBASTfromDSAST(dsast, sastbast=sastBast):
	return sastbast[dsast]

def invalidateDSAST(dsast):
	global sastBast
	global bastTable

	# Need to make sure the cache sends back msg that it has written back everything it need to associated with the DSAST
	sendMsgRetire()
	if(rcvOkToUnmap()):
		abast = sastBast.pop(dsast)
		gastTable = {v: k for k, v in bastTable.items()}
	# if there's already a GAST mapping to the BAST
	# JUST RETURN ACK OR NACK
		return ACK

# 16k packets for now
def writeThrough(dsast, packet):
	global sastBast
	#############################################################################
	# NEW NOTES
	# For write through, if there's no DSAST associated, should we raise Exception?
	# always an exception for the entire LLS

	
	
	abast = sastBast[dsast]
	abast.writeToFile(packet, dsast.offset)
	return

def sendMsgRetire():
	return "Retire cache line x"

def rcvOkToUnmap():
	# Wait for CH to answer back if its ok from sendMsgRetire
	returnmsg = -1 # 1 if ok, 0 if not ok
	while(returnmsg != 0 || returnmsg != 1):
		pass
	return returnmsg

# TB for LLS
# Scenario based testing model. Create objects, write to them, open, close, read, write, etc...
# Make sure we can create objs and put data into them. Use 4 byte cache model for testing.
# After basic testing is implemented, randomize accesses. Add a list to keep track of BAS sizes.
# Test for invalid inputs (size is off etc.) to ensure it sends back msg to PMU/CH.
# Test case for gain a msg to retire bast

# TODO: adjust openFile function. if dont find GAST -> BAST mapping, create a new one and map it to a DSAST
# TODO: finish off invalidateDSAST to include different msgs and then TBs

# open file (and creating file), close file (retire the bast), read, write, invalidate (same as retiring), respond to invalidations

# operations for CH
# read, write, write through (when L5 writes data to the LLS and line becomes clean in the L5, for the LLS it looks the same as write),
# invalidation/discard (LLS throws away cache line) can combine write through with discard, will implement write in later
# operations for PMU
# create data obj, write data obj, read data obj, close data obj

# class OAT:
#	def __init__(self, OIT):
#		self.key = random.getrandbits(256) # will prob be an AES key, I think
#		self.value = self.checksum(OIT)	   # checksum using the data referenced by the OIT and the self.key
# 		#TODO: create entry in OAT Table, index is OIT, value is self
		# the manual says we index by the OIT value, but wth is this value...
		# just using the OIT itself for the time being
#		oatTable[OIT] = self
		#TODO: encrypt data and assign self.key to be the key of the encryption 

#	def checksum(self, OIT): 
# checksum for every 16k of data
# offset of data block as a rotation on the key, so that given the base key in the OAT
# you can use a different key for every 16k block, vector of checksums
#		return self.key ^ OIT.key


# class AESCipher(object): 
# 	#AESCipher class from: https://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256

#     def __init__(self, key): 
#         self.bs = AES.block_size
#         self.key = hashlib.sha256(key.encode()).digest()

#     def encrypt(self, raw):
#         raw = self._pad(raw)
#         iv = Random.new().read(AES.block_size)
#         cipher = AES.new(self.key, AES.MODE_CBC, iv)
#         return base64.b64encode(iv + cipher.encrypt(raw.encode()))

#     def decrypt(self, enc):
#         enc = base64.b64decode(enc)
#         iv = enc[:AES.block_size]
#         cipher = AES.new(self.key, AES.MODE_CBC, iv)
#         return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

#     def _pad(self, s):
#         return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

#     @staticmethod
#     def _unpad(s):
#         return s[:-ord(s[len(s)-1:])]


if __name__ == '__main__':
	
	for i in range(0,10):
		name = "gast"+str(i)
		name = GAST()

	# print(bastTable)

	dsast = DSAST()
	gastlist = [gast for gast in bastTable]
	agast = gastlist[0]
	print(agast)
	# mapBASTtoDSAST(dsast, agast)
	sastBast = openFile(dsast, agast)

	abast = sastBast[dsast]
	print(abast.value)
	abast.writeToFile(dsast, 0)
