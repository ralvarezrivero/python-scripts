# list properties for all domains
# filter by pre2023SecurityPosture = true (inside livenessTests)
# by Rafael Alvarez Rivero

import json, sys, os, requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc

def list_properties():
	api_domains = '/config-gtm/v1/domains'
	switchkey = sys.argv[1]

	edgerc_file_path = os.path.expanduser('~/.edgerc')
	edgerc_object = EdgeRc(edgerc_file_path)
	baseurl = 'https://' + edgerc_object.get('default', 'host')
	url = baseurl + api_domains + '?accountSwitchKey=' + switchkey

	get_domains = requests.Session()
	get_domains.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')
	request_domains = get_domains.get(url=url)
	domains_json = json.loads(request_domains.text)

	domain_count = 1
	matched = []

	for domain in domains_json['items']:
		domain_name = domain['name']
		print(f'Checking domain {domain_count}: {domain_name}...')

		api_property = '/config-gtm/v1/domains/' + domain_name + '/properties' + '?accountSwitchKey=' + switchkey
		property_url = baseurl + api_property

		get_properties = requests.Session()
		get_properties.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')
		headers = {'Accept': 'application/vnd.config-gtm.v1.6+json'}
		request_properties = get_properties.get(url=property_url, headers=headers)

		properties_json = json.loads(request_properties.text)

		if 'items' not in properties_json:
			print(f'  [skipped {domain_name} - unexpected response: {properties_json}]')
			domain_count += 1
			continue

		prop_count = len(properties_json['items'])
		print(f'  Found {prop_count} properties, scanning...')

		domain_printed = False
		for prop in properties_json['items']:
			liveness_tests = prop.get('livenessTests', [])
			has_flag = any(lt.get('pre2023SecurityPosture') == True for lt in liveness_tests)
			if has_flag:
				if not domain_printed:
					print(f'  [MATCH] {domain_name}')
					domain_printed = True
				print('    - ' + prop['name'])
				matched.append({'domain': domain_name, 'property': prop['name']})

		if not domain_printed:
			print(f'  No matches.')

		print()
		domain_count += 1

	print('---')
	print(f'Total properties with pre2023SecurityPosture=true: {len(matched)}')

if __name__ == "__main__":
	list_properties()