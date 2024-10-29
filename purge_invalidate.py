# invalidating by CP Code
# by Rafael Alvarez Rivero

import requests, json, sys, os
from akamai.edgegrid import EdgeGridAuth,EdgeRc
import urllib

def invalidate_cp_code():
	cp_code = str(sys.argv[1])
	# from https://github.com/akamai/AkamaiOPEN-edgegrid-python
	edgerc_file_path = os.path.expanduser('~/.edgerc')
	edgerc_object = EdgeRc(edgerc_file_path)
	baseurl = 'https://' + edgerc_object.get('ccu', 'host')
	url = baseurl + '/ccu/v3/invalidate/cpcode/staging'
	payload = json.loads('{ "objects" : [ ' + cp_code + ' ] }')
	print(payload)
	header = {'Content-type': 'application/json'}

	r = requests.Session()
	r.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'ccu')

	print(url)
	response = r.post(url=url, json=payload, headers=header)
 
	print (json.dumps(response.json(), indent=3))

	return()
        
if __name__ == "__main__":
	invalidate_cp_code()
