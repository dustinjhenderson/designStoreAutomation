#main
#Dustin Henderson

print "Starting Up..."

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

from getFileLocation import getFileLocation
from getCsvName import getNameCsv
from convertCsv import convertCsv
from getDocumentationLinks import getDocLinks
from condenceUrls import condenceUrls
from analyticsCopy import runAnalytics

csvFileLocation = ""	#stores the file location of the input csv
csvFileName = ""		#stores the tested name and location of the csv
xlsFileName = ""		#stores the tested name and location of the xlsx file that is generated from the csv
csvConvertBool = False	#used to determine if the CSV converted correctly
convertCsvName = "csvConvert.xlsx" #name of the output xlsx file
docLinks = []			#stores the urls of the documentation links

while(csvConvertBool == False):
	#get the location of the csv file and check that it exsists
	csvFileLocation = getFileLocation("Enter the location of the CSV file", "location: ")

	#get the name of the csv file and check that it exsists
	csvFileName = getNameCsv(csvFileLocation, "Enter CSV file name", "Name: ")

	#convirts the csv to xlsx and stores it in the same location
	print "Converting the CSV..."
	csvConvertBool = convertCsv(csvFileName, convertCsvName)

print "Convert Done"

#get the documentation links
print "Geting Documentation Links"
docLinks = getDocLinks(csvFileName)

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
print "Checking for duplicate links"
docLinks = condenceUrls(docLinks)

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
runAnalytics()


'''*********************************************************************************************
**********************************Download, update, and upload projects*************************
*********************************************************************************************'''

#downloadFirst


#uploadLast


print "Done!"
exit()