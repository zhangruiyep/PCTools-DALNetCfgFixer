import os
import types
import tkinter.messagebox

import csvop
import cfg

FILEDATA_NAME = 0
FILEDATA_IDX = 1
FILEDATA_STATUS = 2

def getIdxByName(filename):
	# get index by name
	basename = os.path.basename(filename)
	#print(basename)
	try:
		idx = int(basename[4:6])
	except:
		tkinter.messagebox.showerror("Invalid", "File Name Invalid: " + basename)
		return -1
	
	if not ((idx >= 1 and idx <= 13) or (idx == 18)):
		tkinter.messagebox.showerror("Invalid", "File Index Invalid: " + basename)
		return -1
	
	return idx

def idxValid(filename):
	idx = getIdxByName(filename)
	if idx < 0:
		return False
	return True

class filesData():
	def __init__(self, filename="data.csv"):
		self.filename = filename
		self.data = csvop.readDataFile(filename)
		

	def isExist(self, filename):
		idx = getIdxByName(filename)
		for f in self.data:
			if getIdxByName(f[FILEDATA_NAME]) == idx:
				return True
		return False
	
	
	def write(self):
		csvop.writeDataFile(self.data, self.filename)	
