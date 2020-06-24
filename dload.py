
from filesData import *
from mcuDevice import *

FLOW_DEBUG = False
#FLOW_DEBUG = True

class dload():
	def __init__(self, dev, filename):
		self.dev = dev
		self.filename = filename
		self.idxChar = self.getIdxChar()
	
	def getIdxChar(self):
		idx = getIdxByName(self.filename)
		if idx < 16:
			c = b'%x' % idx
		else:
			c = b'%c' % (ord('a') + idx - 10)
		return c

	def dloadRunCmd(self, cmd):
		ret = self.dev.runCmd(cmd)
		if (ret.result != "OK"):
			if FLOW_DEBUG:
				print(ret.msg)
			else:
				#tkinter.messagebox.showerror(ret.result, ret.msg)
				return False
		return True
		

	def dloadFile(self):
		cmd = b'AT+IAPSRT=%c\r\n' % self.idxChar
		print(cmd)
		ret = self.dloadRunCmd(cmd)
		if (ret == False):
			return False
	
		filename = os.path.realpath(self.filename)
		filesize = os.path.getsize(filename)
		#print(filesize)
	
		with open(filename, "rb") as f:
			content = f.read()
			#print(content)
	
			filecrc = CRCCCITT().calculate(content)
			#print(filecrc)
	
			f.close()
	
		cmd = b'AT+IAPSOH=%d,%d\r\n' % (filesize, filecrc)
		print(cmd)
		ret = self.dloadRunCmd(cmd)
		if (ret == False):
			return False
	
		i = 0
		idx = 0
		framesizeMax = 1024
		while i < filesize:
			# process bar
			#self.updateProgress(float(i)/filesize)
			# get real frame size
			if i + framesizeMax <= filesize:
				framesize = framesizeMax
			else:
				framesize = filesize - i
	
			# get frame data
			frame = b''
			for j in range(0,framesize):
				frame += bytes([content[i+j]])
	
			#print(frame)
	
			# calculate frame crc
			framecrc = CRCCCITT().calculate(frame)
	
			cmd = b'AT+IAPDWN=%d,%d,%d,%s\r\n' % (idx, framesize, framecrc, frame.hex().encode("utf-8"))
			#print(cmd)
			print("downloading %d, %d, %d" % (idx, framesize, framecrc))
			ret = self.dloadRunCmd(cmd)
			if (ret == False):
				return False
	
			# set index to next frame
			i += framesizeMax
			idx += 1
	
		cmd = b'AT+IAPEOT=1\r\n'
		print(cmd)
		ret = self.dloadRunCmd(cmd)
		if (ret == False):
			return False
	
		return True

