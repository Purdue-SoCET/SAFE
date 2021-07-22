from LLS import *
# TB for LLS
# Scenario based testing model. Create objects, write to them, open, close, read, write, etc...
# Make sure we can create objs and put data into them. Use 4 byte cache model for testing.
# After basic testing is implemented, randomize accesses. Add a list to keep track of BAS sizes.
# Test for invalid inputs (size is off etc.) to ensure it sends back msg to PMU/CH.
# Test case for gain a msg to retire bast

# FNS LIST TO TEST
# mapBASTtoDSAST(dsast, gast)
# gastRequest(dsast)
# writeToBAST(dsast)		#
# openFile(dsast, gast)		#
# createFile(dsast)
# closeFile(dsast)			#
# saveFile(dsast, permissions)#
# deleteFile(gast)
# getBASTfromDSAST(dsast)
# invalidateDSAST(dsast)	#
# writeThrough(dsast, packet)#
# sendMsgRetire()							# dummy implementation
# rcvOkToUnmap()							# dummy implementation

# GAST.duplicate()
# GAST.free()

# BAST init when there is something in bastAvail list
# BAST.writeToFile()
# BAST.readFromFile()
# BAST.close()



dsastList = []	# Lists of created DSASTS, mimmic PMU's knowledge of dsasts/gasts
gastList = []	# Lists of created GASTS

def testFunc(func, funcname):
	if(func==1):
		print("{} success".format(funcname))
	else:
		print("{} failed: {}".format(funcname, retval))

# Question: How to test saveFile?

def testCreateFile():
	global sastBast
	# create dsast to bast mapping
	adsast = DSAST()
	dsastList.append(adsast)
	agast = GAST()
	gastList.append(agast)
	mapBASTtoDSAST(adsast, agast)
	abast = bastTable[(agast.domain, agast.key)]
	if not (sastBast[adsast] == abast):
		return "Did not map DSAST to BAST from GAST reference"

	fp = abast.open()
	string = "A"*50
	fp.write(string)
	
	# call create file to check if new bast is associated to given dsast
	createFile(adsast)
	if not (sastBast[adsast] != abast):
		return "BASTS are the same after creating file"

	# check if second fp is valid
	abast2 = getBASTfromDSAST(adsast)
	fp2 = abast2.open()
	string = "B"*50
	fp2.write(string)
	if not (fp.name != fp2.name):
		return "BAST file is the same after creating file"
	
	return 1

def testDeleteFile():
	global sastBast
	if len(dsastList):
		abast = getBASTfromDSAST(dsastList[0])
		agast = gastList[0]
	else:
		adsast = DSAST()
		dsastList.append(adsast)
		agast = GAST()
		gastList.append(agast)
		mapBASTtoDSAST(adsast, agast)
		abast = bastTable[(agast.domain, agast.key)]
	
	deleteFile(agast)
	if (agast.domain, agast.key) in bastTable.keys():
		print("deleteFile failed to unmap GAST to BAST")
		return 0
	
	# should the physical file referenced by the bast be deleted from the system as well?
	# it is still innaccessible without an existing bast referencing it, so the next time 
	# something is written to that file it should just be overwritten, I assume, 
	# but need to confirm this

	return 1

def testReadWriteToFile():
	global dsastList
	global gastList

	adsast = DSAST()
	dsastList.append(adsast)
	agast = GAST()
	gastList.append(agast)
	
	# link dsast to a bast to be written
	mapBASTtoDSAST(adsast, agast)
	adsast.offset = 0
	writeToBAST(adsast)
	abast = getBASTfromDSAST(adsast)
	if not abast.readFromFile(0):
		print("Nothing read from written bast")
		return 0

	return 1

def testInvalidate():
	if len(dsastList):
		adsast = dsastList.pop()
		invalidateDSAST(adsast)
		global sastBast
		try:
			if(sastBast[adsast]):
				print(" Did not unmap DSAST to BAST")
				return 0	
		except:
			return 1


def main():

	testFunc(testCreateFile(), "testCreateFile()")
	testFunc(testDeleteFile(), "testDeleteFile()")
	testFunc(testReadWriteToFile(), "testReadWriteToFile()")
	testFunc(testInvalidate(), "testInvalidate()")

if __name__ == "__main__":
	main()
