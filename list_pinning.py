import json

with open('orig_behavior.results.tmo') as origins_data:
    orig_data=json.load(origins_data)
print()
print('Looking for origin behaviors with cqai.app.t-mobile.com in custom certificates')
print()
for prop in orig_data:
    if len(prop['matchLocationResults']) > 0:
        for loc_results in prop['matchLocationResults']:
            try:
                if len(loc_results['options']['customCertificates']) > 0:
                    for cust_cert in loc_results['options']['customCertificates']:
                        if 'cqai' in  cust_cert['subjectCN']:
                            print("%s found in origin %s in property %s"%(cust_cert['subjectCN'],loc_results['options']['hostname'],prop['propertyName']))
            except:
                pass
        