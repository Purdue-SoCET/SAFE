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
# writeToBAST(dsast)
# openFile(dsast, gast)
# createFile(dsast)
# closeFile(dsast)
# saveFile(dsast, permissions)
# deleteFile(gast)
# getBASTfromDSAST(dsast)
# invalidateDSAST(dsast)
# writeThrough(dsast, packet)
# sendMsgRetire()							# dummy implementation
# rcvOkToUnmap()							# dummy implementation

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

	# TODO: open file, write to it
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

def testDeletFile():
	global sastBast
	abast = getBASTfromDSAST(dsastList[0])

	pass


def main():

	testFunc(testCreateFile(), "testCreateFile()")


if __name__ == "__main__":
	main()
