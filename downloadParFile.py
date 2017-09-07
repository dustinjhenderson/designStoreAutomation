#Download .par Files from the design store
#This def acepts an url to a .par file and downloads the file 
#to the directory the script is stored in. If the download
#fials the def will attempt to reDownload the file 3 times
#before reporting and error and completing
#Dustin Henderson

import urllib	#need to be imported in main script

#Url need to be a url to the .par file download
#The url entered should be parced from the download button
#in the design store html code
#The name need to be a string. The string does not include .par
#extention. The .par file is downloaded and saved under the name given
def downloadParFile(url, name):	
	attempts = 0	#used to store the number of attempts at downloading the file
	while(attempts < 2): #do not try and download a file more than 3 times
		try:
			urllib.urlretrieve (url, name + ".par") #retrive the url
			attempts = 5	#if its sucessful break the loop
		except:
			print "Attempts at downloading par: ", attempts	#if there is a fialure print the number of attempts
		attempts = attempts + 1	#increment the number of attempts
	
'''Test Call'''
#downloadParFile("https://cloud.altera.com/devstore/platform/2008/download/", "test1")