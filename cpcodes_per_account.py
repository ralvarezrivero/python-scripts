# report of all cpcodes and products in an account per group
# written by ralvarez on 2024-06-27

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
cpcodes_api='/papi/v1/cpcodes'

headers = {
    "accept": "application/json",
    "PAPI-Use-Prefixes": "false"
}

# Grab the account switch key from command line execution
try:
    skey=sys.argv[1]
    print('Using Account Switch Key: ' + skey)
except IndexError:
    print("Error: Please provide the accountSwitchKey as a command line argument.")
    sys.exit(1)

params = {
    "accountSwitchKey": skey
}

grp_req=s.get(baseurl+groups_api,headers=headers,params=params)
grp_json=grp_req.json()

if grp_req.status_code != 200:
    print(f"\nAPI Error {grp_req.status_code}: {grp_json.get('title', 'Unknown Error')}")
    print(f"Detail: {grp_json.get('detail', 'No details provided.')}")
    sys.exit(1)


for grp in grp_json['groups']['items']:
    print(grp['groupName']+' has the following contract(s) and cpcodes:')
    for contract in grp['contractIds']:
        print(contract)
        # print()
        
        # Add accountSwitchKey to the inner loop params so it carries over
        cp_params={'groupId': grp['groupId'],'contractId': contract, 'accountSwitchKey': skey}
        
        cpc=s.get(baseurl+cpcodes_api,headers=headers,params=cp_params)
        cpc_json=cpc.json()
        
        # print(cpc_json)
        
        # Check if the contract/group combo actually has cpcodes to avoid KeyError
        if 'cpcodes' in cpc_json and 'items' in cpc_json['cpcodes']:
            for cp in cpc_json['cpcodes']['items']:
                # Products are returned as a list, so we join them into a readable string
                products = ", ".join(cp.get('productIds', ['No Product']))
                
                print('   '+cp['cpcodeName']+' cpcodeId: '+cp['cpcodeId']+' | products: '+products)
        else:
            print('   No cpcodes found for this contract/group combo.')
    print()