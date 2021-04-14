# import numpy as np
import random
import sys
import os
import typing
# import base64
# import hashlib
# from Crypto import Random
# from Crypto.Cipher import AES

gastTable = {} # Hash table, bast to gast mapping, not in use as probably does not exist, there should probably only be 
			   # a mapping from GAST to BAST, not the inverse
oitTable = [] # could be a tree indexed by lookup uses, but functionally is just a list 
oatTable = {} # Hash table, index should be OIT's value
bastTable = {} # List of bast, key: GAST key and domain, value: BAST
bastAvail = [] # list of available bast file names
bastCnt = 0 # counter for next bast file if bastavail is empty
sastBast = {} # maps DSAST to a BAST
fpList = {} # Lists file pointers from BASTS, where the index is the BAST value


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

		# if(encrypt):
		# 	aOAT = OAT(aOIT)
		# 	gastTable[(self.domain, self.key)] = aOAT.value # not sure about this part, dave said to ignore OAT for the moment
		# else:
		# aBAST = BAST() # address for tagged data
		# bastTable[(self.domain, self.key)] = aBAST
		# TODO: also have to add a corresponding BAST/OAT


	def duplicate(self):
		newGAST = GAST(permissions=self.permissions)
		bastTable[(newGAST.domain, newGAST.key)] = bastTable[(self.domain, self.key)]

		return newGAST

	def free(self):
		del bastTable[(self.domain, self.key)]


class BAST:
	def __init__(self):

		global bastCnt
		global bastAvail

		if not bastAvail:
			if(self.checkFileExists(bastCnt)):
				self.value = bastCnt
				bastCnt += 1
			else:
				# maybe do not need this open/write?
				with open("./b/"+str(hex(bastCnt))) as file:
					file.write()
				self.value = bastCnt
				bastCnt +=1
		else:
			oldest = bastAvail.pop(0)
			if(self.checkFileExists(oldest)):
				self.value = oldest
			# clear file
			self.writeToFile("", 0)

	
	def checkFileExists(self, count):
		return os.path.exists("./b/"+str(hex(count)))

	# if offset is larger, create space for the write
	def writeToFile(self, value, offset):
		with open("./b/"+str(hex(self.value)), 'w') as file:
			# if we get an offset larger than file size, pad file to fit content
			fsize = file.seek(0, 2) - file.seek(0, 0)
			if(fsize > offset):
				file.seek(0, 2)
				file.write(0 for i in range(0, offset - fsize))
			file.seek(offset, 0)
			file.write(str(value))

	# if offset is larger, raise exception, send back msg to PMU that the process is trying to do funny stuff
	def readFromFile(self, offset):
		with open("./b/"+str(hex(self.value)), 'r') as file:
			# check max offset
			file.seek(0, 2) # 2 == SEEK_END
			max_off = file.tell()
			if(offset > max_off):
				raise ValueError
			file.seek(offset)
			return file.read()

	def open(self):
		global fpList
		fp = open("./b/"+str(hex(self.value)), "r+")
		fpList[self] = fp
		return fp

	def close(self):
		global fpList
		fp = fpList[self]
		if (type(fp) == typing.IO):
			fp.close()
		return

	def retire(self):
		# remove mapping from gast to bast
		global bastTable
		# Leave responsibility of doing the unmapping to the parent function, as there could be key conflict if multiple
		# gasts reference the same bast
		# gastTable = {v: k for k, v in bastTable.items()}
		# agast = gastTable[self]
		bastAvail.append(self.value)
		self.close()
		fpList[self.value] = 0
		# remove mapping to DSAST
		global sastBast
		for sast in sastBast:
			if sastBast[sast.dsast] == self:
				sastBast.pop(sast.dsast)
				return
		return "Did not find dsast to bast mapping"

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
		if (self.domain, self.value) not in oitTable:
			oitTable.append((self.domain, self.value))

class DSAST:
	# NOTE: this DSAST struct represents the entire DSR as described in page 29 of the manual_1y, 
	# 		thus self.offset and self.dsast compose the entire DSR struc and each DSAST field can
	#		be accessed individually as well
	# Structure(MSB to LSB): Way Limit, Size, Line Limit, Index. Part of DSR: Offset, prob useless for python simulations
	def __init__(self, address=None, index=0, lineLimit=0, size=1, wayLimit=0, offset=0):
		# Size: 0 = Large DSAST, 1 = Small DSAST
		# Offset: 40 bits for small, 50 bit for large
		# Index: (mb kinda the file name) indexing in a list of DSASTs
		# only cache fields
		# Line limit: The least significant set-bit of the this field determines the partition size and the remaining 
		# upper bits of the field determine to which of the possible ranges, of the indicated size, the DSAST is restricted.
		# Way Limit: cache restrictions. 0=RESERVED, 1=no restriction, 2=only 1st half of the cache, 3=only second half of the cache
		if(address==None):  # make new dsast
			self.size = size
			if(index != 0):
				self.index = index
			elif(size==0): # large dsast
				self.index = random.getrandbits(15)
			elif(size==1): # small dsast
				self.index = random.getrandbits(24)
			self.linelimit = lineLimit
			self.waylimit = wayLimit
			if(offset != 0):
				self.offset = offset
			else:
				if(size): # small DSAST
					self.offset = random.getrandbits(40)
				else:
					self.offset = random.getrandbits(50)
		else:  # address passed from CH
			self.size = size
			self.waylimit = waylimit
			self.linelimit = linelimit
			if(self.size): # small DSAST				
				self.index = (address >> 39) & 0xffffff # 24 bits
				self.offset = address & 0xffffffffff # 40 bits
				self.dsast = self.index | (self.lineLimit << 24) | (self.size << 29) | (self.waylimit << 30)
			else:
				self.index = (address >> 49) & 0x3fff # 14 bits
				self.offset = address & 0x3ffffffffffff # 50 bits
				self.dsast = self.index | (self.lineLimit << 14) | (self.size << 19) | (self.waylimit << 20)

# local function to get BAST value from DSAST key in dict
# parameters: 	dsast(DSAST()): DSAST to be unmapped
# returns:		BAST(): corresponding bast to dsast
def getBASTfromDSAST(dsast):
	global sastBast
	return sastBast[dsast.dsast]

# PMU function to map dsast to a bast
# parameters: 	dsast(DSAST()): DSAST to be mapped
#				gast(GAST()): optional parameter to get bast directly from GAST
# returns:		DSAST(): corresponding DSAST mapped to a BAST, if gast parameter is passed and if a matching (bast,gast)
#				pair is found, return the dsast mapped to that bast
def mapBASTtoDSAST(dsast, gast=None):
	global bastTable
	global sastBast
	# Check if GAST is mapped to a BAST
	if(not gast):
		aBast = BAST()
	elif ((gast.domain, gast.key) in bastTable.keys()):
		aBast = bastTable[(gast.domain, gast.key)]
	else:
		print("Failed to find BAST")
		return

	# Check if BAST is mapped to a DSAST
	for sast, bast in sastBast.items():
		if(bast == aBast): # already mapped
			return sast

	# Did not find a matching DSAST for the BAST
	sastBast[dsast.dsast] = aBast
	return dsast

# PMU function that requests a gast, WIP
def gastRequest(dsast):
	# randomly pick a gast, map it to the dsast's bast
	pass

# FILE OPERATION FUNCTIONS
def openFile(dsast, gast):
	global bastTable
	global sastBast
	
	if(gast != None):
		abast = bastTable[gast]
	else:
		agast = GAST()
		abast = bastTable[gast]

	if dsast not in sastBast:
		abast = BAST()

	bastsast = {v: k for k, v in sastBast.items()}
	bastsast[abast] = dsast
	sastBast[dsast.dsast] = abast
	return dsast
	# what happens if no bast is mapped to the provided gast

def createFile(dsast):
	# create a bast associated with the dsast, if there's a mapping already, scrap that
	global sastBast
	abast = BAST();
	sastBast[dsast.dsast] = abast
	return

def closeFile(dsast):
	# just unmap dsast from its bast
	global sastBast
	sastBast.pop(dsast.dsast)
	return

def saveFile(dsast, permissions):
	global sastBast
	global gastTable

	agast = GAST(permissions=permissions)
	abast = sastBast[dsast.dsast]
	bastTable[agast] = abast
	return agast

def deleteFile(gast):
	# retire the gast. if the gast is the only reference to its bast, also get rid of bast
	global bastTable
	abast = bastTable.pop((gast.domain, gast.key))

	for gast, bast in bastTable:
		if (bast == abast):
			return
	# abast not found in the dictionary
	abast.retire()	
	return

# PMU function to invalidate/retire corresponding DSAST. Sends retire call to CH and after CH completes retiring, delete
# dsast entry in the global dict
# parameters: 	dsast(DSAST()): DSAST to be unmapped
# returns:		ACK or NACKs
def invalidateDSAST(dsast):
	global sastBast
	global bastTable

	# Need to make sure the cache sends back msg that it has written back everything it need to associated with the DSAST
	sendMsgRetire()
	if(rcvOkToUnmap()):
		abast = sastBast.pop(dsast.dsast)
		gastTable = {v: k for k, v in bastTable.items()}
	# if there's already a GAST mapping to the BAST
	# JUST RETURN ACK OR NACK
		return "ACK"

# TODO: finish off invalidateDSAST to include different msgs and then TBs
# dummy function that tells CH to retire cache line, expects to call rcvOkToUnmap() afterwards
def sendMsgRetire():
	return "Retire cache line x"

# dummy function that waits for CH to respond back and acknowledgement
def rcvOkToUnmap():
	# Wait for CH to answer back if its ok from sendMsgRetire
	returnmsg = -1 # 1 if ok, 0 if not ok
	while(returnmsg != 0 or returnmsg != 1):
		# pass
		break
	return returnmsg

# CH function to map block address to DSAST
# parameters: 	addr(64-bit value): block address from CH
# returns:		corresponding dsast that has same offset and index or false if no matching dsast is found
def mapAddrToDSAST(addr):
	global sastBast
	for dsast, bast in sastBast.items():
		if(dsast.offset == (addr & 0xffffffffff) and dsast.index == (addr & 0xffffff)):
			return dsast
	return False

# CH function to read from DSAST
# parameters: 	dsast(DSAST()): DSAST() mapped to file
# returns:		void: data read from DSAST.offset
def readLLS(dsast):
	global sastBast
	# check if dsast exists
	# NOTE: changed from [dsast] to [dsast.dsast]
	return sastBast[dsast.dsast].readFromFile(dsast.offset)
	
# CH function to write to DSAST
# parameters: 	dsast(DSAST()): DSAST() mapped to file
#			 	writeData(void): data to be written to file
# returns:		nothing, but maybe should change to return fail or success
def writeLLS(dsast, writeData):
	global sastBast
	adsast = mapBASTtoDSAST(dsast.dsast)
	return sastBast[adsast.dsast].writeToFile(writeData, dsast.offset)

# CH functions that accept a non-DSAST address
# def readLLS(addr):
# 	global sastBast
# 	# check if dsast exists
# 	for dsast, bast in sastBast.items():
# 		if(dsast.offset == addr):
# 			return sastBast[dsast].readFromFile(dsast.offset)
# 	return False
	
# def writeLLS(addr, writeData):
# 	global sastBast
# 	dsast = mapAddrToDSAST()
# 	if(dsast == False): # could not find corresponding dsast with addr
# 		dsast = mapBASTtoDSAST(dsast)
# 		dsast.offset = addr
# 	return sastBast[dsast].writeToFile(writeData, dsast.offset)
	


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
	# global sastBast
	
	for i in range(0,10):
		name = "gast"+str(i)
		name = GAST()

	# print(bastTable)

	dsast = DSAST()
	gastlist = [gast for gast in bastTable]
	agast = gastlist[0]
	print(agast)
	# mapBASTtoDSAST(dsast, agast)
	# sastBast = openFile(dsast, agast)

	# abast = sastBast[dsast]
	# print(abast.value)
	# abast.writeToFile(dsast, 0)
