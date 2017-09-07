#Dustin Henderson
#condence URLS

def condenceUrls(inputList):
	inputList = set(tuple(element) for element in inputList)						#remove any duplicates in the list
	inputList = [list(t) for t in set(tuple(element) for element in inputList)]		#convert back to list for the return
	return inputList

'''Test Call'''
# testList = [['a',0],['b',1],['c',2],['d',3],['a',0]]
# print testList
# testList = condenceUrls(testList)
# print testList