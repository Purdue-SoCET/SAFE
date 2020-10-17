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

# create read that is a DSAST offset
# SAST to BAST Table

# Ref page 32 of manual.
# TODO: DSAST to BAST Mapping
# TODO: DPAST to DSAST Mapping

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

	def writeToFile(self, DSAST):
		with open("./b/"+str(hex(self.value)), 'w') as file:
			file.write(DSAST)

	def readFromFile(self):
		with open("./b/"+str(hex(self.value)), 'r') as file:
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