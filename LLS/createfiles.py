import sys
import os

#############################################################
# Usage: python createfiles <number of files>
# creates the specified number of files in the ./b/ directory
# the file names are in hex
#############################################################

def createFiles(n):
	# n is the number of files to be created
	# check if ./b/ directory exists
	if not os.path.isdir("./b"):
			os.mkdir("./b")
	# create files
	for i in range(0, n):
			with open('b/'+str(hex(i)), 'w') as file: 
				file.close()


def main():
	if(len(sys.argv) != 2):
		# check if number fo files to create argument exists
		print("Usage: python createfiles <number of files>")
	else:
		createFiles(int(sys.argv[1]))
		

if __name__ == "__main__":
	main()
