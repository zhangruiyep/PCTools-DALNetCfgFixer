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
from dload import *

class AddFrame(ttk.Frame):
	def __init__(self, master=None, parentIdx=""):
		ttk.Frame.__init__(self, master)
		self.grid()
		self.tv = master
		self.parentIdx = parentIdx
		self.createWidgets()
		self.files = ()

	def createWidgets(self):
		dataframe = ttk.Frame(self)
		dataframe.grid(row = 0, pady=3)

		label = ttk.Label(dataframe, text="File:", justify=tk.LEFT)
		label.grid(row=0, sticky=tk.E, padx=6, pady=3)

		self.fileEntry = ttk.Entry(dataframe)
		self.fileEntry.delete(0, tk.END)
		self.fileEntry.grid(row=0, column=1, padx=6, pady=3)

		self.getFileBtn = ttk.Button(dataframe, text="Choose", command=self.chooseFile, width=10)
		self.getFileBtn.grid(row=0, column=2, padx=6, pady=3)

		btnframe = ttk.Frame(self)
		btnframe.grid(row = 1, pady=3)

		OKBtn = ttk.Button(btnframe, text="OK", command=self.addRecord)
		OKBtn.grid(row=0, padx=6)
		CancelBtn = ttk.Button(btnframe, text="Cancel", command=self.cancelAdd)
		CancelBtn.grid(row=0, column=1, padx=6)

	def addRecord(self):
		filenames = self.files
		count = len(filenames)
		for i in range(0, count):
			filename = filenames[i]
			#print(filename)
			if not os.path.exists(filename):
				tkinter.messagebox.showwarning("Warning", "%s File not found" % filename)
				return

			self.tv.update_filesdata()

			if not idxValid(filename):
				self.destroy()
				return

			if self.tv.filesdata.isExist(filename):
				tkinter.messagebox.showerror("Error", "File %s index exist already!" % filename)
				self.destroy()
				return

			self.tv.insert(self.parentIdx, "end", values=(filename,"READY",))

		self.tv.update_filesdata()

		self.destroy()

	def cancelAdd(self):
		self.destroy()

	def chooseFile(self):
		filenames = tkinter.filedialog.askopenfilenames()
		#print(filenames)
		self.files = filenames
		self.fileEntry.delete(0, tk.END)
		for filename in filenames:
			if (filenames != None) and (filenames != ""):
				self.fileEntry.insert(tk.END, os.path.realpath(filename) + ",")

def takeOffset(elem):
	return elem[FILEDATA_IDX]

class filesTreeview(ttk.Treeview):
	def __init__(self, master=None):
		ttk.Treeview.__init__(self, master)
		self['columns']=("filename", "dload_st")
		self.filesdata = filesData()
		self.grid(sticky=tk.NSEW)
		self.createWidgets()

	def createWidgets(self):
		self.column("#0", width=20, stretch=0)
		self.column("filename", width=500)
		self.column("dload_st", width=100)
		self.heading('filename', text='File Name')
		self.heading('dload_st', text='Status')

	def fill_treeview(self):
		for item in self.get_children():
			self.delete(item)

		for f in self.filesdata.data:
			self.insert('',"end",values=(f[FILEDATA_NAME],f[FILEDATA_STATUS]))

	def update_filesdata(self):
		self.filesdata.data = []
		for i in self.get_children():
			idx = getIdxByName(self.item(i)["values"][0])
			if idx != -1:
				#print(idx)
				#print(self.item(i)["values"])
				self.filesdata.data.append([self.item(i)["values"][0], idx, self.item(i)["values"][1]])
		self.filesdata.data.sort(key=takeOffset)
		self.fill_treeview()



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
		tv_frame = ttk.Frame(self)
		tv_frame.grid(row = 2, sticky=tk.NSEW, pady = 3)

		self.tv = filesTreeview(tv_frame)
		self.tv.grid(row = 0, sticky=tk.NSEW)
		self.tv.fill_treeview()

		self.sb = ttk.Scrollbar(tv_frame, orient=tk.VERTICAL, command=self.tv.yview)
		self.sb.grid(row = 0, column=1, sticky=tk.NS)

		self.tv.configure(yscrollcommand=self.sb.set)

		self.context_menu = tk.Menu(self.tv, tearoff=0)
		self.context_menu.add_command(label="Add", command=self.add_handler)
		self.context_menu.add_command(label="Delete", command=self.delete_handler)
		self.tv.bind('<3>', self.show_context_menu)
		self.entryPopup = ""
		self.record_frame = ""

		serial_frame = ttk.Frame(self)
		serial_frame.grid(row = 0, sticky=tk.NSEW, pady = 3)

		self.Info = ttk.Label(serial_frame, text="COM :", justify=tk.LEFT)
		self.Info.grid(row=0, sticky=tk.W, padx=10)

		#self.serialCOMEntry = ttk.Entry(serial_frame, width = 5)
		#self.serialCOMEntry.grid(row=0, column=1, padx=10)
		#if self.cfg:
		#	try:
		#		self.serialCOMEntry.delete(0, tk.END)
		#		self.serialCOMEntry.insert(0, self.cfg.cp['Serial']['COM1'])
		#	except:
		#		print("can not get file name from cfg")
		
		retryFrame = ttk.Frame(self)
		retryFrame.grid(row = 1, sticky=tk.NSEW, pady = 3)

		self.retryInfo = ttk.Label(retryFrame, text="Command retry times: ", justify=tk.LEFT)
		self.retryInfo.grid(row=0, column=0, sticky=tk.W, padx=10)

		self.retryEntry = ttk.Entry(retryFrame, width = 5)
		self.retryEntry.grid(row=0, column=1, padx=10)
		self.retryEntry.delete(0, tk.END)
		self.retryEntry.insert(tk.END, "1")

		#self.getFileBtn = ttk.Button(serial_frame, text="Choose", command=self.chooseOutputFile, width=10)
		#self.getFileBtn.grid(row=0, column=2, padx=10)

		#flashOptionFrame = ttk.Frame(self)
		#flashOptionFrame.grid(row = 1, sticky=tk.NSEW, pady=3)

		#self.flashSizeInfo = ttk.Label(flashOptionFrame, text="Flash size(MB):", justify=tk.LEFT)
		#self.flashSizeInfo.grid(row = 0, sticky=tk.W, padx=10)

		optionList = ["", ]
		for port in serial.tools.list_ports.comports():
			print(port.description)
			optionList.append(port.description)
		
		self.v = tk.StringVar()
		if len(optionList) > 1:
			self.v.set(optionList[1])
		#if self.cfg:
		#	try:
		#		self.v.set(self.cfg.cp['OutFile']['Size'])
		#	except:
		#		print("can not get file size from cfg")

		self.platformOpt = ttk.OptionMenu(serial_frame, self.v, *optionList)
		self.platformOpt.grid(row = 0, column=1, sticky=tk.W, padx=10)

		progressFrame = ttk.Frame(self)
		progressFrame.grid(row = 3, sticky=tk.NSEW, pady=3)

		self.pbar = ttk.Progressbar(progressFrame, orient ="horizontal", length = 600, mode ="determinate")
		self.pbar.grid(padx=10, sticky=tk.NSEW)
		self.pbar["maximum"] = 100

		actionFrame = ttk.Frame(self)
		actionFrame.grid(row = 4, sticky=tk.NSEW, pady=3)

		self.dloadBtn = ttk.Button(actionFrame, text="Download All", command=self.dloadAll)
		self.dloadBtn.grid(padx=10, row = 0, column = 0)

		self.dloadFailsBtn = ttk.Button(actionFrame, text="Download Fail Files", command=self.dloadFails)
		self.dloadFailsBtn.grid(padx=10, row = 0, column = 1)

		#self.saveCfgFileBtn = ttk.Button(actionFrame, text="Save Configuration", command=self.saveCfgFile)
		#self.saveCfgFileBtn.grid(padx=10, row = 0, column = 1)

	def show_context_menu(self, event):
		self.context_menu.post(event.x_root,event.y_root)
		self.event = event


	def delete_handler(self):
		# close previous popups
		if self.entryPopup:
			self.entryPopup.destroy()

		self.edit_row = self.tv.identify_row(self.event.y)

		self.tv.focus(self.edit_row)

		item = self.tv.focus()
		if item != '':
			self.tv.delete(item)


	def add_handler(self):
		if self.entryPopup:
			self.entryPopup.destroy()

		self.edit_row = self.tv.identify_row(self.event.y)
		self.edit_column = self.tv.identify_column(self.event.x)

		parent = self.tv.parent(self.edit_row)
		self.addDataFrame(parent)


	def addDataFrame(self, parentItem):
		#x,y,width,height = self.tv.bbox(parentItem)

		if self.record_frame:
			self.record_frame.destroy()

		self.record_frame = AddFrame(self.tv, parentItem)
		self.record_frame.place(x=0, y=20, anchor=tk.NW)

	def entryEntryDestroy(self, event):
		self.entryPopup.destroy()

	def dloadAllMode(self, mode):
		option = self.v.get()
		comNum = None
		for port in serial.tools.list_ports.comports():
			if (port.description == option):
				comNum = port.device
				break		
		
		if comNum == None:
			tkinter.messagebox.showerror("Error", "Device COM not set")
			return

		try:
			retry = int(self.retryEntry.get().strip())
		except:
			tkinter.messagebox.showwarning("Warning", "Retry times invalid")
			return

		self.thread = threading.Thread(target=self.dloadThread, name="Thread-dload", args=(comNum, retry, mode), daemon=True)
		self.thread.start()
		#while(self.thread.is_alive()):
		#	self.update_idletasks()
		#	time.sleep(1)

		#tkinter.messagebox.showinfo("Info", "Download Complete.")
	def dloadAll(self):
		self.dloadAllMode("ALL")

	def dloadFails(self):
		self.dloadAllMode("FAIL_RETRY")

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



app = Application()
app.master.title('Flash File Download')
app.master.rowconfigure(0, weight=1)
app.master.columnconfigure(0, weight=1)
app.mainloop()