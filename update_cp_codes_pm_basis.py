# bulk update cp codes to matching product and remove Site Accelerator
# using internal Luna APIs and a CSV mapping file
# by Rafael Alvarez Rivero

import requests, json, sys, csv, time
import argparse

# Dictionary to map product names to their Akamai internal service objects
PRODUCT_MAP = {
    'Ion Premier': {
        "serviceId": "Web_Exp::Ion_SPM",
        "serviceValue": "Ion Premier",
        "unique": False
    },
    'Ion Standard': {
        "serviceId": "Web_Exp::Ion_Na",
        "serviceValue": "Ion Standard",
        "unique": False
    },
    'Site Accelerator': {
        "serviceId": "Site_Accel::Site_Accel",
        "serviceValue": "Site Accelerator",
        "unique": False
    }
}

def main():
    parser = argparse.ArgumentParser(description="Bulk Update CP Code Products via Internal API")
    parser.add_argument('-s', '--akasso', help='AKASSO Cookie', required=True)
    parser.add_argument('-t', '--akatoken', help='AKATOKEN Cookie', required=True)
    parser.add_argument('-x', '--xsrf', help='xsrf_token Header', required=True)
    parser.add_argument('-f', '--file', help='Path to the CSV file', required=True)
    
    args = parser.parse_args()

    baseurl = 'https://control.akamai.com' 
    session = requests.Session()
    
    session.cookies.set('AKASSO', args.akasso, domain='.akamai.com')
    session.cookies.set('AKATOKEN', args.akatoken, domain='.akamai.com')
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "x-xsrf-token": args.xsrf  
    }
    
    processed_cpcodes = set()
    
    print(f"Reading mapping data from {args.file}...\n")
    
    with open(args.file, mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            cpcode = str(row.get('CP Code', '')).strip()
            target_product = str(row.get('Product in the PM', '')).strip()
            
            if not cpcode or cpcode in processed_cpcodes:
                continue
                
            processed_cpcodes.add(cpcode)
            
            if target_product not in PRODUCT_MAP:
                print(f"[{cpcode}] SKIP: Unknown target product '{target_product}' in CSV.")
                continue

            cpcode_api = f'/cpcode-mgmt/api/v1/cpcodes/{cpcode}'
            print(f"[{cpcode}] Fetching configuration...")
            
            get_req = session.get(baseurl + cpcode_api, headers=headers)
            
            if get_req.status_code != 200:
                print(f"  -> ERROR fetching CP code. Status: {get_req.status_code}")
                time.sleep(1)
                continue
                
            payload = get_req.json()
            services = payload.get('services', [])
            original_service_values = [s.get('serviceValue') for s in services]
            
            needs_update = False
            new_services = []
            has_target = False
            
            # filter existing services
            for s in services:
                val = s.get('serviceValue')
                if val == 'Site Accelerator':
                    needs_update = True  # dropping this product
                else:
                    new_services.append(s)
                    if val == target_product:
                        has_target = True

            # guarantee the target product is present
            if not has_target:
                new_services.append(PRODUCT_MAP[target_product])
                needs_update = True
                
            # apply the update if something changed
            if needs_update:
                new_service_values = [s.get('serviceValue') for s in new_services]
                print(f"  -> UPDATE REQUIRED: Changing from {original_service_values} to {new_service_values}")
                
                payload['services'] = new_services
                
                put_req = session.put(baseurl + cpcode_api, headers=headers, json=payload)
                if put_req.status_code in [200, 204]:
                    print(f"  -> SUCCESS: CP Code updated.")
                else:
                    print(f"  -> FAILED: Status {put_req.status_code}")
                    print(put_req.text)
            else:
                print(f"  -> OK: Services {original_service_values} are already perfectly configured. No action needed.")
            
            time.sleep(3)
            print("-" * 60)

    print("\nBulk processing done")

if __name__ == "__main__":
    main()