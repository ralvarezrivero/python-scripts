import argparse, string
import json, sys, os, requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from datetime import datetime, timedelta, date
import urllib
from collections import OrderedDict

################### BEGIN DEFINE FUNCTIONS ##########

#### yet another datetime rounder to mignight to use with Akamai APIs
def set_to_midnight(dt):
    midnight = datetime.time(0)
    return datetime.datetime.combine(dt.date(), midnight)

#### function to return an object with parameters
def get_parameters():

    # add default values -> FROM STUART
    parser = argparse.ArgumentParser()
    parser.add_argument('-e',help='edgerc path',dest='edgerc_file',default='~/.edgerc')
    parser.add_argument('-a',help='account switch key',dest='switch_key')
    parser.add_argument('-s',help='section',dest='section',default='default')
    parser.add_argument('-f',help='property file name',required=True,dest='filename')
    all_args=parser.parse_args()

    return all_args

#### search for a property
def search_property(req_obj, baseurl, prop, skey):

    payload=json.loads('{"propertyName": "'+prop+'"}')
    headers = {
        "accept": "application/json",
        "PAPI-Use-Prefixes": "false",
        "content-type": "application/json"
    }
    search_url = baseurl+'/papi/v1/search/find-by-value?accountSwitchKey='+skey
    try:
        response = req_obj.post(search_url, json=payload, headers=headers)
        prop_versions=response.json()
        if prop_versions['versions']['items']:
            for prop_ver in prop_versions['versions']['items']:
                if prop_ver['productionStatus'] == "ACTIVE":
                    return prop_ver['propertyId'],prop_ver['propertyVersion']
    except:
        print('Error searching for property '+prop)
        # do not exit the entire script if one property failed to be found
        sys.exit(1)

#### with a given property, get the json to get the CP Code and call reporting APIs
def set_cpcode_dict(req_obj, baseurl, prop_id, prop_ver, skey, results_dict):

    # start by getting the property json file for that version
    headers = {
        "Accept": "application/json",
        "PAPI-Use-Prefixes": "false"
    }
    querystring = {"accountSwitchKey": skey}    
    prop_url=baseurl+'/papi/v1/properties/'+str(prop_id)+'/versions/'+str(prop_ver)+'/rules'
    
    try:
        response=req_obj.get(prop_url, headers=headers, params=querystring)
        prop_json=response.json()
        for behavior in prop_json['rules']['behaviors']:
            if behavior['name'] == 'cpCode':
                default_cpcode = (behavior['options']['value']['id'])
        if not default_cpcode:
            for behavior in prop_json['rules']['children'][0]['children'][0]['behavior']:
                if behavior['name'] == 'cpCode':
                    default_cpcode = (behavior['options']['value']['id'])
        
        results_dict.append(default_cpcode)
        return results_dict
    except:
        print('Could not initialize cpcode json dictionary')
        sys.exit(1)

#### overall hits result
def get_overall_hits(req_obj,baseurl,date_now_iso,date_14d_ago_iso,cpcode,skey):

    hits_url=baseurl+'/reporting-api/v1/reports/hits-by-time/versions/1/report-data'
    headers = {'content-type': 'application/json'}
    querystring = {
        "start": str(date_14d_ago_iso),
        "end": str(date_now_iso),
        "objectIds": cpcode,
        "metrics": 'edgeHitsTotal',
        "interval": 'HOUR',
        "accountSwitchKey": skey
    }
    try:
        response=req_obj.get(hits_url,headers=headers,params=querystring)
        r_json=response.json()
        return int(r_json['summaryStatistics']['edgeHitsTotal']['value'])
    except:
        print('Error getting overall hits report')
        sys.exit(1)

#### overall bytes result
def get_overall_bytes(req_obj,baseurl,date_now_iso,date_14d_ago_iso,cpcode,skey):

    hits_url=baseurl+'/reporting-api/v1/reports/bytes-by-time/versions/1/report-data'
    headers = {'content-type': 'application/json'}
    querystring = {
        "start": str(date_14d_ago_iso),
        "end": str(date_now_iso),
        "objectIds": cpcode,
        "metrics": 'edgeBytesTotal',
        "interval": 'HOUR',
        "accountSwitchKey": skey
    }
    try:
        response=req_obj.get(hits_url,headers=headers,params=querystring)
        r_json=response.json()
        return int(r_json['summaryStatistics']['edgeBytesTotal']['value'])
    except:
        print('Error getting overall bytes report')
        print(response.text)
        sys.exit(1)

#### hits by url
def hits_by_url(req_obj,baseurl,cpcode,skey):

    today=date.today()
    d14_ago=today - timedelta(days=14)
    today_str=str(today)+'T00:00:00'
    d14_ago_str=str(d14_ago)+'T00:00:00'
    hits_url=baseurl+'/reporting-api/v1/reports/urlhits-by-url/versions/1/report-data'
    headers = {'content-type': 'application/json'}
    querystring = {
        "start": d14_ago_str,
        "end": today_str,
        "objectIds": cpcode,
        "metrics": 'allEdgeHits',
        "limit": 20,
        "accountSwitchKey": skey
    }
    try:
        response=req_obj.get(hits_url,headers=headers,params=querystring)
        r_json=response.json()
        return r_json['data']
    except:
        print('Error getting top url hits report')
        print(response.text)
        sys.exit(1)

#### top 4xx URLs
def top_4xx(req_obj,baseurl,cpcode,skey):

    today=date.today()
    d14_ago=today - timedelta(days=14)
    today_str=str(today)+'T00:00:00'
    d14_ago_str=str(d14_ago)+'T00:00:00'
    hits_url=baseurl+'/reporting-api/v1/reports/urlresponses-by-url/versions/1/report-data'
    headers = {'content-type': 'application/json'}
    querystring = {
        "start": d14_ago_str,
        "end": today_str,
        "objectIds": cpcode,
        "metrics": '4XXEdgeHits',
        "limit": 5,
        "accountSwitchKey": skey
    }
    try:
        response=req_obj.get(hits_url,headers=headers,params=querystring)
        r_json=response.json()
        return r_json['data']
    except:
        print('Error getting top 4xx URLs')
        print(response.text)
        sys.exit(1)

#### round time for the over-complicated Akamai report APIs
def rounder(t):
    return t.replace(second=0, microsecond=0, minute=0)

################### END DEFINE FUNCTIONS ############

################### START PROGRAM ###################

start_time = datetime.now()

args=get_parameters()

if args.switch_key:
    s_key=args.switch_key
else:
    print('Trying to get the switch key from env var')
    try:
        s_key=os.environ['AKAMAI_ACCOUNT_KEY']
    except:
        print('Switch Key in the environment is empty')
        sys.exit(1)

# set the request's object information
edgerc_file_path = os.path.expanduser(args.edgerc_file)
edgerc_object = EdgeRc(edgerc_file_path)
baseurl = 'https://' + edgerc_object.get(args.section, 'host')
r = requests.Session()
r.auth = EdgeGridAuth.from_edgerc(edgerc_object, args.section)

# open file to get the properties to search for
with open(args.filename) as prop_file:
    a_properties = prop_file.readlines()

# start working by getting the propertyId and propertyVersion
results_dict = []
for prop in a_properties:
    print("Working with property: "+prop.strip())
    prop_id,prop_ver=search_property(r, baseurl,prop.strip(),s_key)
    if prop_id: # if there is a propertyId to use
        results_dict=set_cpcode_dict(r, baseurl, prop_id, prop_ver, s_key, results_dict)

# generate the date and time to use in the report APIs
date_now=rounder(datetime.now())
date_now_iso=date_now.isoformat(timespec='seconds')
date_14d_ago=date_now - timedelta(days=14)
date_14d_ago_iso=date_14d_ago.isoformat(timespec='seconds') 
print('Getting stats from '+date_14d_ago_iso+' to '+date_now_iso)

print(results_dict)
results_dict=list(set(results_dict))
print(results_dict)

report_dict={"cpcodes":[]}
# traverse the cpcodes object and fill it with the report API information
for i, cpcode in enumerate(results_dict):
    hits=get_overall_hits(r,baseurl,date_now_iso,date_14d_ago_iso,cpcode,s_key)
    bytes=get_overall_bytes(r,baseurl,date_now_iso,date_14d_ago_iso,cpcode,s_key)
    top_urls=hits_by_url(r,baseurl,cpcode,s_key)
    top_4xx_urls=top_4xx(r,baseurl,cpcode,s_key)
    report_dict['cpcodes'].append({'cpcode': cpcode})
    report_dict['cpcodes'][i]['HitsTotal']=hits
    report_dict['cpcodes'][i]['BytesTotal']=bytes
    report_dict['cpcodes'][i]['TopURLs']=top_urls
    report_dict['cpcodes'][i]['Top4xxURLs']=top_4xx_urls
    
print(json.dumps(report_dict, indent=4))

# save the json to a file
with open('stats_assessment.json', 'w') as f:
    json.dump(report_dict, f, indent=4)

end_time = datetime.now()

print('Duration: {}'.format(end_time - start_time))

