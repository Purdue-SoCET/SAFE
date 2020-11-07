#CAS contains NPAST_to_NSAST entries that can be indexed using the NPAST tags
#Each NPAST_to_NSAST entry has an NSAST value that is the network system AST
#Table 18 to 27


class NSR:
	def __init__(self, SNE_index = 0, socket_index = 0):
		self.SNE_index = SNE_index
		self.socket_index = socket_index

class NPR:
	def __init__(self, SNE_index, socket_index, offset):
		self.SNE_index = SNE_index
		self.socket_index = socket_index
		self.offset = offset
		self.NPAST = (self.SNE_index, self.socket_index)
	def translate_to_NSR(self, CAS):
		nsr_out = NSR()
		NSAST_out = CAS.NPAST_to_NSAST[self.NPAST]
		nsr_out.SNE_index = NSAST_out.system_SNE_index
		nsr_out.socket_index = NSAST_out.socket_index
		return nsr_out
