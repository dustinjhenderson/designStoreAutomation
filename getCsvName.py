#get csv file name
#Dustin Henderson

import os
import csv

def getNameCsv(fileLocation, userMessege, tag):
	enteredName = ""
	goodMessege = "Good File"
	badMessege = "Bad File"
	goodFile = False
	print userMessege
	enteredName = raw_input(tag)
	try:
		with open(fileLocation + enteredName, 'rb') as csvfile:
			goodFile = True
			enteredName = enteredName + fileLocation
			print(goodMessege)
	except:
		try:
			with open(enteredName, 'rb') as csvfile:
				print(goodMessege)
				goodFile = True
		except:
			print badMessege
	while(goodFile == False):
		enteredName = raw_input(tag)
		try:
			with open(fileLocation + enteredName, 'rb') as csvfile:
				goodFile = True
				enteredName = enteredName + fileLocation
				print goodMessege
		except:
			try:
				with open(enteredName, 'rb') as csvfile:
					print(goodMessege)
					goodFile = True
			except:
				print badMessege
	return enteredName
	
''' Test call '''
#getNameCsv("C:\Users\dustinhe\Documents\python\DesignStoreScript", "testing the name input", "testFile: ")