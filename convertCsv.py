#Download CSV
#Dustin Henderson

import csv
import openpyxl

def convertCsv(source, output):
	try:
		wb = openpyxl.Workbook()
		ws = wb.active
		f = open(source)
		reader = csv.reader(f, delimiter=',')
		for row in reader:
			ws.append(row)
		f.close()
		wb.save(output)
		return True
	except:
		print "Convert Error!"
		print "Try checking..." #change this later to error messege
		return False

'''Test Decloration'''
#convertCsv('testFile.csv', 'vert.xlsx')