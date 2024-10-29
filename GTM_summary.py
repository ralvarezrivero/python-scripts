# list targets for all properties in Traffic Mgmt
# by Rafael Alvarez Rivero

import json, sys, os, requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
import urllib

edgerc_file_path = os.path.expanduser('~/.edgerc')
edgerc_object = EdgeRc(edgerc_file_path)
baseurl = 'https://' + edgerc_object.get('default', 'host')
r = requests.Session()
r.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')

def get_domain_property(switchkey):
	url_domains = baseurl + '/config-gtm/v1/domains' + '?accountSwitchKey=' + switchkey
	r_domains = r.get(url=url_domains)
	domains_json = r_domains.json()
	target_found = False

	for domain in domains_json['items']:
		print(domain['name'])
		dom_name = domain['name']
		url_props = baseurl + '/config-gtm/v1/domains/' + dom_name + '/properties' + '?accountSwitchKey=' + switchkey
		r_properties = r.get(url=url_props)
		props_json = r_properties.json()

		for prop in props_json['items']:
			prop_name = prop['name']
			print('   ' + prop_name)
			traffic_targets = prop['trafficTargets']

			targets = ''
			for traffic_target in traffic_targets:
				targets += str(traffic_target['handoutCName']) + ' '
			print('      ' + targets)
			print('')

if __name__ == "__main__":
	get_domain_property('1-14300Z9')