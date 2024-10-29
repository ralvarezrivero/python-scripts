# ralvarez 2024

import argparse, string
import json, sys, os, requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
import urllib
from urllib.parse import urljoin
import dns.resolver

# define the parameters that are the inputs for this program
def get_parameters():

    parser = argparse.ArgumentParser()
    parser.add_argument('-e',help='edgerc path',dest='edgerc_file',default='~/.edgerc')
    parser.add_argument('-a',help='account switch key',required=True,dest='switch_key')
    parser.add_argument('-s',help='Slot number',required=True,dest='slot')
    parser.add_argument('-sec',help='section',dest='section',default='default')
    all_args=parser.parse_args()

    return all_args

# ==>>>>>>> START PROGRAM <<<<<<<==

args=get_parameters()

# set the request's object information
edgerc_file_path = os.path.expanduser(args.edgerc_file)
edgerc_object = EdgeRc(edgerc_file_path)
baseurl = 'https://' + edgerc_object.get(args.section, 'host')
r = requests.Session()
r.auth = EdgeGridAuth.from_edgerc(edgerc_object, args.section)

# get all property ids from groups and contracts API

properties=[]

headers = {'Content-Type': 'application/json'}
params = {'accountSwitchKey': args.switch_key}
path = '/papi/v1/hostnames/'
fullurl = urljoin(baseurl, path)
result = r.get(fullurl,params=params)
body = result.json()

print('WORKING WITH SLOT NUMBER: {}'.format(args.slot))

for hostname in body['hostnames']['items']:
    network=''
    if "productionCnameTo" in hostname:
        network="production"
    if "stagingCnameTo" in hostname:
        network="staging"
    try:
        answer=dns.resolver.resolve(hostname['cnameFrom'],'CNAME')
        cname=''
        for rdata in answer:
            #print('{} CNAMEs to: {}'.format(hostname['cnameFrom'],rdata.target))
            cname=str(rdata.target)
        if "edgekey" in cname:
            #print('{} is an edgekey hostname'.format(cname))
            answer2=dns.resolver.resolve(cname,'CNAME')
            for rdata2 in answer2:
                #print('Edgekey {} resolves to {}'.format(cname,rdata2.target))
                cname2=str(rdata2.target)
                if args.slot in cname2:
                    print('Network: {} -> hostname {} is CNAMED to {} in property {}'.format(network,hostname['cnameFrom'],cname,hostname['propertyName']))
    except:
        logger='{} no DNS record found'.format(hostname['cnameFrom'])