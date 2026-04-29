#!/usr/bin/env python3

import json
import sys
import os
import argparse
import time
from akamai.edgegrid import EdgeGridAuth, EdgeRc
import requests
from urllib.parse import urljoin

def find_and_replace_logging_section(rule_tree, new_logging_section):
    """
    Recursively search for the logging section in the rule tree and replace it
    Returns (updated_tree, was_replaced)
    """
    was_replaced = False
    
    if isinstance(rule_tree, dict):
        # Check if this is the logging section
        if rule_tree.get('name', '').startswith('Logging -'):
            print(f"Found logging section: {rule_tree['name']}")
            # Return the new logging section, but preserve the original name
            new_section = new_logging_section.copy()
            new_section['name'] = rule_tree['name']
            return new_section, True
        
        # Process children recursively
        if 'children' in rule_tree and isinstance(rule_tree['children'], list):
            new_children = []
            for child in rule_tree['children']:
                updated_child, child_replaced = find_and_replace_logging_section(child, new_logging_section)
                new_children.append(updated_child)
                if child_replaced:
                    was_replaced = True
                    print("Replaced logging section successfully")
            rule_tree['children'] = new_children
    
    return rule_tree, was_replaced

def update_property_with_new_logging(property_file, logging_file, output_file=None):
    """
    Main function to update the property with the new logging section
    """
    # Load the property JSON
    with open(property_file, 'r') as f:
        property_json = json.load(f)
    
    # Load the logging section JSON
    with open(logging_file, 'r') as f:
        logging_json = json.load(f)
    
    # Find and replace the logging section
    updated_rules, was_replaced = find_and_replace_logging_section(property_json['rules'], logging_json)
    
    if not was_replaced:
        print("No logging section found in the property configuration.")
        return False
    
    property_json['rules'] = updated_rules
    
    # Save the updated property JSON
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(property_json, f, indent=4)
        print(f"Updated property saved to {output_file}")
    else:
        # If no output file specified, overwrite the input file
        with open(property_file, 'w') as f:
            json.dump(property_json, f, indent=4)
        print(f"Updated property saved back to {property_file}")
    
    return True

def find_property_by_name(session, base_url, property_name, account_key=None, max_retries=3):
    """
    Find property by name using the find-by-value API with retry logic
    """
    find_url = urljoin(base_url, "/papi/v1/search/find-by-value")
    
    request_data = {
        "propertyName": property_name
    }
    
    params = {}
    if account_key:
        params["accountSwitchKey"] = account_key
    
    # Try a few times with backoff
    for attempt in range(max_retries):
        try:
            response = session.post(find_url, json=request_data, params=params)
            
            if response.status_code == 200:
                break
            
            print(f"Attempt {attempt+1}/{max_retries}: Failed to find property by name: {response.status_code}")
            if response.text:
                print(response.text)
            
            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"Error during API call: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    if response.status_code != 200:
        return None
    
    result = response.json()
    versions = result.get('versions', {}).get('items', [])
    
    if not versions:
        print(f"No versions found for property {property_name}")
        return None
    
    # Find the latest production or latest version
    prod_versions = [v for v in versions if v.get('productionStatus') == 'ACTIVE']
    if prod_versions:
        latest_prod = max(prod_versions, key=lambda x: x.get('propertyVersion', 0))
        return latest_prod
    
    # If no production version, get the latest version
    latest_version = max(versions, key=lambda x: x.get('propertyVersion', 0))
    return latest_version

def get_property_rules(session, base_url, property_id, property_version, contract_id, group_id, account_key=None, max_retries=3):
    """
    Get the rules for a specific property version with retry logic
    """
    rules_url = f"/papi/v1/properties/{property_id}/versions/{property_version}/rules"
    url = urljoin(base_url, rules_url)
    
    params = {
        "contractId": contract_id,
        "groupId": group_id
    }
    
    if account_key:
        params["accountSwitchKey"] = account_key
    
    # Try a few times with backoff
    for attempt in range(max_retries):
        try:
            response = session.get(url, params=params)
            
            if response.status_code == 200:
                break
            
            print(f"Attempt {attempt+1}/{max_retries}: Failed to get property rules: {response.status_code}")
            if response.text:
                print(response.text)
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"Error during API call: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    if response.status_code != 200:
        return None
    
    return response.json()

def create_new_property_version(session, base_url, property_id, contract_id, group_id, account_key=None, max_retries=3):
    """
    Create a new version of the property based on the latest version
    """
    create_version_url = f"/papi/v1/properties/{property_id}/versions"
    url = urljoin(base_url, create_version_url)
    
    params = {
        "contractId": contract_id,
        "groupId": group_id
    }
    
    if account_key:
        params["accountSwitchKey"] = account_key
    
    # Get the latest version
    versions_url = urljoin(base_url, f"/papi/v1/properties/{property_id}/versions")
    versions_response = session.get(versions_url, params=params)
    
    if versions_response.status_code != 200:
        print(f"Failed to get property versions: {versions_response.status_code}")
        print(versions_response.text)
        return None
    
    versions_data = versions_response.json()
    versions = versions_data.get('versions', {}).get('items', [])
    
    if not versions:
        print(f"No versions found for property {property_id}")
        return None
    
    latest_version = max(versions, key=lambda x: x.get('propertyVersion', 0))
    from_version = latest_version.get('propertyVersion')
    
    request_data = {
        "createFromVersion": from_version
    }
    
    # Try a few times with backoff
    for attempt in range(max_retries):
        try:
            response = session.post(url, json=request_data, params=params)
            
            if response.status_code in [201, 200]:
                break
            
            print(f"Attempt {attempt+1}/{max_retries}: Failed to create new property version: {response.status_code}")
            if response.text:
                print(response.text)
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"Error during API call: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    if response.status_code not in [201, 200]:
        return None
    
    version_data = response.json()
    new_version = version_data.get('versionLink', '').split('?')[0].split('/')[-1]
    
    if not new_version:
        try:
            # Different response format in some API versions
            new_version = version_data.get('versions', {}).get('items', [{}])[0].get('propertyVersion')
        except (KeyError, IndexError):
            print("Failed to extract new version number from response")
            return None
    
    return new_version

def update_property_via_api(property_names_file, logging_file, section_name="Logging - TrafficPeak", 
                            edgerc_file="~/.edgerc", edgerc_section="default", account_key=None):
    """
    Update the properties via Akamai API using property names
    """
    # Load the property names
    with open(property_names_file, 'r') as f:
        property_names = [line.strip() for line in f if line.strip()]
    
    # Load the logging section JSON
    with open(logging_file, 'r') as f:
        logging_json = json.load(f)
    
    # Setup EdgeGrid authentication
    edgerc_path = os.path.expanduser(edgerc_file)
    edgerc = EdgeRc(edgerc_path)
    section = edgerc_section
    
    # Create session with EdgeGrid auth
    session = requests.Session()
    session.auth = EdgeGridAuth(
        client_token=edgerc.get(section, 'client_token'),
        client_secret=edgerc.get(section, 'client_secret'),
        access_token=edgerc.get(section, 'access_token')
    )
    
    # Set the base URL
    base_url = f"https://{edgerc.get(section, 'host')}"
    
    success_count = 0
    failure_count = 0
    
    for property_name in property_names:
        print(f"\nProcessing property: {property_name}")
        
        # Find the property by name
        property_info = find_property_by_name(session, base_url, property_name, account_key)
        
        if not property_info:
            print(f"Could not find property information for {property_name}")
            failure_count += 1
            continue
        
        property_id = property_info.get('propertyId')
        property_version = property_info.get('propertyVersion')
        contract_id = property_info.get('contractId')
        group_id = property_info.get('groupId')
        
        print(f"Found property ID: {property_id}, version: {property_version}")
        
        # Create a new version of the property
        print(f"Creating a new version based on version {property_version}...")
        new_version = create_new_property_version(session, base_url, property_id, contract_id, group_id, account_key)
        
        if not new_version:
            print(f"Failed to create a new version for property {property_name}")
            failure_count += 1
            continue
        
        print(f"Created new version: {new_version}")
        
        # Get the rules for the new version
        rules_data = get_property_rules(session, base_url, property_id, new_version, contract_id, group_id, account_key)
        
        if not rules_data:
            print(f"Could not get rules for property {property_name} version {new_version}")
            failure_count += 1
            continue
        
        # Find and replace the logging section
        updated_rules, was_replaced = find_and_replace_logging_section(rules_data.get('rules', {}), logging_json)
        
        if not was_replaced:
            print(f"No section named '{section_name}' found in property {property_name}")
            failure_count += 1
            continue
        
        # Update the rules in the data
        rules_data['rules'] = updated_rules
        
        # API endpoint to update the property
        update_url = f"/papi/v1/properties/{property_id}/versions/{new_version}/rules"
        url = urljoin(base_url, update_url)
        
        # Prepare the request data - only send the rules object
        request_data = {
            "rules": rules_data['rules']
        }
        
        # Add query parameters
        params = {
            "contractId": contract_id,
            "groupId": group_id
        }
        
        if account_key:
            params["accountSwitchKey"] = account_key
        
        # Make the API request with retry logic
        success = False
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = session.put(url, json=request_data, params=params)
                
                if response.status_code == 200:
                    print(f"Successfully updated property {property_name} with new version {new_version} (no activation performed)")
                    success = True
                    break
                else:
                    print(f"Attempt {attempt+1}/{max_retries}: Failed to update property {property_name}: {response.status_code}")
                    if response.text:
                        print(response.text)
                    
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
            except Exception as e:
                print(f"Error during API call: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        if success:
            success_count += 1
        else:
            failure_count += 1
    
    print(f"\nSummary: {success_count} properties updated successfully, {failure_count} failures")
    return success_count > 0

def main():
    parser = argparse.ArgumentParser(description='Update Akamai Property logging section')
    parser.add_argument('property_file', help='Path to the file containing property names (one per line)')
    parser.add_argument('logging_file', help='Path to the new logging section JSON file')
    parser.add_argument('--output', '-o', help='Output file path (for local mode only)')
    parser.add_argument('--local', '-l', action='store_true', help='Run in local mode (no API calls)')
    parser.add_argument('--edgerc', default='~/.edgerc', help='Path to .edgerc file')
    parser.add_argument('--section', default='default', help='Section in .edgerc file')
    parser.add_argument('--account-key', help='Account switch key for API requests')
    
    args = parser.parse_args()
    
    if args.local:
        success = update_property_with_new_logging(
            args.property_file,
            args.logging_file,
            args.output
        )
    else:
        success = update_property_via_api(
            args.property_file, 
            args.logging_file,
            edgerc_file=args.edgerc,
            edgerc_section=args.section,
            account_key=args.account_key
        )
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()