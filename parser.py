#!/usr/bin/env python

import simplejson as json
from ftplib import FTP
import os
from zipfile import ZipFile
from StringIO import StringIO
from datetime import datetime
from datetime import timedelta
import emlparse
import logresults
import schedule
import time

#Generates a list of zip files from the AEC
# 2013 id = '17496'
# 2016 address = results.aec.gov.au
# 2016 id = '20499'
# 2016 address = mediafeed.aec.gov.au

verbose = True
electionIDs = ['22692','22693','22694','22695','22696']
testIDs = ['21364','21379']

testTime = datetime.strptime("2017-12-16 17:00","%Y-%m-%d %H:%M")

# path = '/{electionID}/Standard/Verbose/'.format(electionID=electionID)

print "Logging in to AEC FTP"

# ftpUrl = 'mediafeed.aec.gov.au'
ftpUrl = 'mediafeedarchive.aec.gov.au'

ftp = FTP(ftpUrl)
ftp.login()

def parse_results(test,idList):

	new_data = {}

	for electionID in idList:
		
		print("Election: " + electionID)

		ftp.cwd('/{electionID}/Standard/Verbose/'.format(electionID=electionID))

		my_files = []

		def get_filenames(ln):
			# global my_files
			cols = ln.split(' ')
			objname = cols[len(cols)-1] # file or directory name
			if objname.endswith('.zip'):
				my_files.append(objname) # full path


		print "Getting all the filenames"

		ftp.retrlines('LIST', get_filenames)
		timestamps = []

		if verbose:
			print my_files

		# Get latest timestamp

		print "Getting latest timestamp"

		for f in my_files:
			timestamp = f.split("-")[-1].replace(".zip","")

			if test:
				print datetime.strptime(timestamp,"%Y%m%d%H%M%S")
				print testTime
				if datetime.strptime(timestamp,"%Y%m%d%H%M%S") < testTime:
					print "test time is ", testTime
					if verbose:
						print timestamp
					timestamps.append(datetime.strptime(timestamp,"%Y%m%d%H%M%S"))
			else:
				if verbose:
					print timestamp

				timestamps.append(datetime.strptime(timestamp,"%Y%m%d%H%M%S"))

		print timestamps		
		latestTimestamp = max(timestamps)
		latestTimestampStr = datetime.strftime(latestTimestamp, '%Y%m%d%H%M%S')

		print "latest timestamp is", latestTimestamp

		# Check if results log exists

		if os.path.exists('recentResults.json'):

			# Get recent timestamps of results

			with open('recentResults.json','r') as recentResultsFile:
				recentResults = json.load(recentResultsFile)

			print recentResults

			# Check if we have it or not

			if latestTimestampStr not in recentResults[electionID]:
				
				print "{timestamp} hasn't been saved, saving now".format(timestamp=latestTimestampStr)
				
				#Get latest file

				latestFile = "aec-mediafeed-Standard-Verbose-{electionID}-{timestamp}.zip".format(electionID=electionID,timestamp=datetime.strftime(latestTimestamp, '%Y%m%d%H%M%S'))
				r = StringIO()

				print('Getting ' + latestFile)

				#Get file, read into memory

				ftp.retrbinary('RETR ' + latestFile, r.write)
				input_zip=ZipFile(r, 'r')
				ex_file = input_zip.open("xml/aec-mediafeed-results-standard-verbose-" + electionID + ".xml")
				content = ex_file.read()
				
				# print content

				print "Parsing the feed into JSON"

				emlparse.eml_to_JSON(electionID,content,'media feed',False,latestTimestampStr)
				logresults.saveRecentResults(electionID,idList,latestTimestampStr)

			if latestTimestampStr in recentResults[electionID]:
				print "{timestamp} has already been saved".format(timestamp=latestTimestampStr)

		# It doesn't exist, so treat timestamp as first

		else:
			print "Results file not found, saving {timestamp} as first entry".format(timestamp=latestTimestampStr)
				
			#Get latest file

			latestFile = "aec-mediafeed-Standard-Verbose-{electionID}-{timestamp}.zip".format(electionID=electionID,timestamp=datetime.strftime(latestTimestamp, '%Y%m%d%H%M%S'))
			r = StringIO()

			print('Getting ' + latestFile)

			#Get file, read into memory

			ftp.retrbinary('RETR ' + latestFile, r.write)
			input_zip = ZipFile(r, 'r')
			ex_file = input_zip.open("xml/aec-mediafeed-results-standard-verbose-" + electionID + ".xml")
			content = ex_file.read()
			
			# print content

			print "Parsing the feed into JSON"

			emlparse.eml_to_JSON(electionID,content,'media feed',False,latestTimestampStr)
			logresults.saveRecentResults(electionID,idList,latestTimestampStr)

		print "Done, results all saved"

# Use scheduler to time function every 2 minutes

parse_results(False,electionIDs)
schedule.every(2).minutes.do(parse_results,False,electionIDs)

while True:
    schedule.run_pending()
    time.sleep(1)
    print datetime.now()

# Test function, counts from 6 pm to 11 pm on election night 2013    

# def runTest():
# 	global testTime
# 	# testTime = datetime.strptime("2016-12-16 17:00","%Y-%m-%d %H:%M")
# 	endTime = datetime.strptime("2017-12-16 19:00","%Y-%m-%d %H:%M")
# 	parse_results(True,testIDs)
# 	schedule.every(2).minutes.do(parse_results,True,testIDs)
	
# 	while testTime < endTime:
# 		schedule.run_pending()
# 		testTime = testTime + timedelta(seconds=1)
# 		print testTime
# 		time.sleep(1)


# runTest()

# parse_results(True)
# ftp.quit()

