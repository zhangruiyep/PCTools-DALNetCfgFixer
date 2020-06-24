import csv

def readDataFile(filename):
	filesdata = []
	try:
		f = open(filename, newline='', encoding='utf-8')
	except:
		print(filename + " can not open")
		return filesdata
	
	rdr = csv.reader(f)
	for row in rdr:
		filesdata.append([row[0], int(row[1],16)])
	f.close()
	return filesdata

def writeDataFile(filesdata, filename):
	print("saving %s" % filename)
	with open(filename, 'w', newline='', encoding='utf-8') as f:
		wtr = csv.writer(f)
		for r in filesdata:
			row = []
			row.append(''.join(r[0]))
			row.append('0x%X' % r[1])
			wtr.writerow(row)
		f.close()
	