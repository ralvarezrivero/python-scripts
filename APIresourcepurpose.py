import requests 
from akamai.edgegrid import EdgeRc, EdgeGridAuth
import pandas as pd
import json

session = requests.Session()
edgerc = EdgeRc('~/.edgerc')
section = 'default'
hostname = edgerc.get(section, 'host')
session.auth = EdgeGridAuth.from_edgerc(edgerc, section)

csvfile = ("/home/aaron/BOTMANPROJECT/FILES/ResourcesNames.csv")
df = pd.read_csv(csvfile)
print(df) 
row, col = df.shape
Loop_limit = (row)

with open('/home/aaron/BOTMANPROJECT/FILES/OPERATORIDS.txt', 'w') as f:

    for row_counter in range(Loop_limit):
        resourcename = (df.iloc[row_counter,1])
        resourcemethod = (df.iloc[row_counter,0])
        resourcepath = (df.iloc[row_counter,2])
        resourcepurpose = (df.iloc[row_counter,3])

        if resourcepurpose=="LOGIN":

            paramLocation = (df.iloc[row_counter,5])
            paramName = (df.iloc[row_counter,6])
            isRequired = (df.iloc[row_counter,7])
            paramType = (df.iloc[row_counter,8])

            CreateAPIResource={
  "apiResourceMethods": [
    {
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
      "apiResourceMethod": (resourcemethod)
    }
  ],
  "apiResourceName": (resourcename),
  "description": "FROM API",
  "resourcePath": (resourcepath)
}
            payload = CreateAPIResource
            params = {
        'accountSwitchKey':'B-F-F2JX4L:1-8BYUX'
        }
            print(CreateAPIResource)
            response = session.post('https://' + hostname + '/api-definitions/v2/endpoints/845900/versions/18/resources', json=payload, params=params)
            jsonresponse = response.json()
            json_formatted_str = json.dumps(jsonresponse, indent=2)
            print(json_formatted_str)
            apiresourceid = (jsonresponse['apiResourceId'])
            print(apiresourceid)
            apiparamid =  (jsonresponse['apiResourceMethods'][0]['apiParameters'][0]['apiParameterId'])
            print(apiparamid)
            CreateAPIOperator = {
            "method": (resourcemethod),
            "operationPurpose": (resourcepurpose),
            "apiResourceId": (apiresourceid),
            "operationName": (resourcename),
            "apiResourceId": (apiresourceid),
            "operationName": (resourcename),
            "usernameParameterId": (apiparamid)
            }
    #   print(CreateAPIOperator)
            apiresourceid_as_a_str = str(apiresourceid)
            Path = '/api-definitions/v2/endpoints/845900/versions/18/resources/' + apiresourceid_as_a_str + '/operations'
    #   print (Path)
            payload = CreateAPIOperator
            response = session.post('https://' + hostname + Path, json=payload, params=params)
            jsonresponse = response.json()
            json_formatted_str = json.dumps(jsonresponse, indent=2)
            print(json_formatted_str)
############################################SAVEOPERATORID##############################################
            operatorid = (jsonresponse['operationId'])
            print(operatorid)
            f.write("%s\n" % operatorid)

        else:

            CreateAPIResource = {
        "apiResourceMethods": [
            {
            "apiResourceMethod": (resourcemethod)
            }
        ],
        "apiResourceName": (resourcename),
        "description": "Created with API call",
        "resourcePath": (resourcepath)
        }
    
            print(CreateAPIResource)

            payload = CreateAPIResource
            params = {
        'accountSwitchKey':'B-F-F2JX4L:1-8BYUX'
        }
#########################################CREATEOPERATORID#########################################
            response = session.post('https://' + hostname + '/api-definitions/v2/endpoints/845900/versions/18/resources', json=payload, params=params)
            jsonresponse = response.json()
            json_formatted_str = json.dumps(jsonresponse, indent=2)
            print(json_formatted_str)
            apiresourceid = (jsonresponse['apiResourceId'])
            print(apiresourceid)

            CreateAPIOperator = {
            "method": (resourcemethod),
            "operationPurpose": (resourcepurpose),
            "apiResourceId": (apiresourceid),
            "operationName": (resourcename),
            "apiResourceId": (apiresourceid),
            "operationName": (resourcename)
            }
    #   print(CreateAPIOperator)
            apiresourceid_as_a_str = str(apiresourceid)
            Path = '/api-definitions/v2/endpoints/845900/versions/18/resources/' + apiresourceid_as_a_str + '/operations'
    #   print (Path)
            payload = CreateAPIOperator
            response = session.post('https://' + hostname + Path, json=payload, params=params)
            jsonresponse = response.json()
            json_formatted_str = json.dumps(jsonresponse, indent=2)
            print(json_formatted_str)
############################################SAVEOPERATORID##############################################
            operatorid = (jsonresponse['operationId'])
            print(operatorid)
            f.write("%s\n" % operatorid)

        ##Push to staging
        ###Loop de check
        ###api def
        ####create endpoints