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

def eml_to_JSON(eml_file, type, local,timestamp):
	
	#convert xml to json
	
	if local:
		elect_data = xmltodict.parse(open(eml_file))
	else:
		elect_data = xmltodict.parse(eml_file)	
	
	if type == "media feed":
	  
		#parse house of reps
		results_json = {}
		summary_json = {}
		electorates_list = []

		for election in elect_data['MediaFeed']['Results']['Election']:
			# House of Representative contests
			
			if 'House' in election:
				# National summary
				results_json['enrollment'] = int(election['House']['Analysis']['National']['Enrolment'])
				results_json['votesCountedPercent'] = float(election['House']['Analysis']['National']['FirstPreferences']['Total']['Votes']['@Percentage'])
				results_json['votesCounted'] = int(election['House']['Analysis']['National']['FirstPreferences']['Total']['Votes']['#text'])
				
				summary_json['enrollment'] = int(election['House']['Analysis']['National']['Enrolment'])
				summary_json['votesCountedPercent'] = float(election['House']['Analysis']['National']['FirstPreferences']['Total']['Votes']['@Percentage'])
				summary_json['votesCounted'] = int(election['House']['Analysis']['National']['FirstPreferences']['Total']['Votes']['#text'])

				# Division summaries

				for contest in election['House']['Contests']['Contest']:

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
		summaryJson = json.dumps(summary_json, indent=4)

		# Save the file locally

		with open('{timestamp}.json'.format(timestamp=timestamp),'w') as fileOut:
			print "saving results locally"
			fileOut.write(newJson)	

		with open('summaryResults.json','w') as fileOut:
			print "saving results locally"
			fileOut.write(summaryJson)		

		# Save to s3

		print "Connecting to S3"
		conn = boto.connect_s3(AWS_KEY,AWS_SECRET)
		bucket = conn.get_bucket('gdn-cdn')

		from boto.s3.key import Key

		k = Key(bucket)
		k.key = "2016/aus-election/results-data/{timestamp}.json".format(timestamp=timestamp)
		k.set_metadata("Cache-Control", "max-age=90")
		k.set_metadata("Content-Type", "application/json")
		k.set_contents_from_string(newJson)
		k.set_acl("public-read")

		k2 = Key(bucket)
		k2.key = "2016/aus-election/results-data/summaryResults.json"
		k2.set_metadata("Cache-Control", "max-age=90")
		k2.set_metadata("Content-Type", "application/json")
		k2.set_contents_from_string(summaryJson)
		k2.set_acl("public-read")


		print "Done, JSON is updated"	

# eml_to_JSON('aec-mediafeed-results-standard-verbose-17496.xml','media feed',True,'20160331011057')	