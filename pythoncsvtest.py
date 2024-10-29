import requests 
from akamai.edgegrid import EdgeRc, EdgeGridAuth
import pandas as pd

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

        response = session.post('https://' + hostname + '/api-definitions/v2/endpoints/845900/versions/16/resources', json=payload, params=params)
        jsonresponse = response.json()
        print(jsonresponse)
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
        print(CreateAPIOperator)
        apiresourceid_as_a_str = str(apiresourceid)
        Path = '/api-definitions/v2/endpoints/845900/versions/16/resources/' + apiresourceid_as_a_str + '/operations'
        print (Path)
        payload = CreateAPIOperator
        response = session.post('https://' + hostname + Path, json=payload, params=params)
        jsonresponse = response.json()
        print(jsonresponse)
        operatorid = (jsonresponse['operationId'])
        print(operatorid)
        f.write("%s\n" % operatorid)

