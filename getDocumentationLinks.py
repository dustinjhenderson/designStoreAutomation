#Get Documentation Links
#Dustin Henderson

import csv

def getDocLinks(csvLocation):
	#title, doc1, doc2, doc3, doc4, doc5,
	docLinks = []
	with open(csvLocation, 'rb') as table:
		reader = csv.reader(table, delimiter=',')
		for row in reader:
			if (row[6][0] != "-"):
				docLinks.append([row[1],row[6],row[7],row[8],row[9],row[10]])
	return docLinks

'''test call'''
# docLinks = []
# docLinks = getDocLinks('testFile.csv')
# counter = 0

# for lines in docLinks:
	# print counter, lines
	# counter = counter + 1


	
	
#old code
'''
import csv

def getDocLinks(csvLocation):
	#title, doc1, doc2, doc3, doc4, doc5,
	docLinks = [[],[],[],[],[],[]]
	with open(csvLocation, 'rb') as table:
		reader = csv.reader(table, delimiter=',')
		for row in reader:
			if (row[6][0] != "-"):
				docLinks[0].append(row[1])
				docLinks[1].append(row[6])
				docLinks[2].append(row[7])
				docLinks[3].append(row[8])
				docLinks[4].append(row[9])
				docLinks[5].append(row[10])
	return docLinks


docLinks = [[],[],[],[],[],[]]
docLinks = getDocLinks('testFile.csv')
counter = 0

for lines in docLinks[0]:
	print counter, docLinks[0][counter], docLinks[1][counter], docLinks[2][counter], docLinks[3][counter], docLinks[4][counter], docLinks[5][counter]
	counter = counter + 1
'''