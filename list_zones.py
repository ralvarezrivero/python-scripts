import requests, json, sys, os
from akamai.edgegrid import EdgeGridAuth, EdgeRc
import urllib

edgerc_file_path = os.path.expanduser('~/.edgerc')
edgerc_object = EdgeRc(edgerc_file_path)
baseurl = 'https://' + edgerc_object.get('default', 'host')
endpoint = "/config-dns/v2/zones?showAll=true&accountSwitchKey=1-14300Z9"

r = requests.Session()
r.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')
response1 = r.get(baseurl + endpoint)
zones = json.loads(response1.text)

zone_array = {"zones": []}

for zone in zones['zones']:
	zone_array['zones'].append(zone['zone'])

print(json.dumps(zone_array, indent=2))

endpoint_transfer_status = "/config-dns/v2/zones/zone-transfer-status?accountSwitchKey=1-14300Z9"
header = {'Content-Type': 'application/json'}
response2 = r.post(url = baseurl + endpoint_transfer_status, json=zone_array, headers=header)

print(response2.text)