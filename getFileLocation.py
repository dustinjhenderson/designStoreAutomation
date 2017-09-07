#Get file location
#Dustin Henderson

import os

def getFileLocation(userMessege, tag):
	enteredLoc = ""
	goodPath = False
	print userMessege
	enteredLoc = raw_input(tag)
	if os.path.exists(enteredLoc):
		goodPath = True
	while(goodPath == False):
		if not os.path.exists(enteredLoc):
			print "Error! Please try again"
		else:
			goodPath = True
		enteredLoc = raw_input(tag)
	print "Good Path"
	return enteredLoc
		
'''Test call'''
#getFileLocation("Please enter file location for the videos to be saved in\nsaved in (Example: C:\Users\dustinhe\Videos\e3e\)", "Location: ")