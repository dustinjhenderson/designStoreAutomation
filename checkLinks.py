#testing url libraries
#Dustin Henderson

import csv
import urllib2

def checkUrl(url):
	code = "200"
	if url[0] == 'h':
		req = urllib2.Request(url, data = None)
		req.add_header('User', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')
		try:
			urllib2.urlopen(req, timeout=4)
		except urllib2.HTTPError, e:
			if(e.code != 403):
				code = e.code
			else:
				print "403 need to figure out how to get into wiki"
		except urllib2.URLError, e:
			code = e.args
	return code
			
'''test decloration'''
testUrlList = [	'https://www.altera.com/support/support-resources/design-examples/intellectual-property/embedded/nios-ii/exm-accelerated-fir.html',
				'https://www.altera.com/support/support-resources/design-examples/intellectual-property/embedded/nios-ii/exm-accelerated-fir.html',
				'https://www.altera.com/support/support-resources/design-examples/intellectual-property/embedded/nios-ii/exm-altia-demo.html',
				'https://www.altera.com/support/support-resources/design-examples/intellectual-property/embedded/nios-ii/exm-avalon-mm.html',
				'https://www.altera.com/support/support-resources/design-examples/intellectual-property/embedded/nios-ii/exm-tes-demo.html',
				'https://rocketboards.org/foswiki/view/Design Examples/AndroidForDE1SoCBoard',
				'http://www.alterawiki.com/wiki/10-Gbps_Ethernet_MAC_and_XAUI_PHY_Interoperability_Hardware_Demonstration_Reference_Design']

for url in testUrlList:
	print "url: ", url
	print checkUrl(url)
