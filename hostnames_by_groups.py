# report of all hostnames in an account per group
# by Rafael Alvarez Rivero
# written october 2024

import requests, json, sys, os
from akamai.edgegrid import EdgeGridAuth,EdgeRc
import urllib
import argparse

# from https://github.com/akamai/AkamaiOPEN-edgegrid-python
edgerc_file_path = os.path.expanduser('~/.edgerc')
edgerc_object = EdgeRc(edgerc_file_path)
baseurl = 'https://' + edgerc_object.get('default', 'host')

s=requests.Session()
s.auth=EdgeGridAuth.from_edgerc(edgerc_object,'default')

groups_api='/papi/v1/groups'
prps_api='/papi/v1/properties'

headers = {
    "accept": "application/json",
    "PAPI-Use-Prefixes": "false"
}
grp_req=s.get(baseurl+groups_api,headers=headers)
grp_json=grp_req.json()

for grp in grp_json['groups']['items']:
    print(grp['groupName']+' has the following contract(s) and properties:')
    for contract in grp['contractIds']:
        #print(contract)
        #print()
        params={'groupId': grp['groupId'],'contractId': contract}
        prps=s.get(baseurl+prps_api,headers=headers,params=params)
        prps_json=prps.json()
        for props in prps_json['properties']['items']:
            print('   '+props['propertyName'])
        print()
        

        


	
