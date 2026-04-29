### Written by Rafael Alvarez Rivero
### Add Ion Premier to CP codes that have DSA/Site Delivery but not Ion Premier

import requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from urllib.parse import urljoin
import json, sys, time
from datetime import datetime

edgerc = EdgeRc('~/.edgerc')
section = 'default'
baseurl = 'https://%s' % edgerc.get(section, 'host')
s = requests.Session()
s.auth = EdgeGridAuth.from_edgerc(edgerc, section)

def get_cc_headers(akasso, akatoken, xsrf):
    return {
        'Accept': 'application/json',
        'X-XSRF-TOKEN': xsrf,
        'Cookie': f'AKATOKEN={akatoken};AKASSO={akasso}',
        'Content-Type': 'application/json'
    }

def get_all_cpcodes(cc_headers):
    url = "https://control.akamai.com/cpcode-mgmt/api/v1/cpcodes"
    response = requests.get(url, headers=cc_headers)
    body = response.json()
    return body.get('cpcodes', [])

def filter_cpcodes(cpcodes):
    to_update = []
    for cpcode in cpcodes:
        cpcode_id = cpcode['cpcode']
        cpcode_name = cpcode['cpcodeName']
        services = cpcode.get('services', [])
        
        has_dsa = any('Site_Accel' in s.get('serviceId', '') for s in services)
        has_site_delivery = any('Site_Del' in s.get('serviceId', '') for s in services)
        has_ion = any('Ion_SPM' in s.get('serviceId', '') or 'Ion_Na' in s.get('serviceId', '') for s in services)
        
        # Add Ion Premier if has DSA OR Site Delivery, but no Ion Premier
        if (has_dsa or has_site_delivery) and not has_ion:
            to_update.append({'id': cpcode_id, 'name': cpcode_name})
            #print(f"CP Code {cpcode_id} ({cpcode_name}) needs Ion Premier")
    
    return to_update

def get_cpcode_config(cpcode_id, headers):
    url = f"https://control.akamai.com/cpcode-mgmt/api/v1/cpcodes/{cpcode_id}"
    response = requests.get(url, headers=headers)
    return response.json()

def update_cpcode(cpcode_id, config, headers):
    services = config.get('services', [])
    has_ion = any(s.get('serviceId') == 'Web_Exp::Ion_SPM' for s in services)
    
    if has_ion:
        return False
    
    ion_service = {
        "serviceId": "Web_Exp::Ion_SPM",
        "serviceValue": "Ion Premier",
        "serviceStartDate": datetime.now().strftime("%m/%d/%Y"),
        "serviceEndDate": datetime.now().strftime("%m/%d/%Y")
    }
    
    if services is None:
        config['services'] = []
    config['services'].append(ion_service)
    
    url = f"https://control.akamai.com/cpcode-mgmt/api/v1/cpcodes/{cpcode_id}"
    
    # Debug: print what we're sending
    print(f"Sending PUT to {url}")
    print(f"Updated services: {json.dumps(config['services'], indent=2)}")
    
    response = requests.put(url, headers=headers, json=config)
    
    # Debug: print response
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text[:500]}")
    
    return True

def main(accountSwitchKey, akasso, akatoken, xsrf):
    cc_headers = get_cc_headers(akasso, akatoken, xsrf)
    
    print("Getting all CP codes from Control Center...")
    all_cpcodes = get_all_cpcodes(cc_headers)
    for cp_code in all_cpcodes[:2]:
        print(f"CP CODE {cp_code['cpcodeName']} has these products associated:")
        for service in cp_code['services']:
            print(f"      product {service['serviceValue']} with service ID {service['serviceId']}")
        print()    
    print()

    print(f"Found {len(all_cpcodes)} total CP codes")
    print()
    
    print("Filtering for CP codes with DSA but no Ion Premier...")
    cpcodes_to_update = filter_cpcodes(all_cpcodes)
    print()
    
    if len(cpcodes_to_update) == 0:
        print("No CP codes need updating")
        return
    
    print(f"Found {len(cpcodes_to_update)} CP codes to update")
    print()
    print("First CP code that needs updating:")
    print(json.dumps(cpcodes_to_update[0], indent=4))

    for cpcode in cpcodes_to_update[:2]:
        cpcode_id = cpcode['id']
        cpcode_name = cpcode['name']
        
        config = get_cpcode_config(cpcode_id, cc_headers)
        updated = update_cpcode(cpcode_id, config, cc_headers)
        
        if updated:
            print(f"Updated CP Code {cpcode_id} ({cpcode_name})")
        else:
            print(f"Skipped CP Code {cpcode_id} ({cpcode_name}) - already has Ion Premier")
        
        time.sleep(0.5)

if __name__ == "__main__":
    accountSwitchKey = sys.argv[1]
    akasso = sys.argv[2]
    akatoken = sys.argv[3]
    xsrf = sys.argv[4]
    print("=============================================")
    print("Adding Ion Premier to DSA CP codes...")
    print("=============================================")
    main(accountSwitchKey, akasso, akatoken, xsrf)