import requests 
from akamai.edgegrid import EdgeRc, EdgeGridAuth

session = requests.Session()
edgerc = EdgeRc('~/.edgerc')
section = 'default'
hostname = edgerc.get(section, 'host')
session.auth = EdgeGridAuth.from_edgerc(edgerc, section)

with open("/home/aaron/BOTMANPROJECT/FILES/OPERATORIDS.txt", 'r') as file:
    List = open("/home/aaron/BOTMANPROJECT/FILES/OPERATORIDS.txt").readlines()
    name_length = len(List)    
    for i in range(name_length):
        file = open('/home/aaron/BOTMANPROJECT/FILES/OPERATORIDS.txt')
        linenumber = int(i)
        Operatorid = file.readlines()
        print(Operatorid[i])
        NewOperatorid = (Operatorid[i])

        jsonparam = {
  "telemetryTypeStates": {
    "inline": {
      "enabled": False
    },
    "nativeSdk": {
      "enabled": False,
      "disabledAction": "monitor"
    },
    "standard": {
      "enabled": True,
    }
  },
  "traffic": {
    "standardTelemetry": {
      "aggressiveAction": "monitor",
      "strictAction": "monitor",
      "overrideThresholds": False
    }
  },
  "apiEndPointId": 845900,
  "operationId": (NewOperatorid)
}
        payload = jsonparam

        params = {
        'accountSwitchKey':'B-F-F2JX4L:1-8BYUX'
        }
        path = "/appsec/v1/configs/75451/versions/473/security-policies/TRDO_193032/transactional-endpoints/bot-protection"

        response = session.post('https://' + hostname + path, json=payload, params=params)
        jsonresponse = response.json()
        print(jsonresponse)


