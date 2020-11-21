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
# getBASTfromDSAST(dsast, sastbast=sastBast)
# invalidateDSAST(dsast)
# writeThrough(dsast, packet)
# sendMsgRetire()							# dummy implementation
# rcvOkToUnmap()							# dummy implementation

def testFunc(func):
	if(func):
		print("Test {} success".format(func.__name__))
	else:
		print("Test {} failed".format(func.__name__))

def testCreatingFile():
	global sastBast
	# create dsast to bast mapping
	adsast = DSAST()
	agast = GAST()
	mapBASTtoDSAST(adsast, agast)
	abast = bastTable[(agast.domain, agast.key)]
	assert sastBast[adsast] == abast

	# call create file to check if new bast is associated to given dsast
	createFile(adsast)
	assert type(sastBast[adsast]) == BAST
	assert sastBast[adsast] != abast

	return 1


def main():

	testFunc(testCreatingFile)


if __name__ == "__main__":
	main()
