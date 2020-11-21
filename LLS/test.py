import LLS
# TB for LLS
# Scenario based testing model. Create objects, write to them, open, close, read, write, etc...
# Make sure we can create objs and put data into them. Use 4 byte cache model for testing.
# After basic testing is implemented, randomize accesses. Add a list to keep track of BAS sizes.
# Test for invalid inputs (size is off etc.) to ensure it sends back msg to PMU/CH.
# Test case for gain a msg to retire bast

# FNS TO TEST
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
def main():



if __name__ == "__main__":
	main()
