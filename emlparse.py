import json
import xmltodict
import boto
import os

AWS_KEY = os.environ['AWS_KEY_ID']
AWS_SECRET = os.environ['AWS_SECRET_KEY']

def convertPartyCode(partycode):
	partyCodes = {'LP':'LIB', 'NP':'NAT'}
	if partycode in partyCodes:
		return partyCodes[partycode]
	else:
		return partycode	

def candidate_party(candidate,candidateType):
	if candidateType == 'short':
		if 'eml:AffiliationIdentifier' in candidate:
			return candidate['eml:AffiliationIdentifier']['@ShortCode']
		else:
			return 'IND'
	if candidateType == 'long':
		if 'eml:AffiliationIdentifier' in candidate:
			return candidate['eml:AffiliationIdentifier']['eml:RegisteredName']
		else:
			return 'Independent'

def eml_to_JSON(electionID,eml_file, type, local,timestamp):
	
	#convert xml to json
	
	if local:
		elect_data = xmltodict.parse(open(eml_file))
	else:
		elect_data = xmltodict.parse(eml_file)	
	
	if type == "media feed":
	  
		#parse house of reps
		results_json = {}
		electorates_list = []

		election = elect_data['MediaFeed']['Results']['Election']

		if 'House' in election:
			
			contest = election['House']['Contests']['Contest']

			electorates_json = {}
			electorates_json['id'] = int(contest['PollingDistrictIdentifier']['@Id'])
			electorates_json['name'] = contest['PollingDistrictIdentifier']['Name']
			print contest['PollingDistrictIdentifier']['Name']
			electorates_json['state'] = contest['PollingDistrictIdentifier']['StateIdentifier']['@Id']
			electorates_json['enrollment'] = int(contest['Enrolment']['#text'])
			electorates_json['votesCounted'] = int(contest['FirstPreferences']['Total']['Votes']['#text'])
			candidates = contest['FirstPreferences']['Candidate']
			electorates_json['candidates'] = [
				{
					'candidate_id': int(candidate['eml:CandidateIdentifier']['@Id']),
					'candidate_name': candidate['eml:CandidateIdentifier']['eml:CandidateName'],
					'votesTotal': int(candidate['Votes']['#text']),
					'votesPercent': float(candidate['Votes']['@Percentage']),
					'party_short': convertPartyCode(candidate_party(candidate,'short')),
					'party_long':candidate_party(candidate,'long'),
					'incumbent':candidate['Incumbent']['#text']
				}
				for candidate in candidates
			]
			# print contest['TwoCandidatePreferred']
			if "@Restricted" not in contest['TwoCandidatePreferred'] and "@Maverick" not in contest['TwoCandidatePreferred']:
				twoCandidatePreferred = contest['TwoCandidatePreferred']['Candidate']
				electorates_json['twoCandidatePreferred'] = [
					{
						'candidate_id': int(candidate['eml:CandidateIdentifier']['@Id']),
						'candidate_name': candidate['eml:CandidateIdentifier']['eml:CandidateName'],
						'votesTotal': int(candidate['Votes']['#text']),
						'votesPercent': float(candidate['Votes']['@Percentage']),
						'swing':float(candidate['Votes']['@Swing']),
						'party_short': convertPartyCode(candidate_party(candidate,'short')),
						'party_long':candidate_party(candidate,'long')
					}
					for candidate in twoCandidatePreferred
				]

			elif "@Restricted" in contest['TwoCandidatePreferred']:
				electorates_json['twoCandidatePreferred'] = "Restricted"

			elif "@Maverick" in contest['TwoCandidatePreferred']:
				electorates_json['twoCandidatePreferred'] = "Maverick"						

			twoPartyPreferred = contest['TwoPartyPreferred']['Coalition']
			
			electorates_json['twoPartyPreferred'] = [
				{
					'coalition_id': int(coalition['CoalitionIdentifier']['@Id']),
					'coalition_long': coalition['CoalitionIdentifier']['CoalitionName'],
					'coalition_short': coalition['CoalitionIdentifier']['@ShortCode'],
					'votesTotal': int(coalition['Votes']['#text']),
					'votesPercent': float(coalition['Votes']['@Percentage']),
					'swing':float(coalition['Votes']['@Swing'])
				}
				for coalition in twoPartyPreferred
			]		

			# print electorates_json
			electorates_list.append(electorates_json)			

			# print electorates_list
			results_json['divisions'] = electorates_list

		if 'Senate' in election:
			pass


		newJson = json.dumps(results_json, indent=4)

		# return newJson

		# Save the file locally

		with open('{electionID}-{timestamp}.json'.format(electionID=electionID,timestamp=timestamp),'w') as fileOut:
			print "saving results locally"
			fileOut.write(newJson)	

		# with open('summaryResults.json','w') as fileOut:
		# 	print "saving results locally"
		# 	fileOut.write(summaryJson)		

		# Save to s3

		print "Connecting to S3"
		conn = boto.connect_s3(AWS_KEY,AWS_SECRET)
		bucket = conn.get_bucket('gdn-cdn')

		from boto.s3.key import Key

		k = Key(bucket)
		k.key = "2018/07/aus-byelections/{electionID}-{timestamp}.json".format(electionID=electionID,timestamp=timestamp)
		k.set_metadata("Cache-Control", "max-age=90")
		k.set_metadata("Content-Type", "application/json")
		k.set_contents_from_string(newJson)
		k.set_acl("public-read")


		print "Done, JSON is updated"	

# eml_to_JSON('aec-mediafeed-results-standard-verbose-17496.xml','media feed',True,'20160331011057')	