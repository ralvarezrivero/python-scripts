# update single cp code to ion standard 
# using internal Luna APIs
# by Rafael Alvarez Rivero

import requests, json, sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Update a single CP Code Product via Internal API")
    parser.add_argument('-s', '--akasso', help='AKASSO Cookie', required=True)
    parser.add_argument('-t', '--akatoken', help='AKATOKEN Cookie', required=True)
    parser.add_argument('-x', '--xsrf', help='xsrf_token Header', required=True)
    parser.add_argument('-k', '--accountkey', help='Account Switch Key', required=True)
    parser.add_argument('-c', '--cpcode', help='Target CP Code ID (numbers only)', required=True)
    
    args = parser.parse_args()

    baseurl = 'https://control.akamai.com' 
    s = requests.Session()
    
    # Set the internal cookies & headers
    s.cookies.set('AKASSO', args.akasso, domain='.akamai.com')
    s.cookies.set('AKATOKEN', args.akatoken, domain='.akamai.com')
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "x-xsrf-token": args.xsrf  
    }
    params = {'accountSwitchKey': args.accountkey}
    
    cpcode_api = f'/cpcode-mgmt/api/v1/cpcodes/{args.cpcode}'

    print(f"Fetching configuration for CP Code: {args.cpcode}...")
    
    # 1. GET the current configuration
    get_req = s.get(baseurl + cpcode_api, headers=headers, params=params)
    
    if get_req.status_code != 200:
        print(f"Failed to fetch CP code {args.cpcode}. Status: {get_req.status_code}")
        print(get_req.text)
        sys.exit(1)
        
    payload = get_req.json()
    cpcode_name = payload.get('cpcodeName', 'Unknown')
    print(f"Found: {cpcode_name}")
    
    # 2. MODIFY the payload
    # Enforce ONLY Ion Standard in the services array
    payload['services'] = [
        {
            "serviceId": "Web_Exp::Ion_Na",
            "serviceValue": "Ion Standard",
            "unique": False
        }
    ]
    
    print(f"Pushing update for {cpcode_name} (Setting to Ion Standard only)...")
    
    # 3. PUT the modified configuration back
    put_req = s.put(baseurl + cpcode_api, headers=headers, params=params, json=payload)
    
    if put_req.status_code in [200, 204]:
        print(f"  -> SUCCESS: {args.cpcode} updated.")
    else:
        print(f"  -> FAILED: Status {put_req.status_code}")
        print(put_req.text)

if __name__ == "__main__":
    main()