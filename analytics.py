import json, requests

r = requests.get('https://formulae.brew.sh/api/formula.json')
packages_json = r.json()

# print(json.dumps(packages_json, indent=3))

count = 0

for package in packages_json:
	package_name = package['name']
	pack_url = f'https://formulae.brew.sh/api/formula/{package_name}.json'
	
	r = requests.get(pack_url)
	package_info = r.json()

	print ('{p:15s} {d:30s}'.format(p=package_info['name'], d=package_info['desc']))
	count += 1
	if count > 30:
		break

# print(len(packages_json))

# for package in package_json['name']:
# 	print(json.dumps(package['name']))
# r = requests.get(package_url)
# package_json = r.json()
# package_string = json.dumps(package_json, indent=2)
# print(package_string)
# installs_30 = package_json['analytics']['install_on_request']['30d'][package]
# installs_90 = package_json['analytics']['install_on_request']['90d'][package]
# installs_365 = package_json['analytics']['install_on_request']['365d'][package]

# print(package,package_desc, installs_30, installs_90, installs_365)