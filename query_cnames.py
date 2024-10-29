import dns.resolver, requests, json, sys, os
from akamai.edgegrid import EdgeGridAuth,EdgeRc
import urllib

edgerc_file_path = os.path.expanduser('~/.edgerc')
edgerc_object = EdgeRc(edgerc_file_path)
baseurl = 'https://' + edgerc_object.get('default', 'host')

r = requests.Session()
r.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')

# api_enr = baseurl + '/cps/v2/enrollments?contractId=ctr_C-IXCOB3&accountSwitchKey=EP-2LU'
api_enr = baseurl + '/papi/v1/contracts?accountSwitchKey=1-AITJY'

print(api_enr)

response = r.get(url=api_enr)
enrollments_json = response.json()

print(json.dumps(enrollments_json, indent=3))

# for enrollment in enrollments_json['enrollments']:
# 	print (enrollment['location'])

# answer = dns.resolver.query('www.discover.com', 'CNAME')
# for rdata in answer:
# 	print (rdata)


	