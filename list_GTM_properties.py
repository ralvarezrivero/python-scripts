# list properties for all domains
# by Rafael Alvarez Rivero

import json, sys, os, requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
import urllib

def list_properties():
	api_domains = '/config-gtm/v1/domains'
	switchkey = sys.argv[1]
	#api_property = '/config-gtm/v1/domains/' + domain + '/properties/' + prop + '?accountSwitchKey=' + switchkey 

	edgerc_file_path = os.path.expanduser('~/.edgerc')
	edgerc_object = EdgeRc(edgerc_file_path)
	baseurl = 'https://' + edgerc_object.get('default', 'host')
	url = baseurl + api_domains + '?accountSwitchKey=' + switchkey

	get_domains = requests.Session()
	get_domains.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')
	request_domains = get_domains.get(url=url)
	domains_json = json.loads(request_domains.text)

	domain_count = 1

	for domain in domains_json['items']:
		print(str(domain_count) + ': ' + domain['name'])
		domain_count += 1
		domain_name = domain['name']
		api_property = '/config-gtm/v1/domains/' + domain_name + '/properties' + '?accountSwitchKey=' + switchkey
		property_url = baseurl + api_property
		get_properties = requests.Session()
		get_properties.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')
		request_properties = get_properties.get(url=property_url)

		properties_json = json.loads(request_properties.text)
		#print(json.dumps(properties_json, indent=3))

		for prop in properties_json['items']:
			print('  ' + prop['name'])
		print('  ')

if __name__ == "__main__":	
	list_properties()