#!/usr/bin/env python3
import json
import requests
import sys
import os
import argparse
from typing import Dict, List, Any
from akamai.edgegrid import EdgeGridAuth, EdgeRc


def get_contracts(session, hostname, account_switch_key=None):
    base_url = f"https://{hostname}/papi/v1/contracts"
    
    params = {}
    if account_switch_key:
        params["accountSwitchKey"] = account_switch_key
    
    headers = {
        "Accept": "application/json"
    }
    
    try:
        response = session.get(
            base_url,
            params=params,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching contracts: {e}")
        sys.exit(1)


def get_enrollments(session, hostname, contract_id, account_switch_key=None):
    base_url = f"https://{hostname}/cps/v2/enrollments"
    
    params = {
        "contractId": contract_id
    }
    
    if account_switch_key:
        params["accountSwitchKey"] = account_switch_key
    
    headers = {
        "Accept": "application/json"
    }
    
    try:
        response = session.get(
            base_url,
            params=params,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching enrollments for contract {contract_id}: {e}")
        return {"enrollments": []}


def extract_data(data):
    result = []
    
    if 'enrollments' not in data:
        return result
        
    for enrollment in data['enrollments']:
        enrollment_data = {
            'enrollment_id': enrollment.get('id', 'Unknown'),
            'common_name': None,
            'dns_names': None,
            'disallowed_tls_versions': None
        }
        
        if 'csr' in enrollment and 'cn' in enrollment['csr']:
            enrollment_data['common_name'] = enrollment['csr']['cn']
            
        if ('networkConfiguration' in enrollment and 
            'dnsNameSettings' in enrollment['networkConfiguration'] and 
            'dnsNames' in enrollment['networkConfiguration']['dnsNameSettings']):
            enrollment_data['dns_names'] = enrollment['networkConfiguration']['dnsNameSettings']['dnsNames']
            
        if ('networkConfiguration' in enrollment and 
            'disallowedTlsVersions' in enrollment['networkConfiguration']):
            enrollment_data['disallowed_tls_versions'] = enrollment['networkConfiguration']['disallowedTlsVersions']
            
        result.append(enrollment_data)
        
    return result


def setup_session(edgerc_file, edgerc_section):
    edgerc_path = os.path.expanduser(edgerc_file)
    edgerc = EdgeRc(edgerc_path)
    section = edgerc_section
    
    session = requests.Session()
    session.auth = EdgeGridAuth(
        client_token=edgerc.get(section, 'client_token'),
        client_secret=edgerc.get(section, 'client_secret'),
        access_token=edgerc.get(section, 'access_token')
    )
    
    hostname = edgerc.get(section, 'host')
    return session, hostname


def main():
    parser = argparse.ArgumentParser(description="Extract CPS enrollment data")
    parser.add_argument("--account-switch-key", help="Account Switch Key (optional)")
    parser.add_argument("--edgerc", default="~/.edgerc", help="Path to .edgerc file (default: ~/.edgerc)")
    parser.add_argument("--section", default="default", help="Section in .edgerc file (default: default)")
    args = parser.parse_args()
    
    session, hostname = setup_session(args.edgerc, args.section)
    
    all_enrollment_data = []
    
    # Fetch all contracts
    contracts_data = get_contracts(session, hostname, args.account_switch_key)
    
    if 'contracts' in contracts_data and 'items' in contracts_data['contracts']:
        for contract in contracts_data['contracts']['items']:
            contract_id = contract.get('contractId')
            if contract_id:
                print(f"Fetching enrollments for contract: {contract_id}", file=sys.stderr)
                data = get_enrollments(session, hostname, contract_id, args.account_switch_key)
                extracted = extract_data(data)
                if extracted:
                    all_enrollment_data.extend(extracted)
                    print(f"Found {len(extracted)} enrollments for contract {contract_id}", file=sys.stderr)
                else:
                    print(f"No enrollments found for contract {contract_id}", file=sys.stderr)
    else:
        print("No contracts found or invalid response format", file=sys.stderr)
    
    print(json.dumps(all_enrollment_data, indent=2))


if __name__ == "__main__":
    main()