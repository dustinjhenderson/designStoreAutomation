#Design Store Script
#Dustin Henderson

print "Starting Up..."	#set up takes some time because the interpeter has to locate and link several different python files

#**** NOTE: ****
# any imports used in other python defs and classes need to also be imported here in order for the script to exicute properly
#***************
try:
	import os
except ImportError :
	print 'ERROR : Run the batch file again \nOR \nMake sure \'os\' package is installed correctly, to check enter in command prompt: \n<python -m pip install openpyxl> and re-run the script'
	exit()	

try:
	import csv
except ImportError :
	print 'ERROR : Run the batch file again \nOR \nMake sure \'csv\' package is installed correctly, to check enter in command prompt: \n<python -m pip install openpyxl> and re-run the script'
	exit()	

try:
	import openpyxl
	from openpyxl.styles import Font
except ImportError :
	print 'ERROR : Run the batch file again \nOR \nMake sure \'openpyxl\' package is installed correctly, to check enter in command prompt: \n<python -m pip install openpyxl> and re-run the script'
	exit()
	
try:
	import glob
except ImportError :
	print 'ERROR : Run the batch file again \nOR \nMake sure \'glob\' package is installed correctly, to check enter in command prompt: \n<python -m pip install openpyxl> and re-run the script'
	exit()
	
try:	
	import requests
except ImportError :
	print 'ERROR : Run the batch file again \nOR \nMake sure \'requests\' package is installed correctly, to check enter in command prompt: \n<python -m pip install openpyxl> and re-run the script'
	exit()

#import defs and classes from other python files
from getFileLocation import getFileLocation
from getCsvName import getNameCsv
from convertCsv import convertCsv
from getDocumentationLinks import getDocLinks
from condenceUrls import condenceUrls
from analyticsCopy import runAnalytics

csvFileLocation = ""				#stores the file location of the input csv
csvFileName = ""					#stores the tested name and location of the csv
xlsFileName = ""					#stores the tested name and location of the xlsx file that is generated from the csv
csvConvertBool = False				#used to determine if the CSV converted correctly
convertCsvName = "csvConvert.xlsx" 	#name of the output xlsx file
docLinks = []						#stores the urls of the documentation links

#loop asking for file location and CSV name untill valid answers are given
while(csvConvertBool == False):
	#get the location of the csv file and check that it exsists
	#this function loops its self until a valid location is given
	csvFileLocation = getFileLocation("Enter the location of the CSV file", "location: ")

	#get the name of the csv file and check that it exsists
	csvFileName = getNameCsv(csvFileLocation, "Enter CSV file name", "Name: ")

	#convirts the csv to xlsx and stores it in the same location this is for the scripts that use xlsx over csv and viceVersa
	print "Converting the CSV..."	#comment for testing 
	csvConvertBool = convertCsv(csvFileName, convertCsvName)	

print "Convert Done"	#Alert the user that the convertion of the csv file is completed

#get the documentation links
print "Geting Documentation Links"	#alert the user that the script is grabbing the documentation links
docLinks = getDocLinks(csvFileName)	#This function parses the csv file for documentation links
									#The function returns a multiDemensional array of documentation links

''' For Testing '''
print "*****************************************************************************************"
print "************************************Before***********************************************"
print "*****************************************************************************************"
testCount = 0
testLenBefore = 0
testLenAfter = 0
while(testCount < 50):
	print docLinks[testCount]
	testCount = testCount + 1
testLenBefore = len(docLinks)
print "*****************************************************************************************"
print "************************************After************************************************"
print "*****************************************************************************************"
'''End of testing section'''
print "Checking for duplicate links"	#alter the user that the script is removing duplicate links for the documentation links
docLinks = condenceUrls(docLinks)		#The function takes in the multiDimentional arry created by the getDocLinks def and
										#reutns the same dimensioned arry with duplicate links removed

'''Testing Section'''
testCount = 0
while(testCount < 50):
	print docLinks[testCount]
	testCount = testCount + 1
testLenAfter = len(docLinks)
print "*****************************************************************************************"
print "before len: ", testLenBefore, "after len: ", testLenAfter 
'''End of testing section'''


'''*********************************************************************************************
*************************************Next Step is to check the links****************************
*********************************************************************************************'''


'''*********************************************************************************************
************************************Next Step is to report anylitics****************************
*********************************************************************************************'''
runAnalytics()	#This script opens the .xlsx file. Performs anaylitics calculations
				#stores the data in the same .xlsx file and saves/closes it


'''*********************************************************************************************
**********************************Download, update, and upload projects*************************
*********************************************************************************************'''

#downloadFirst


#uploadLast


print "Done!"	#When the script is sucessfuly completed alert the user that it is finished
exit()			#exit the script