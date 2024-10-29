# update a GTM property's JSON
# by Rafael Alvarez Rivero

import json, sys, os, requests, argparse
from akamai.edgegrid import EdgeGridAuth, EdgeRc
import urllib

edgerc_file_path = os.path.expanduser('~/.edgerc')
edgerc_object = EdgeRc(edgerc_file_path)
baseurl = 'https://' + edgerc_object.get('default', 'host')
r = requests.Session()
r.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')

def get_parameters():
	parser = argparse.ArgumentParser(description="Update weight of a target datacenter")
	parser.add_argument('-d', '--datacenter', required=True, help="Datacenter to update weight to")
	parser.add_argument('-D', '--domain', metavar='', help="GTM Domain")
	parser.add_argument('-P', '--property', metavar='', help="GTM Property")
	parser.add_argument('-w', '--weight', type=int, metavar='', help="DC new weight")
	args = parser.parse_args()
	return args

def get_domain_property(switchkey, dc):
	url_domains = baseurl + '/config-gtm/v1/domains' + '?accountSwitchKey=' + switchkey
	r_domains = r.get(url=url_domains)
	domains_json = r_domains.json()
	doms_props = []
	for domain in domains_json['items']:
		dom_name = domain['name']
		url_props = baseurl + '/config-gtm/v1/domains/' + dom_name + '/properties' + '?accountSwitchKey=' + switchkey
		r_properties = r.get(url=url_props)
		props_json = r_properties.json()
		for prop in props_json['items']:
			prop_name = prop['name']
			traffic_targets = prop['trafficTargets']
			for traffic_target in traffic_targets:
				if dc in str(traffic_target['handoutCName']):
					doms_props.append(dom_name)
					doms_props.append(prop_name)
					# print('Target exists in domain ' + dom_name + ' and property ' + prop_name)
	print (str(len(doms_props)))
	if len(doms_props) == 0:
		print(dc + ' not found in any GTM property')
	else:
		print("DC %s exists in the following domains-properties, call this program with domain and property parameters." % (dc))
		i = 0
		while i < len(doms_props):
			print("Domain: %s and Property: %s" % (doms_props[i], doms_props[i+1]))
			i += 2

def update_dc_weight(dom, pro, dac, nw, sk):
	api_property = '/config-gtm/v1/domains/' + dom + '/properties/' + pro + '?accountSwitchKey=' + sk
	url = baseurl + api_property
	r_property = r.get(url=url)
	property_json = r_property.json()
	for dcs in property_json['trafficTargets']:
		if dac in str(dcs['handoutCName']): 
			dcs['weight'] = nw
			#print(dcs['handoutCName'], dcs['weight'])
	print (json.dumps(property_json, indent=4))

def start_update():
	args = get_parameters()
	if args.domain and args.property:
		print("Updating %s in Domain %s, Property %s" % (args.datacenter, args.domain, args.property))
		update_dc_weight(args.domain, args.property, args.datacenter, args.weight, '1-14300Z9')
	if not args.domain and not args.property:
		try:
			get_domain_property('1-14300Z9', args.datacenter)
		except:
			print("Something went wrong fetching the data center")
			exit(1)

if __name__ == "__main__":
	start_update()