# report of what zones have ZAM configured
# by Rafael Alvarez Rivero

import requests, json, sys, os
from akamai.edgegrid import EdgeGridAuth,EdgeRc
import urllib

# from https://github.com/akamai/AkamaiOPEN-edgegrid-python
edgerc_file_path = os.path.expanduser('~/.edgerc')
edgerc_object = EdgeRc(edgerc_file_path)
baseurl = 'https://' + edgerc_object.get('default', 'host')

r = requests.Session()
r.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')

def get_akamaicdn_status():
	endpoint_zones = '/config-dns/v2/zones?showAll=true&accountSwitchKey=AANA-76YA50'
	url = baseurl + endpoint_zones
	response_1 = r.get(url=url)
	zones = response_1.json()

	for zone in zones['zones']:
		endpoint_type = '/config-dns/v2/zones/' + str(zone.get('zone'))\
							+ '/recordsets?types=AKAMAICDN&accountSwitchKey=AANA-76YA50'
		url_2 = baseurl + endpoint_type
		response_2 = r.get(url=url_2)
		zone_record = response_2.json()
		recordsets = zone_record['recordsets']
		if recordsets:
			for recordset in recordsets:
				zone_name = recordset['name']
				zone_type = recordset['type']
				edge_host = ''
				rdata_list = recordset['rdata']
				for edgekey in rdata_list:
					edge_host += ' ' + edgekey
				print ('{zn:35s} {zt:8s} {eh:40s}'.format(zn=zone_name, zt=zone_type, eh=edge_host))
		else:
			print(zone['zone'])
        
if __name__ == "__main__":
	get_akamaicdn_status()