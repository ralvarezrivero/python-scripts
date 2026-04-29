# report of properties and products for specific contracts
# written by ralvarez on 2024-06-28
# updated to grab production version only and filter by DSA/Ion

import requests, json, sys, os, time
from akamai.edgegrid import EdgeGridAuth,EdgeRc

#target_contracts = ['2-3MOVP', '3-1E6ALN0', '3-1ENMDU2', '3-8F6KIX', 'C-50BNW5']
target_contracts = ['3-1ENMDU2']

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

# Grab the account switch key from command line
try:
    skey=sys.argv[1]
    print('Using Account Switch Key: ' + skey)
except IndexError:
    print("Error: Please provide the accountSwitchKey as a command line argument.")
    sys.exit(1)

params = {
    "accountSwitchKey": skey
}

print("Fetching groups to map target contracts...\n")
grp_req=s.get(baseurl+groups_api,headers=headers,params=params)

# Safety Check 1
if grp_req.status_code != 200:
    grp_json = grp_req.json()
    print(f"\nAPI Error {grp_req.status_code}: {grp_json.get('title', 'Unknown Error')}")
    sys.exit(1)

grp_json=grp_req.json()
print(f"{'Contract':<12} | {'Property Name':<40} | {'Property ID':<12} | {'Product'}")
print("-" * 90)

for grp in grp_json['groups']['items']:
    for contract in grp['contractIds']:
        
        if contract not in target_contracts:
            continue
            
        prp_params={'groupId': grp['groupId'],'contractId': contract, 'accountSwitchKey': skey}
        
        # --- Retry Loop for Properties ---
        prps_success = False
        prps_retries = 0
        
        while not prps_success and prps_retries < 4:
            prps=s.get(baseurl+prps_api,headers=headers,params=prp_params)
            
            if prps.status_code == 200:
                prps_success = True
            elif prps.status_code == 429:
                print(f"   -> Rate limit hit fetching properties for {contract}! Sleeping 15s... (Retry {prps_retries+1})")
                time.sleep(15)
                prps_retries += 1
            else:
                break # Exit loop if it's a 403, 401, etc.
                
        if not prps_success:
            continue
            
        prps_json=prps.json()
        
        if 'properties' in prps_json and 'items' in prps_json['properties']:
            for prop in prps_json['properties']['items']:
                
                # GRAB THE PRODUCTION VERSION
                prod_version = prop.get('productionVersion')
                
                # If there is no production version, skip entirely
                if prod_version is None:
                    continue 
                
                prop_name = prop.get('propertyName', 'N/A')
                prop_id = prop.get('propertyId', 'N/A')
                
                versions_api = f"/papi/v1/properties/{prop_id}/versions"
                
                # --- Retry Loop for Versions ---
                product = "N/A"
                ver_success = False
                ver_retries = 0
                
                while not ver_success and ver_retries < 4:
                    ver_req = s.get(baseurl+versions_api, headers=headers, params=prp_params)
                    
                    if ver_req.status_code == 200:
                        ver_json = ver_req.json()
                        
                        # Find the specific version that is live on production
                        if 'versions' in ver_json and 'items' in ver_json['versions']:
                            for v in ver_json['versions']['items']:
                                if v.get('propertyVersion') == prod_version:
                                    product = v.get('productId', 'N/A')
                                    break # found the active version, stop looping versions
                                    
                        ver_success = True
                    elif ver_req.status_code == 429:
                        print(f"      [Rate limit hit fetching versions for {prop_id}] Sleeping 15s... (Retry {ver_retries+1})")
                        time.sleep(15)
                        ver_retries += 1
                    else:
                        break # Exit on other errors

                if not ver_success and product == "N/A":
                    product = "RATE_LIMITED_FAILED"
                
                # filter by DSA and Ion only
                #prod_lower = product.lower()
                #if 'site_accel' not in prod_lower and 'fresca' not in prod_lower and 'ion' not in prod_lower:
                #    continue # Skip this property, it's not DSA or ION (e.g. SPM, WAA, etc.)

                print(f"{contract:<12} | {prop_name[:40]:<40} | {prop_id:<12} | {product}")
                
                time.sleep(0.3) 
                
        time.sleep(1)