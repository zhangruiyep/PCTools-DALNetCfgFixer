import os
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.ttk as ttk
import types
import serial.tools.list_ports
import threading
import time

import csvop
import cfg
from filesData import *
from mcuDevice import *

class Application(ttk.Frame):
	def __init__(self, master=None):
		ttk.Frame.__init__(self, master)
		self.cfg = cfg.configFile()
		self.columnconfigure(0, weight=1)
		self.rowconfigure(1, weight=1)
		self.grid(sticky=tk.NSEW)
		self.createWidgets()
		self.dev = None

	def createWidgets(self):
		serial_frame = ttk.Frame(self)
		serial_frame.grid(row = 0, sticky=tk.NSEW, pady = 3)

		self.Info = ttk.Label(serial_frame, text="COM :", justify=tk.LEFT)
		self.Info.grid(row=0, sticky=tk.W, padx=10)

		optionList = ["", ]
		for port in serial.tools.list_ports.comports():
			#print(port.description)
			optionList.append(port.description)
		
		self.v = tk.StringVar()
		if len(optionList) > 1:
			self.v.set(optionList[1])

		#self.serialPortOpt = ttk.OptionMenu(serial_frame, self.v, *optionList, command=self.onPortChange)
		self.serialPortOpt = ttk.OptionMenu(serial_frame, self.v, *optionList)
		self.serialPortOpt.grid(row = 0, column=1, sticky=tk.W, padx=10)

		opFrame = ttk.Frame(self)
		opFrame.grid(row = 1, sticky = tk.NSEW, pady = 3)

		self.opDevice = ttk.Label(opFrame, text="Device :", justify=tk.LEFT)
		self.opDevice.grid(row = 0, sticky=tk.E, padx=10)

		self.stDevice = ttk.Label(opFrame, text="", justify=tk.LEFT)
		self.stDevice.grid(row = 0, column = 1, sticky=tk.W, padx=10)

		self.opThingsName = ttk.Label(opFrame, text="Things Name :", justify=tk.LEFT)
		self.opThingsName.grid(row = 1, sticky=tk.E, padx=10)

		self.stThingsName = ttk.Label(opFrame, text="", justify=tk.LEFT)
		self.stThingsName.grid(row = 1, column = 1, sticky=tk.W, padx=10)

		self.opUrl = ttk.Label(opFrame, text="MQTT URL :", justify=tk.LEFT)
		self.opUrl.grid(row = 2, sticky=tk.E, padx=10)

		self.stUrl = ttk.Label(opFrame, text="", justify=tk.LEFT)
		self.stUrl.grid(row = 2, column = 1, sticky=tk.W, padx=10)

		self.opCert = ttk.Label(opFrame, text="Cert :", justify=tk.LEFT)
		self.opCert.grid(row = 3, sticky=tk.E, padx=10)

		self.stCert = ttk.Label(opFrame, text="", justify=tk.LEFT)
		self.stCert.grid(row = 3, column = 1, sticky=tk.W, padx=10)
		
		actFrame = ttk.Frame(self)
		actFrame.grid(row = 2, sticky = tk.NSEW, pady = 3)

		self.startBtn = ttk.Button(actFrame, text="Start", command=self.startRepair)
		self.startBtn.grid(padx=10, row = 0, column = 0)
		
		progressFrame = ttk.Frame(self)
		progressFrame.grid(row = 3, sticky=tk.NSEW, pady=3)

		self.pbar = ttk.Progressbar(progressFrame, orient ="horizontal", length = 600, mode ="determinate")
		#self.pbar.grid(padx=10, sticky=tk.NSEW)
		self.pbar["maximum"] = 100

		#self.saveCfgFileBtn = ttk.Button(actionFrame, text="Save Configuration", command=self.saveCfgFile)
		#self.saveCfgFileBtn.grid(padx=10, row = 0, column = 1)
		
		helpFrame = ttk.Frame(self)
		helpFrame.grid(row = 4, sticky=tk.NSEW, pady = 3)

		self.helpInfo = ttk.Label(helpFrame, text="Steps:\n1. Select COM port.\n2. Connect device to white-box.\n3. Power on and wait device bootup.\n4. Click \"Start\" button.", justify=tk.LEFT)
		self.helpInfo.grid(row = 0, sticky=tk.E, padx=10)

	def saveCfgFile(self):
		try:
			self.cfg.cp.add_section("OutFile")
		except:
			print("section exist")
		outFileName = self.serialCOMEntry.get().strip()
		self.cfg.cp['OutFile']['Name'] = outFileName
		self.cfg.cp['OutFile']['Size'] = self.v.get()
		self.cfg.write()

		self.tv.update_filesdata()
		self.tv.filesdata.write()

		return

	def updateProgress(self, value):
		self.pbar["value"] = int(value * self.pbar["maximum"])
		self.update_idletasks()

	#def onPortChange(self, value):
	def startRepair(self):
		value = self.v.get()
		comNum = None
		for port in serial.tools.list_ports.comports():
			if (port.description == value):
				comNum = port.device
				break
		
		if comNum == None:
			tkinter.messagebox.showerror("Error", "Device COM not set")
			return

		self.thread = threading.Thread(target=self.repairThread, name="Thread-repair", args=(comNum,), daemon=True)
		self.thread.start()

	def getThingsName(self):
		ret = self.dev.runCmd(b"AT+THINGSNAME?\r\n", "THINGSNAME")
		# test rsp data
		#ret.msg = "THINGSNAME=391202006300010AA\r\nATXXX"
		atRsp = ret.msg.split() #remove \r\n
		#print(atRsp)
		atParas = atRsp[0].split('=')
		#print(atParas)
		if (atParas[1][:3] == "391"):
			correctNameLen = 15
		elif (atParas[1][:4] == "3413"):
			correctNameLen = 16
		else:
			correctNameLen = 16
		#print("correctNameLen=%d" % correctNameLen)
		# read another line
		line = self.dev.ser.readline().decode("utf-8")
		if len(line) == 0 and len(atRsp) == 1 and len(atParas[1]) == correctNameLen:
			nameIsCorrect = True
		else:
			nameIsCorrect = False
		
		#print(atParas[1][:correctNameLen])
		#print(nameIsCorrect)
		#print(ret)
		return atParas[1][:correctNameLen],nameIsCorrect,ret

	def getMQTT(self):
		ret = self.dev.runCmd(b"AT+MQTT?\r\n", "MQTT")
		atRsp = ret.msg.split() #remove \r\n
		atParas = atRsp[0].split('=')
		#print(atParas)
		return atParas[1],ret
	
	def repairThread(self, comNum):
		# init status
		self.stDevice["text"] = "Waiting"
		self.stThingsName["text"] = ""
		self.stUrl["text"] = ""
		self.startBtn['state'] = "disabled"
		self.updateProgress(0.0)
		
		# open serial
		self.dev = mcuDevice(comNum, 0)
		ret = self.dev.open()
		if (ret.result != "OK"):
			tkinter.messagebox.showerror(ret.result, ret.msg)
			self.startBtn['state'] = "normal"
			return
		
		# wait device boot up
		time.sleep(6)
		self.updateProgress(0.2)
		
		# clean boot log
		#self.dev.cleanRxBuff()
		
		# pv mode
		self.stDevice["text"] = "Waiting"
		ret = self.dev.connect()
		retry = 0
		while ((ret.result != "OK") and (retry < 1000)):	
			self.stDevice["text"] = "Waiting"
			time.sleep(1)
			ret = self.dev.connect()
			retry += 1
			if (retry >= 1000):
				self.stDevice["text"] = "Timeout"
				tkinter.messagebox.showerror(ret.result, ret.msg)
				self.dev.close()
				self.startBtn['state'] = "normal"
				return
		'''
		# close log
		self.stDevice["text"] = "Waiting"
		ret = self.dev.connect()
		'''
		
		# check version
		ret = self.dev.runCmd(b"AT+MCUVER?\r\n", "+ACK:")
		if not "JETS_E1A1_GA01" in ret.msg:
			tkinter.messagebox.showerror("ERROR", "Can not get device version JETS_E1A1_GA01.")
			self.dev.close()
			self.startBtn['state'] = "normal"
			return
		
		# ready
		self.stDevice["text"] = "Ready"
		
		# things name				
		self.stThingsName["text"] = "Checking"
		name,isCorrect,ret = self.getThingsName()
		#if len(atCmds) > 1:
		if not isCorrect:
			print("get error data")
			self.stThingsName["text"] = "Repairing"
			ret = self.dev.runCmd(b"AT+THINGSNAME=" + bytes(name, "utf-8") + b"\r\n", "OK")
			if (ret.result != "OK"):
				tkinter.messagebox.showerror(ret.result, ret.msg)
				self.dev.close()
				self.startBtn['state'] = "normal"
				return
			
			self.stThingsName["text"] = "Verifing"
			name,isCorrect,ret = self.getThingsName()
			if not isCorrect:
				tkinter.messagebox.showerror(ret.result, ret.msg)
				print("Repair fail")
				self.dev.close()
				self.startBtn['state'] = "normal"
				return
					
			self.stThingsName["text"] = "Repaired"
			self.updateProgress(0.5)
		else:
			self.stThingsName["text"] = "Pass"
			self.updateProgress(0.5)
		
		
		# MQTT
		self.stUrl["text"] = "Checking"
		correctUrl = "a17ra1c9bg88c2-ats.iot.eu-central-1.amazonaws.com,8883"
		url,ret = self.getMQTT()

		if url != correctUrl:
			self.stUrl["text"] = "Repairing"
			ret = self.dev.runCmd(b"AT+MQTT=" + bytes(correctUrl, "utf-8") + b"\r\n", "OK")
			if (ret.result != "OK"):
				tkinter.messagebox.showerror(ret.result, ret.msg)
				self.dev.close()
				self.startBtn['state'] = "normal"
				return
			
			self.stUrl["text"] = "Verifing"
			url,ret = self.getMQTT()
			if url != correctUrl:
				tkinter.messagebox.showerror(ret.result, ret.msg)
				print("Repair fail")
				self.dev.close()
				self.startBtn['state'] = "normal"
				return
					
			self.stUrl["text"] = "Repaired"
			self.updateProgress(0.7)
		else:
			self.stUrl["text"] = "Pass"
			self.updateProgress(0.7)

		# CERT
		self.stCert["text"] = "Deleting"
		ret = self.dev.runCmd(b"AT+ZFILEDEL=mq_rootCA.crt\r\n", "OK")
		
		if (ret.msg == "Can not get ACK from device"):
			retry = 0
			while retry < 5 and ret.msg == "Can not get ACK from device":
				time.sleep(5)
				ret = self.dev.runCmd(b"AT+ZFILEDEL=mq_rootCA.crt\r\n", "OK")
				retry += 1
			
			if retry >= 5:
				self.stCert["text"] = "Fail"
				self.updateProgress(1.0)
			else:
				self.stCert["text"] = "Pass"
				self.updateProgress(1.0)
				
		else:
			self.stCert["text"] = "Pass"
			self.updateProgress(1.0)
		
		tkinter.messagebox.showinfo("Done", "Complete!\r\nPlease power off and disconnect device.\r\nThen repeat step 2~4.")
		self.dev.close()
		self.startBtn['state'] = "normal"
		return


app = Application()
app.master.title('DAL601 Net Repair Tool V1.9')
app.master.rowconfigure(0, weight=1)
app.master.columnconfigure(0, weight=1)
app.mainloop()
