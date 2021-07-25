#!/usr/bin/python3
import os
import re
import sys
import filecmp
import time
def file2array(rfile):
	with open(rfile, 'r') as f:
		read_file = f.readlines()
	return read_file
if __name__ == "__main__":
	hexfile = file2array('meminit.hex')
        with open('0x0','w') as f:
		for line in hexfile:
			f.write(line[9:17] + '\n')
