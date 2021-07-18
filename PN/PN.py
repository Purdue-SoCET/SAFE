import ctypes
import sys

sys.path.append("../")
from PMU.PMU import Proc, createDPAST
from LLS.LLS import bastTable

fp = "Simulator/sim.so"
simulator = ctypes.CDLL(fp)

def run(gast):
    global simulator
    # send GAST to PMU
    # proc = createDPAST(gast)
    # receive DPAST back and run it
    bast = bastTable[(gast.domain, gast.key)]
    simulator.main("../../LLS/b/" + bast.getfname())

    # which type of address space goes into PN
    # why does the PN need a DPSAT