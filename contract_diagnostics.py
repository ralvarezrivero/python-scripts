import requests, sys, os
from akamai.edgegrid import EdgeGridAuth, EdgeRc

target_contract = '3-1ENMDU2'

edgerc_object = EdgeRc(os.path.expanduser('~/.edgerc'))
baseurl = 'https://' + edgerc_object.get('default', 'host')
s = requests.Session()
s.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')

headers = {"accept": "application/json", "PAPI-Use-Prefixes": "false"}
skey = sys.argv[1]
params = {"accountSwitchKey": skey}

print(f"--- DIAGNOSTIC TEST FOR {target_contract} ---")
grp_req = s.get(baseurl + '/papi/v1/groups', headers=headers, params=params)
grp_json = grp_req.json()

found = False
for grp in grp_json.get('groups', {}).get('items', []):
    if target_contract in grp.get('contractIds', []):
        found = True
        print(f"\nSUCCESS: Contract found in Group -> {grp['groupName']} (ID: {grp['groupId']})")
        
        # Now let's check the properties in this group/contract combo
        prp_params = {'groupId': grp['groupId'], 'contractId': target_contract, 'accountSwitchKey': skey}
        prps = s.get(baseurl + '/papi/v1/properties', headers=headers, params=prp_params)
        prps_json = prps.json()
        
        items = prps_json.get('properties', {}).get('items', [])
        print(f"API returned {len(items)} properties for this contract.")
        
        for prop in items:
            name = prop.get('propertyName')
            prod_ver = prop.get('productionVersion')
            stg_ver = prop.get('stagingVersion')
            print(f"  -> Property: {name} | Prod Version: {prod_ver} | Staging Version: {stg_ver}")

if not found:
    print(f"\nCRITICAL FAIL: The contract {target_contract} is NOT in the groups list.")
    print("Your API client cannot see this contract under this Account Switch Key.")