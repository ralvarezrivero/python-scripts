# report of what zones have ZAM configured
# by Rafael Alvarez Rivero

import requests, json, sys, os
from akamai.edgegrid import EdgeGridAuth,EdgeRc
import urllib

def get_akamaicdn_status():
	endpoint_zones = '/config-dns/v2/zones?showAll=true&###'

	# from https://github.com/akamai/AkamaiOPEN-edgegrid-python
	edgerc_file_path = os.path.expanduser('~/.edgerc')
	edgerc_object = EdgeRc(edgerc_file_path)
	baseurl = 'https://' + edgerc_object.get('default', 'host')
	url = baseurl + endpoint_zones

	r = requests.Session()
	r.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')

	response_1 = r.get(url=url)
	zones = json.loads(response_1.text)

	for zone in zones['zones']:
		endpoint_type = '/config-dns/v2/zones/' + str(zone.get('zone')) + '/recordsets?types=AKAMAICDN&#####'
		url_2 = baseurl + endpoint_type
		response_2 = r.get(url=url_2)
		recordset = json.loads(response_2.text)
		recordset = recordset['recordsets']
		if recordset:
			for record in recordset:
				zone_name = record.get('name')
				zone_type = record.get('type')
				zone_edge = record.get('rdata')
				zone_type_string = ' '
				for zone_type_1 in zone_edge:
					zone_type_string += zone_type_1
				print (zone_name + ' ' + zone_type + ' ' + zone_type_string)
		else:
			print (zone.get('zone'))
        
if __name__ == "__main__":
	get_akamaicdn_status()