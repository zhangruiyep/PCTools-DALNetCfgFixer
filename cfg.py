import os
import sys
import configparser

class configFile():
	def __init__(self, filename="cfg.ini"):
		self.cp = configparser.ConfigParser()
		self.cp.read(os.path.join(os.path.abspath(''),filename), encoding='utf-8')
	
	def write(self, filename="cfg.ini"):
		realFileName = os.path.join(os.path.abspath(''),filename)
		writeFile = open(realFileName, 'w', encoding='utf-8')
		self.cp.write(writeFile)
		writeFile.close()

