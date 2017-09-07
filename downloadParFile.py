#download par files from the design store
#Dustin Henderson
import urllib

def downloadParFile(url, name):
	attempts = 0
	while(attempts < 2):
		try:
			urllib.urlretrieve (url, name + ".par")
			break
		except:
			print "Attempts at downloading par: ", attempts
		attempts = attempts + 1
	
'''Test Call'''
#downloadParFile("https://cloud.altera.com/devstore/platform/2008/download/", "test1")