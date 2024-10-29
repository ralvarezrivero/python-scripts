#!/usr/bin/python3

"""
Use Example:
python3 traffic_reports.py report --cpcode 718245 822962 --accountSwitchKey F-AC-1577936:1-5G3LB
"""

import requests, json, sys, os
from akamai.edgegrid import EdgeGridAuth,EdgeRc
import argparse
from urllib.parse import urljoin
import pandas as pd
from pandas import json_normalize

class MyArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        self.exit(0, '%s: error: %s\n' % (self.prog, message))

# Initialize the authorization parameters for the API calls
def init_config():
    rc_path = os.path.expanduser('~/.edgerc')
    edgerc = EdgeRc(rc_path)
    section = 'default'
    global baseurl
    baseurl = 'https://%s' % edgerc.get(section, 'host')

    global session
    session = requests.Session()
    session.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    return()

def url_responses_by_url(cp_codes, account_key, filter_criteria, error_class):
    headers = {'content-type': 'application/json'}
    data = {
    'objectType': 'cpcode',
    'objectIds': cp_codes,
    'metrics': [
        filter_criteria
    ],
    'limit': 5000
    }
    # Convert the json object to a string that the API can interpret
    data = json.dumps(data)
    response = session.post(urljoin(baseurl, '/reporting-api/v1/reports/url' + error_class + 'responses-by-url/versions/1/report-data?start=2021-08-01T00:00:00Z&end=2021-09-01T00:00:00Z&interval=DAY&trace=true&accountSwitchKey=' + account_key), data=data, headers=headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))

    df = pd.DataFrame(response)
    df = json_normalize(response.json(), "data")
    df[filter_criteria] = pd.to_numeric(df[filter_criteria])
    df = df.sort_values(filter_criteria,ascending=False)
    #df.to_excel('./exported_json_data.xlsx')
    return(df)

def traffic_by_response(cp_codes, account_key):
    headers = {'content-type': 'application/json'}
    data = {
    'objectType': 'cpcode',
    'objectIds': cp_codes,
    'metrics': [
        'edgeHits',
        'edgeHitsPercent',
        'originHits',
        'originHitsPercent'
    ]
    }
    # Convert the json object to a string that the API can interpret
    data = json.dumps(data)
    response = session.post(urljoin(baseurl, '/reporting-api/v1/reports/traffic-by-response/versions/1/report-data?start=2021-08-01T00:00:00Z&end=2021-09-01T00:00:00Z&interval=HOUR&trace=true&accountSwitchKey=' + account_key), data=data, headers=headers)
    #print(json.dumps(response.json(), indent=4, sort_keys=True))

    df = pd.DataFrame(response)
    df.info()
    #pd.options.display.float_format = '{:.2%}'.format
    df = json_normalize(response.json(), "data")
    df.info()
    #pd.to_numeric(df, downcast='integer')
    df['edgeHits'] = df['edgeHits'].astype('int')
    df['originHits'] = df['originHits'].astype('int')
    df['edgeHitsPercent'] = df['edgeHitsPercent'].astype('float').round(2)
    df['originHitsPercent'] = df['originHitsPercent'].astype('float').round(2)
    df.info()
    df = df.sort_values('response_code',ascending=False)
    return(df)

def url_hits(cp_codes, account_key):
    headers = {'content-type': 'application/json'}
    data = {
    'objectType': 'cpcode',
    'objectIds': cp_codes,
    'metrics': [
        'allEdgeHits',
        'allOriginHits',
        'allHitsOffload'
    ], 
    "limit": 5000
    }
    # Convert the json object to a string that the API can interpret
    data = json.dumps(data)
    response = session.post(urljoin(baseurl, '/reporting-api/v1/reports/urlhits-by-url/versions/1/report-data?start=2021-09-01T00:00:00Z&end=2021-10-01T00:00:00Z&interval=DAY&trace=true&accountSwitchKey=' + account_key), data=data, headers=headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))

    df = pd.DataFrame(response)
    df.info()
    #pd.options.display.float_format = '{:.2%}'.format
    df = json_normalize(response.json(), "data")
    df.info()
    #pd.to_numeric(df, downcast='integer')
    df['allEdgeHits'] = df['allEdgeHits'].astype('int')
    df['allOriginHits'] = df['allOriginHits'].astype('int')
    df['allHitsOffload'] = df['allHitsOffload'].astype('float').round(2)
    df.info()
    df = df.sort_values('allEdgeHits',ascending=False)
    return(df)

# Main Function
def main():
    global args

    parser = MyArgumentParser(
            description='Offload and Response Codes for TBAs', add_help=False)

    parser.add_argument('--version', action='version', version='TBA Friend v1.0')

    subparsers = parser.add_subparsers(title='Commands', dest='command', metavar="")

    create_parser = subparsers.add_parser('help', help='Show available help').add_argument('args', metavar="", nargs=argparse.REMAINDER)
    parser_report = subparsers.add_parser('report', help='Hits Offload and Response Code Reports', add_help=False)

    mandatory_report = parser_report.add_argument_group('required arguments')
    mandatory_report.add_argument('--cpcode', nargs='+', required=True, help='CP code or list of CP codes separated by space')
    mandatory_report.add_argument('-a', '--accountSwitchKey', required=True, help='Account Switch Key')

    optional_report = parser_report.add_argument_group('optional arguments')
    optional_report.add_argument('-e', '--edgerc', help='Config file [default: ~/.edgerc]')
    optional_report.add_argument('-s', '--section', help='Config section in .edgerc [default: default]')
    

    args = parser.parse_args()

    if len(sys.argv) <= 1 or args.command == 'help':
        parser.print_help()
        return 0

    global baseurl, session

    init_config()

    account_key = args.accountSwitchKey
    cp_codes = args.cpcode

    df1 = url_hits(cp_codes, account_key)
    df2 = traffic_by_response(cp_codes, account_key)
    df3 = url_responses_by_url(cp_codes, account_key, '304EdgeHits', '3XX')
    df4 = url_responses_by_url(cp_codes, account_key, '404EdgeHits', '4XX')

    writer = pd.ExcelWriter('exported_json_data.xlsx', engine='xlsxwriter')

    # Write each dataframe to a different worksheet.
    df1.to_excel(writer, sheet_name='URL Traffic')
    df2.to_excel(writer, sheet_name='Response Codes')
    df3.to_excel(writer, sheet_name='304 Responses')
    df4.to_excel(writer, sheet_name='404 Responses')

    writer.save()

# MAIN PROGRAM
if __name__ == "__main__":
    # Main Function
    main()