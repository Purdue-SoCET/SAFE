import random
import math
from scipy.stats import norm, expon
import numpy as np
import matplotlib.pyplot as plt
import simpy
import threading
import time
from time import sleep
class Process:
  domain = 0
  process_id = -1
  state = "READY"
  readyTime = 0
  runningTime = 0
  blockedTime = 0
  executionTime = 0

  # def __init__(self):
  #   pass

  def __init__(self, process_id, domain):
    self.process_id = process_id
    self.domain = domain

  def setState(self, state):
    self.state = state

  def setRunningTime(self, time):
    self.runningTime = time

  def setReadyTime(self, time):
    self.readyTime = time

  def setBlockedTime(self, time):
    self.blockedTime = time

  def setExecutionTime(self, time):
    self.executionTime = time
  
  def getReadyTime(self):
    return self.readyTime
  def getProcessID(self):
    return self.process_id
  def getExecutionTime(self):
    return self.executionTime
