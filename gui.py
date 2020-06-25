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
			print(port.description)
			optionList.append(port.description)
		
		self.v = tk.StringVar()
		#if len(optionList) > 1:
		#	self.v.set(optionList[1])

		self.serialPortOpt = ttk.OptionMenu(serial_frame, self.v, *optionList, command=self.onPortChange)
		self.serialPortOpt.grid(row = 0, column=1, sticky=tk.W, padx=10)

		opFrame = ttk.Frame(self)
		opFrame.grid(row = 1, sticky = tk.NSEW, pady = 3)

		self.opDevice = ttk.Label(opFrame, text="Device :", justify=tk.LEFT)
		self.opDevice.grid(row = 0, sticky=tk.E, padx=10)

		self.opThingsName = ttk.Label(opFrame, text="Things Name :", justify=tk.LEFT)
		self.opThingsName.grid(row = 1, sticky=tk.E, padx=10)

		self.opUrl = ttk.Label(opFrame, text="MQTT URL :", justify=tk.LEFT)
		self.opUrl.grid(row = 2, sticky=tk.E, padx=10)

		progressFrame = ttk.Frame(self)
		progressFrame.grid(row = 3, sticky=tk.NSEW, pady=3)

		self.pbar = ttk.Progressbar(progressFrame, orient ="horizontal", length = 600, mode ="determinate")
		self.pbar.grid(padx=10, sticky=tk.NSEW)
		self.pbar["maximum"] = 100

		#self.saveCfgFileBtn = ttk.Button(actionFrame, text="Save Configuration", command=self.saveCfgFile)
		#self.saveCfgFileBtn.grid(padx=10, row = 0, column = 1)

	def dloadThread(self, comNum, retry, mode):
		self.dloadBtn["state"] = "disabled"
		self.dloadFailsBtn["state"] = "disabled"
		self.dev = mcuDevice(comNum, retry)
		ret = self.dev.open()
		if (ret.result != "OK"):
			tkinter.messagebox.showerror(ret.result, ret.msg)
			self.dloadBtn["state"] = "normal"
			self.dloadFailsBtn["state"] = "normal"
			return
		
		# reset files state
		if (mode == "ALL"):
			for d in self.tv.filesdata.data:
				d[FILEDATA_STATUS] = "READY"
			self.tv.fill_treeview()
			
		dloadAllOK = True
		doneCount = 0
		
		for d in self.tv.filesdata.data:
			if (mode == "FAIL_RETRY") and (d[FILEDATA_STATUS] != "FAIL"):
				continue
			dlretry = 0
			dl = dload(self.dev, d[FILEDATA_NAME]);
			while (dl.dloadFile() == False):
				#self.dev.close()
				#tkinter.messagebox.showinfo("Info", "Download %s failed." % d[0])
				#self.dloadBtn["state"] = "normal"
				#return
				dlretry += 1
				if (dlretry > retry):
					break;
			if (dlretry > retry):
				d[FILEDATA_STATUS] = "FAIL"
				dloadAllOK = False
			else:
				d[FILEDATA_STATUS] = "DONE"
			self.tv.fill_treeview()
			doneCount += 1
			self.updateProgress(1.0 * doneCount / len(self.tv.filesdata.data))
		
		self.dev.close()
		if (dloadAllOK):
			tkinter.messagebox.showinfo("Info", "Download Complete.")
		else:
			tkinter.messagebox.showerror("Error", "Download Fail.")
			
		self.dloadBtn["state"] = "normal"
		self.dloadFailsBtn["state"] = "normal"



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

	def onPortChange(self, value):
		print("Port change to:" + value)


app = Application()
app.master.title('DAL601 Network Configuration Repair Tool')
app.master.rowconfigure(0, weight=1)
app.master.columnconfigure(0, weight=1)
app.mainloop()
