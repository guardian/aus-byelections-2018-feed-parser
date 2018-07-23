import os
import simplejson as json
from datetime import datetime
import boto

AWS_KEY = os.environ['AWS_KEY_ID']
AWS_SECRET = os.environ['AWS_SECRET_KEY']

def saveRecentResults(timestamp):

	# check if file exists already

	jsonObj = []

	if os.path.exists('recentResults.json'):

		print "Results file exists, updating"

		with open('recentResults.json','r') as recentResultsFile:
			
			# Convert the results to a list of datetime objects

			tempList = []
			recentResults = json.load(recentResultsFile)
			for result in recentResults:
				tempList.append(datetime.strptime(result,"%Y%m%d%H%M%S"))

			# Sort it	

			tempList.sort(reverse=True)

			# Check if it's less than 20 and append the new timestamp

			if len(tempList) < 20:

				print "Less than twenty results, appending latest now"

				tempList.append(datetime.strptime(timestamp,"%Y%m%d%H%M%S"))
				tempList.sort(reverse=True)
				for temp in tempList:
					jsonObj.append(datetime.strftime(temp, '%Y%m%d%H%M%S'))	
				print jsonObj

			# If it's 20, remove the oldest timestamp, then append the new one	

			elif len(tempList) == 20:

				print "Twenty results, removing oldest and appending newest"

				del tempList[-1]
				tempList.append(datetime.strptime(timestamp,"%Y%m%d%H%M%S"))
				tempList.sort(reverse=True)
				for temp in tempList:
					jsonObj.append(datetime.strftime(temp, '%Y%m%d%H%M%S'))	
				print jsonObj
					
		# Write the new version
		newJson = json.dumps(jsonObj, indent=4)
		with open('recentResults.json','w') as fileOut:
				fileOut.write(newJson)				

		print "Finished saving results log locally"

		print "Connecting to S3"
		conn = boto.connect_s3(AWS_KEY,AWS_SECRET)
		bucket = conn.get_bucket('gdn-cdn')

		from boto.s3.key import Key

		k = Key(bucket)
		k.key = "2018/07/aus-byelections/recentResults.json".format(timestamp=timestamp)
		k.set_metadata("Cache-Control", "max-age=180")
		k.set_metadata("Content-Type", "application/json")
		k.set_contents_from_string(newJson)
		k.set_acl("public-read")
		print "Done, JSON is updated"			

	# Otherwise start a new file		

	else:
		print "No results file, making one now"
		jsonObj.append(timestamp)
		newJson = json.dumps(jsonObj, indent=4)
		with open('recentResults.json','w') as fileOut:
				fileOut.write(newJson)

		print "Finished creating results log"

		print "Connecting to S3"
		conn = boto.connect_s3(AWS_KEY,AWS_SECRET)
		bucket = conn.get_bucket('gdn-cdn')

		from boto.s3.key import Key

		k = Key(bucket)
		k.key = "2016/aus-election/results-data/recentResults.json".format(timestamp=timestamp)
		k.set_metadata("Cache-Control", "max-age=90")
		k.set_metadata("Content-Type", "application/json")
		k.set_contents_from_string(newJson)
		k.set_acl("public-read")
		print "Done, JSON is updated"			

# saveRecentResults()
