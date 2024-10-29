import argparse, string
import json, sys, os, requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
import urllib
import csv
import pandas as pd

################### BEGIN DEFINE FUNCTIONS ##########

# define the parameters that are the inputs for this program
def get_parameters():

    parser = argparse.ArgumentParser()
    parser.add_argument('-e',help='edgerc path',dest='edgerc_file',default='~/.edgerc')
    parser.add_argument('-a',help='account switch key',required=True,dest='switch_key')
    parser.add_argument('-s',help='section',dest='section',default='default')
    parser.add_argument('-f',help='csv file',required=True,dest='csvfile')
    parser.add_argument('-v',help='API Version',required=True,dest='api_version')
    parser.add_argument('-i',help='Endpoint ID',required=True,dest='ep_id')
    parser.add_argument('-n',help='Activation Network',required=True,dest='act_network')
    all_args=parser.parse_args()

    return all_args

# create a resource as the first step
def create_res(req_obj,baseurl,endpoint,version,row,skey):

    create_res_url=baseurl+'/api-definitions/v2/endpoints/'+endpoint+'/versions/'+version+'/resources'

    resname=datafr.loc[row,'apiResourceName']
    resmethod=datafr.loc[row,'apiResourceMethod']
    respath=datafr.loc[row,'resourcePath']
    respurp=datafr.loc[row,'Purpose']
    resmethods = {
                "apiResourceMethod": resmethod
            }
    if respurp == "LOGIN":
        paramLocation = (datafr.loc[row,'paramlocation'])
        paramName = (datafr.loc[row,'paramname'])
        isRequired = (datafr.loc[row,'isrequired'])
        paramType = (datafr.loc[row,'paramtype'])
        resmethods={
                  "apiParameters": [
                    {
                      "apiParameterLocation": (paramLocation),
                      "apiParameterRequired": False,
                      "apiParameterRestriction": {
                        "arrayRestriction": {
                          "collectionFormat": "csv"
                        },
                        "xmlConversionRule": {
                          "attribute": False,
                          "wrapped": False
                        }
                      },
                      "apiParameterType": "string",
                      "apiParameterName": (paramName)
                    }
                  ],
                  "apiResourceMethod": (resmethod)
                }

    payload = {
        "apiResourceMethods": [
            resmethods
        ],
        "apiResourceName": resname,
        "resourcePath": respath,
        "description": "Purpose: "+respurp
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    querystring = {
        "accountSwitchKey": skey
    }
    #print(json.dumps(payload,indent=4))
    try:
        response=req_obj.post(create_res_url,json=payload,params=querystring)
        res_resp=response.json()
        return res_resp['apiResourceId']
    except:
        print(res_resp['detail'])

# after creating the resources, create API operations with these resources
def create_operators(req_obj,baseurl,endpoint,version,skey):
    for row in range(len(datafr)):
      create_op_url=baseurl+'/api-definitions/v2/endpoints/'+endpoint+'/versions/'+version+'/resources/'\
        +str(datafr.loc[row,'resourceId'])+'/operations'
      CreateAPIOperator = {
            "method": datafr.loc[row,'apiResourceMethod'],
            "operationPurpose": datafr.loc[row,'Purpose'],
            "apiResourceId": int(datafr.loc[row,'resourceId']),
            "operationName": datafr.loc[row,'apiResourceName']
      }
      querystring = {
        "accountSwitchKey": skey
      }
      response=req_obj.post(create_op_url,json=CreateAPIOperator,params=querystring)
      op_resp=response.json()
      print(json.dumps(op_resp,indent=4))
      if "resOperation" in datafr.columns:
          datafr.loc[row,'resOperation']=op_resp['operationId']
      else:
          datafr.insert(row,"resOperation",op_resp['operationId'])

################### START PROGRAM ###################

args=get_parameters()

# set the request's object information
edgerc_file_path = os.path.expanduser(args.edgerc_file)
edgerc_object = EdgeRc(edgerc_file_path)
baseurl = 'https://' + edgerc_object.get(args.section, 'host')
r = requests.Session()
r.auth = EdgeGridAuth.from_edgerc(edgerc_object, args.section)

# declaring our dataframe global
# this datafr will have all the information necessary in memory
global datafr
datafr=pd.read_csv(args.csvfile)

for row in range(len(datafr)):
  print('Creating resource: {}'.format(datafr.loc[row,'apiResourceName']))
  resId=create_res(r,baseurl,args.ep_id,args.api_version,row,args.switch_key) 
  if "resourceId" in datafr.columns:
      datafr.loc[row,'resourceId']=resId
  else:
      datafr.insert(row,"resourceId", resId)

create_operators(r,baseurl,args.ep_id,args.api_version,args.switch_key)
    
print(datafr)



# push to staging
# check if version of staging is the one we created

# create the api definition
