# get the zone file for all zones in an account
# by Rafael Alvarez Rivero

import requests, json, sys, os, urllib
from akamai.edgegrid import EdgeGridAuth, EdgeRc

def show_all_zone_record():
    endpoint_get_zones='/config-dns/v2/zones?showAll=true'

    # from https://github.com/akamai/AkamaiOPEN-edgegrid-python
    edgerc_file_path = os.path.expanduser('~/.edgerc')
    edgerc_object = EdgeRc(edgerc_file_path)
    baseurl = 'https://' + edgerc_object.get('default', 'host')
    url = baseurl + endpoint_get_zones + 'accountSwitchKey=1-14300Z9'

    r.requests.Session()
    r.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')

    response1 = r.get(url=url)
    zones = json.loads(response1.text)

    for zone in zones['zone']
        print (zone)

if __main__ == "__main__"
    show_all_zone_records()