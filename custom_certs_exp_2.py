# written by ralvarez sept 2024
# this version picks up a file with a json bulksearch result and transform the notAfter epoch to human date

import json
import datetime

with open('t-mocert.json') as origins_data:
    orig_data=json.load(origins_data)

for prop in orig_data:
    print(prop['propertyName'])
    if len(prop['matchLocationResults']) > 0:
        #print(str(len(prop['matchLocationResults'])))
        for loc_results in prop['matchLocationResults']:    
            milli_to_secs=loc_results['notAfter']/1000
            human_date=datetime.datetime.fromtimestamp(milli_to_secs)
            human_date_str=human_date.strftime( "%B - %d - %Y")
            print("    Custom Cert "+loc_results['subjectCN']+" expires "+human_date_str)
            #print('No custom certificates pinned')
    print()