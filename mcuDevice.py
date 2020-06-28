import serial
import time

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

	def findAckInLine(self, ack):
		try:
			line = self.ser.readline().decode("utf-8")
			#line = b"\r\nOK\r\n".decode("utf-8")
			#line = b"THINGSNAME=8864202001140013\r\n".decode("utf-8")
			#line = b"THINGSNAME=8864202001140013\r\nAT+ZGETICCID?\r\n".decode("utf-8")
			#line = b"MQTT=ag2xadrg7ayfr-ats.iot.ap-southeast-1.amazonaws.cooom".decode("utf-8")
		except:
			print("Serial data INVALID. Please check device serial.")
			getACK = False
			line = ""
		else:
			getACK = ack in line
		
		return getACK,line

	def runCmd(self, cmd, ackString):
		cmdRetry = 0
		ret = None
		
		while(cmdRetry <= self.retryCount):
			if (cmdRetry != 0):
				print("Retry: %d" % cmdRetry)
				
			# send AT
			print("sending",cmd)
			self.ser.write(cmd)
		
			# get rsp, check ack
			getACK,line = self.findAckInLine(ackString)
			#print("get line",getACK,line)
			
			# try again to get rsp
			rspRetry = 0
			while (not getACK) and (rspRetry <= self.retryCount):
				getACK,line = self.findAckInLine(ackString)
				rspRetry += 1
			
			# can not get ack, try to send AT again
			if (not getACK) and (rspRetry > self.retryCount):
				ret = mcuDeviceRet("Warning", "Can not get ACK from device")
				print(ret.msg)
				cmdRetry += 1
				continue
				
			#print("Got",getACK,line)
			
			if "ERROR" in line:
				ret = mcuDeviceRet("ERROR", line)
				print(ret.msg)
				cmdRetry += 1
				continue
			
			if (getACK):
				ret = mcuDeviceRet("OK", line)
				print("return",ret.msg)
				return ret
					
		return ret
	
	def connect(self):
		ret = self.runCmd(b"AT+PVMODE=1\r\n", "OK")
		time.sleep(1)
		self.cleanRxBuff()
		return self.runCmd(b"AT+PVMODE=1\r\n", "OK")
		
	def cleanRxBuff(self):
		try:
			line = self.ser.readline().decode("utf-8")
		except:
			print("Serial data INVALID. Discard.")
			line = "1" #just some data, do not care content

		while(len(line) > 0):
			try:
				line = self.ser.readline().decode("utf-8")
			except:
				print("Serial data INVALID. Discard.")
				line = "1" #just some data, do not care content

		return
        
