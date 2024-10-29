# get the zone file for all zones in an account - DFS
# by Rafael Alvarez Rivero

import requests, json, sys, os, urllib
from akamai.edgegrid import EdgeGridAuth, EdgeRc


def show_all_zone_records():
    endpoint_get_zones='/config-dns/v2/zones?showAll=true'
    SwitchKey = 'accountSwitchKey=1-14300Z9'

    # from https://github.com/akamai/AkamaiOPEN-edgegrid-python
    edgerc_file_path = os.path.expanduser('~/.edgerc')
    edgerc_object = EdgeRc(edgerc_file_path)
    baseurl = 'https://' + edgerc_object.get('default', 'host')
    url = baseurl + endpoint_get_zones + '&' + SwitchKey

    r = requests.Session()
    r.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')

    response1 = r.get(url=url)
    zones = json.loads(response1.text)

    for zone in zones['zones']:
        endpoint_zone_record = '/config-dns/v2/zones/' + str(zone.get('zone')) + '/zone-file?' + SwitchKey
        url2 = baseurl + endpoint_zone_record
        header = {'Content-type': 'text/dns'}

        r2 = requests.Session()
        r2.auth = EdgeGridAuth.from_edgerc(edgerc_object, 'default')

        master_response = r2.get(url=url, headers=header)

        first_record = master_response.json()
        print (json.dumps(first_record['zone']))

if __name__ == "__main__":
    show_all_zone_records()