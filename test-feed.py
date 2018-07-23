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

verbose = True
electionID = '17496'
my_files = []

print "Logging in to AEC FTP"

def get_filenames(ln):
		# global my_files
		cols = ln.split(' ')
		objname = cols[len(cols)-1] # file or directory name
		if objname.endswith('.zip'):
			my_files.append(objname) 

ftp = FTP('mediafeed.aec.gov.au')
ftp.login()
ftp.retrlines('LIST', get_filenames)

