import serial
from PyCRC.CRCCCITT import CRCCCITT

class mcuDeviceRet():
	def __init__(self, result, msg):
		self.result = result
		self.msg = msg

class mcuDevice():
	def __init__(self, comNum, retry):
		self.comNum = comNum
		self.ser = None
		self.retryCount = retry
		
	def open(self):
		try:
			self.ser = serial.Serial(self.comNum, 115200, timeout=1)
		except:
			ret = mcuDeviceRet("ERROR", "%s can not open." % self.comNum)
			return ret
		
		ret = mcuDeviceRet("OK", "Open done.")
		return ret
		
	def close(self):
		self.ser.close()
		
		ret = mcuDeviceRet("OK", "Close done.")
		return ret

	def runCmd(self, cmd):
		cmdRetry = 0
		ret = None
		
		while(cmdRetry <= self.retryCount):
			if (cmdRetry != 0):
				print("Retry: %d" % cmdRetry)
				
			self.ser.write(cmd)
			
			try:
				line = self.ser.readline().decode("utf-8")
			except:
				print("Serial data INVALID. Please check device serial.")
				getACK = False
			else:
				getACK = "+ACK:" in line
				
			rspRetry = 0
			while (not getACK) and (rspRetry <= self.retryCount):
				try:
					line = self.ser.readline().decode("utf-8")
				except:
					print("Serial data INVALID. Please check device serial.")
					getACK = False
				else:
					getACK = "+ACK:" in line
				rspRetry += 1
			
			if (not getACK) and (rspRetry > self.retryCount):
				ret = mcuDeviceRet("Warning", "Can not get +ACK from device")
				print(ret.msg)
				cmdRetry += 1
				continue
				
			print(line)
			if "ERROR" in line:
				ret = mcuDeviceRet("ERROR", line)
				print(ret.msg)
				cmdRetry += 1
				continue
	
			ret = mcuDeviceRet("OK", "runCmd done.")
			return ret
					
		return ret
