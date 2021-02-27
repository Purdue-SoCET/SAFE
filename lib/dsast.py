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