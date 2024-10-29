### Written by Rafael Alvarez Rivero
### Last update: feb 2022
### Need to write code to check for nested GTM properties

import requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from urllib.parse import urljoin
import json,re, sys, os, datetime, time, urllib
from time import strftime

edgerc = EdgeRc('/Users/ralvarez/.edgerc')
section = 'default'
baseurl = 'https://%s' % edgerc.get(section, 'host')
s = requests.Session()
s.auth = EdgeGridAuth.from_edgerc(edgerc, section)

def getpropctraccId(id):
    return id[4:]

def showsummary(count_dictionary,config_dictionary): # Traverse the gtm property count dictionary
    print()
    for gtm_prop in count_dictionary:
        print("GTM property "+gtm_prop+" found "+str(count_dictionary[gtm_prop])+" times in these delivery files:")
        print(config_dictionary[gtm_prop])
        print()

def get_gtm_properties(accountSwitchKey): # Obtain the gtm properties and assemble them in a property.domain format
    domains_endpoint = '/config-gtm/v1/domains'
    domurl = urljoin(baseurl, domains_endpoint)
    params = {'accountSwitchKey': accountSwitchKey}
    dom_result = s.get(domurl,params=params)
    domains = dom_result.json()
    prop_dictionary = {} # gtm property as key and count as value
    prop_dictionary2 = {} # gtm property as key and properties where it exists in as value

    try:
        for gtmdomain in domains['items']: 
            propurl = baseurl+'/config-gtm/v1/domains/'+gtmdomain['name']+'/properties?accountSwitchKey='+accountSwitchKey
            prop_result = s.get(propurl,params=params)
            prop_body = prop_result.json()
            for prop in prop_body['items']:
                prop_name = str(prop['name'])+"."+str(gtmdomain['name']) # property.domain format
                prop_dictionary[prop_name] = 0
                prop_dictionary2[prop_name] = ""
        return prop_dictionary, prop_dictionary2
    except:
        print("An error occurred while attempting to get the GTM properties initialized")
        sys.exit(1)

def getProperties(accountSwitchKey,contractid,groupid):
    properties_path = '/papi/v1/properties'
    params = {'accountSwitchKey': accountSwitchKey,'groupId': groupid,'contractId': contractid}
    fullurl = urljoin(baseurl, properties_path)
    result = s.get(fullurl,params=params)
    body = result.json()
    if len(body['properties']['items']) != 0:
        return body['properties']['items']
    else:
        temp = {}
        return temp

def fetchRuleTreeandSearch(accountSwitchKey,property_list,count_dictionary,config_dictionary):
    config_dict = {}
    config_dict_propnames = {}
    # fill up two dictonaries with all the property ids and names for a given set of group and contract ids
    for i in property_list:
        propname = i['propertyName']
        propid = getpropctraccId(i['propertyId'])
        grpid = getpropctraccId(i['groupId'])
        ctrid =getpropctraccId(i['contractId'])
        rule_tree_path = "/papi/v0/properties/"+str(propid)+"/versions/"+str(i["productionVersion"])+"/rules"
        params = {'accountSwitchKey': accountSwitchKey,'contractId': i['contractId'],'groupId': i['groupId']}
        fullurl = urljoin(baseurl, rule_tree_path)
        result = s.get(fullurl, params=params)
        body = result.json()
        config_dict_propnames[propid] = propname
        config_dict[propid] = json.dumps(body)
       
    for key_gtm_prop in count_dictionary:
        count = 0
        for prop_id in config_dict:
            propjson = config_dict[prop_id]
            if key_gtm_prop in propjson:
                count_dictionary[key_gtm_prop] = count_dictionary[key_gtm_prop] + 1
                if config_dictionary[key_gtm_prop] == "":
                    config_dictionary[key_gtm_prop] = config_dict_propnames[prop_id]
                else:
                    config_dictionary[key_gtm_prop] = config_dictionary[key_gtm_prop]+", "+config_dict_propnames[prop_id]
                count += 1

def main(accountSwitchKey):
    headers = {'Content-Type': 'application/json'}
    params = {'accountSwitchKey': accountSwitchKey}
    path = '/papi/v1/groups/'
    fullurl = urljoin(baseurl, path)
    result = s.get(fullurl,params=params)
    body = result.json()
    global count_dictionary
    global config_dictionary
    count_dictionary, config_dictionary = get_gtm_properties(accountSwitchKey)

    for groupitem in body['groups']['items']:
        for contractID in groupitem['contractIds']:
            property_list = getProperties(accountSwitchKey,contractID,groupitem['groupId'])
            print(str(len(property_list)))
            if len(property_list) != 0:
                fetchRuleTreeandSearch(accountSwitchKey,property_list,count_dictionary,config_dictionary)
    
    showsummary(count_dictionary,config_dictionary)

if __name__=="__main__":
    accountSwitchKey = sys.argv[1]
    print("=============================================")
    print("Searching all the configs in the account.....")
    print("=============================================")
    main(accountSwitchKey)