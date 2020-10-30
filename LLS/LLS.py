# import numpy as np
import random
import sys
import os
# import base64
# import hashlib
# from Crypto import Random
# from Crypto.Cipher import AES

gastTable = {} # Hash table
oitTable = {} # could be a tree also
oatTable = {} # Hash tab
bastTable = {} # List of bast
bastAvail = [] # list of available bast file names
bastCnt = 0 # counter for next bast file if bastavail is empty
sastBast = {}

# TODO: create read that is a DSAST offset

#################################################################
# Page 24
# At any given point in time, the potentially vast array of data objects
# (BASs) that are not mapped to DSASTs are inaccessible to any/all of a
# system’s programs. A program cannot independently map a BAS to a
# DSAST unless it knows the BAS’s associated GAST value (or one of its
# associated GASTs), and even then it can only request a mapping from
# its PMU
#################################################################
# Page 27 for table referencing DSAST Structure

class GAST:
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
			aBAST = BAST(addr)
			bastTable[(self.domain, self.key)] = aBAST # BAST is the GAST's value
		else:
			aBAST = BAST(addr) # address for tagged data
			bastTable[(self.domain, self.key)] = aBAST
		# TODO: also have to add a corresponding BAST/OAT
		
	# TODO: external calls can create, duplicate, and free a particular GAST
	def duplicate(self):
		newGAST = GAST(permissions=self.permissions)
		bastTable[(newGAST.domain, newGAST.key)] = bastTable[(self.domain, self.key)]

		return newGAST

	def free(self):
		del bastTable[(self.domain, self.key)]


class BAST:
	def __init__(self):
		# probably do not pass this "value", increment number (bast counter)
		# when free, put freed in the bastavailable list
		# when creating a new bast, take oldest bastavail list

		global bastCnt

		if not bastAvail:
			if(self.checkFileExists(bastCnt)):
				self.value = bastCnt
				bastCnt += 1
			else:
				pass # TODO: What to do when file does not exist??
		else:
			oldest = bastAvail.pop(0)
			if(self.checkFileExists(oldest)):
				self.value = oldest

	
	def checkFileExists(self, count):
		return os.path.exists("./b/"+str(hex(count)))

# TODO: FIGURE OUT WHAT IS BEING WRITTEN HERE, AS IT MOST LIKELY ISN'T THE DSAST ITSELF
# 		MAYBE IT'S THE DSAS, BUT IDK IF WE GET THAT IN THE MN OR IF WE NEED TO FETCH IT
	def writeToFile(self, DSAST, offset):
		with open("./b/"+str(hex(self.value)), 'w') as file:
			file.seek(offset)
			file.write(DSAST)

	def readFromFile(self, offset):
		with open("./b/"+str(hex(self.value)), 'r') as file:
			file.seek(offset)
			return file.read()


class OIT:
	def __init__(self, permissions):
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
	# Structure(MSB to LSB): Way Limit, Size, Line Limit, Index, Offset, prob useless for python simulations but w/e
	def __init__(self, index, lineLimit, size, wayLimit):
		# Size: 0 = Large DSAST, 1 = Small DSAST
		# Offset: 40 bits for small, 50 bit for large
		# Index: (mb kinda the file name) indexing in a list of DSASTs
		# Line limit: The least significant set-bit of the this field determines the partition size and the remaining upper bits of the field determine to which of the possible ranges, of the indicated size, the DSAST is restricted. If field bit 64 is set, then the
		# remaining 4 bits (68:65) index a 1/16th size partition. If field bit 64 is clear and bit 65 is set, then bits 68:66 indicate the
		# location of an even index aligned partition pair (partitions 0:1, 2:3, 4:5 ,,, or 14:15). If field bits 64 and 65 are both clear
		# and bit 66 is set, then bits 68:67 indicate the location of a partition quad (partitions 0:3, 4:7, 8:11 or 12:15). If field bits
		# 64 through 66 are all clear and bit 67 is set, then bit 68 indicates that associated data object is restricted to either the first
		# half (partitions 1:7) or the last half (partitions 8:15) of the of a cache. A field value of 16 indicates that the associated
		# data object enjoys unrestricted cache placement. The field value 0 is reserved.
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
def mapBASTtoDSAST(DSAST, GAST):
	# Check if GAST is mapped to a BAST
	if ((GAST.domain, GAST.key) in bastTable.keys()):
		aBast = bastTable[(GAST.domain, GAST.key)]
	else:
		aBast = BAST()

	# Check if BAST is mapped to a DSAST
	for dsast, bast in sastBast.items():
		if(bast == aBast): # already mapped
			return dsast

	# Did not find a matching DSAST for the BAST
	sastBast[DSAST] = aBast
	return DSAST

# Write cache line to DSAST's BAST
def writeToBAST(dsast):
	try:
		abast = sastBast[dsast]
		abast.writeToFile(DSAST=dsast, offset=DSAST.offset)
		return
	except:
		print("Could not write to DSAST's BAST\n")

# class OAT:
#	def __init__(self, OIT):
#		self.key = random.getrandbits(256)
#		self.value = self.checksum(OIT)
# 		#TODO: create entry in OAT Table, index is OIT, value is self
		# the manual says we index by the OIT value, but wth is this value...
		# just using the OIT itself for the time being
#		oatTable[OIT] = self
		#TODO: encrypt data and assign self.key to be the key of the encryption 

#	def checksum(self, OIT): 
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
	
	abast = BAST()
	abast.writeToFile("This is a test")
	print(abast.readFromFile())


	# aOIT = OIT()

	# aGAST = GAST(1,1234)
	# bGAST = GAST(0,4321)
	# print(gastTable)
	# print(oitTable)
	#print(oatTable)
	# print(bastTable)
	
	# aOIT = OIT()
	# aOAT = OAT(aOIT)
	# print(type(aOIT.key[0]))
	#print("Domain: {}\nValue: {}\nKey: {}\n".format(aOIT.domain, aOIT.value, aOIT.key))
	#print("Key: {}\nValue: {}".format(aOAT.key, aOAT.value))