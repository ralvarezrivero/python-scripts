import json
import re
import os
import sys
import optparse
import datetime

def parseCondition(filterType, comparison, value, matches):
        # Set defaults
    negate = False
    queryParam = None
    queryValue = None

    # Parse filterType to akamai match type
    if filterType == 'URL':
        matchType = 'path'
    elif filterType == 'QueryString':
        matchType = 'query'
    elif filterType == 'QueryStringParamValue':
        matchType = 'query'
    elif filterType == 'ClientIP':
        matchType = 'clientip'
    elif filterType == 'User-Agent':
        matchType = 'header'

    # Remove trailing pipe and surrounding quotes
    if value.endswith('|'):
        value = value[0: len(value) - 1]
    if value.startswith('"'):
        value = value[1:]
    if value.endswith('"'):
        value = value[0: len(value) - 1]

    matchValue = value # added by ralvarez to fix local variable 'matchValue' referenced before assignment error

    if matchType == 'query':
        if filterType == 'QueryString':
            queryComponents = value.split('=')
            queryParam = queryComponents[0]
            queryValue = value.replace("{q}=".format(q = queryComponents[0]),'')
        elif filterType == 'QueryStringParamValue':
            queryComponents = json.loads(value.replace(';',':'))
            queryParam = list(queryComponents.keys())[0]
            queryValue = queryComponents[queryParam]
        matchValue = '{q}={v}'.format(q = queryParam, v = queryValue)
        existingRule = [r for r in matches if r['matchType'] == 'query' and r['negate'] == negate and r['matchValue'].startswith(queryParam) ]
    else:
        if comparison == '==':
            matchValue = value
        elif comparison == 'contains':
            matchValue = '*{v}*'.format(v = value)
        elif comparison == 'starts with':
            matchValue = '{v}*'.format(v = value)
        elif comparison == 'endswith':
            matchValue = '*{v}'.format(v = value)
        if comparison == '!=':
            matchValue = value
            negate = True
        elif comparison == 'not contains':
            matchValue = '*{v}*'.format(v = value)
            negate = True
        elif comparison == 'does not start with':
            matchValue = '{v}*'.format(v = value)
            negate = True
        elif comparison == 'does not end with':
            matchValue = '*{v}'.format(v = value)
            negate = True

        if matchValue.startswith('*^'): # added by ralvarez
            matchValue = matchValue[2:]
        
        if filterType == 'User-Agent':
            headerName = 'user-agent'
            headerValue = matchValue
            existingRule = [r for r in matches if r['matchType'] == matchType and r['negate'] == negate and r['objectMatchValue']['name'] == headerName ]
        else:
            existingRule = [r for r in matches if r['matchType'] == matchType and r['negate'] == negate]
    

    if len(existingRule) > 0:
        existingRule = existingRule[0]
        if matchType == 'query':
            existingRule['matchValue'] += ' {q}'.format(q = queryValue)
        elif matchType == 'header':
            existingRule['objectMatchValue']['options']['value'].append(headerValue)
        else:
            existingRule['matchValue'] += ' {v}'.format(v = matchValue)
            # Handle subsequent values containing wildcards when initial did not
            if '*' in existingRule['matchValue']:
                 existingRule['matchOperator'] = 'contains'
    else:
        if matchType == 'header':
            match = json.loads(headerRuleTemplate)
            match['objectMatchValue']['name'] = headerName
            match['objectMatchValue']['options']['value'].append(headerValue)
        else:
            match = json.loads(simpleRuleTemplate)
            match['matchValue'] = matchValue

        match['negate'] = negate
        match['matchType'] = matchType

        # Handle path contains requirement
        if 'matchValue' in match.keys() and '*' in match['matchValue']:
            if options.debug:
                print('Correcting match operator for value "{m}"'.format(m = match['matchValue']))
            match['matchOperator'] ='contains'
        
        # Add to list
        matches.append(match)
    
    return matches

def parseFrom(inputFrom, matches):
    # Bail out of empty string input
    if inputFrom == '':
        return matches

    url_re = '(http[s]?)?(?:\:\/\/)?([a-z0-9\-\.]+)?([^\?]*)(?:\??(.+))?'
    url_matches = re.search(url_re,inputFrom)
    protocol = url_matches.group(1)
    hostname = url_matches.group(2)
    path = url_matches.group(3)
    query_str = url_matches.group(4)

    if protocol is not None:
        protocol_match = json.loads(simpleRuleTemplate)
        protocol_match['matchType'] = 'protocol'
        protocol_match['matchValue'] = protocol
        matches.append(protocol_match)

    if hostname is not None:
        hostname_match = json.loads(simpleRuleTemplate)
        hostname_match['matchType'] = 'hostname'
        hostname_match['matchValue'] = hostname
        matches.append(hostname_match)

    if path is not None:
        if '*' in path:
            regex_match = json.loads(simpleRuleTemplate)
            regex_match['matchType'] = 'regex'
            regex_match['matchValue'] = path.replace('*','(.*)')
            matches.append(regex_match)
        else:
            path_match = json.loads(simpleRuleTemplate)
            path_match['matchType'] = 'path'
            path_match['matchValue'] = path
            matches.append(path_match)

    if query_str is not None:
        split_query = query_str.split('&')
        for split in split_query:
            query_match = json.loads(simpleRuleTemplate)
            query_match['matchType'] = 'query'
            query_match['matchValue'] = split
            matches.append(query_match)

    return matches

def parseTo(inputTo):
    if '$1' in inputTo:
        inputTo = inputTo.replace('$1','\\1')
    elif '$2' in inputTo:
        inputTo = inputTo.replace('$2','\\2')
    elif '$3' in inputTo:
        inputTo = inputTo.replace('$3','\\3')
    elif '$4' in inputTo:
        inputTo = inputTo.replace('$4','\\4')

    return inputTo

def parseRule(rule, match_rules):
    matches = []
    matches = parseFrom(rule['from'], matches)
    matches = parseFilter(rule['filter'], matches)

    if len(matches) == 0:
        print('-- WARNING: Rule "{r}" has neither "from" not "filter" fields and will be skipped'.format(r = rule['name']))
        return match_rules

    redirectUrl = rule['to'].strip() # remove whitespace at start or end
    if '$1' in redirectUrl:
        redirectUrl = redirectUrl.replace('$1','\\1')
    if '$2' in redirectUrl:
        redirectUrl = redirectUrl.replace('$2','\\2')
    if '$3' in redirectUrl:
        redirectUrl = redirectUrl.replace('$3','\\3')
    if '$args' in redirectUrl:
        redirectUrl = redirectUrl.replace('$args','')
    
    # Copy query string if $args present in destination
    useIncomingQueryString = False
    if '$args' in rule['to']:
        useIncomingQueryString = True

    # Set relative URL if destination starts with /
    useRelativeUrl = 'none'
    if redirectUrl.startswith('/'):
        useRelativeUrl = 'relative_url'

    match_rule = {
        'type': 'erMatchRule',
        'name': rule['name'],
        'start': 0,
        'end': 0,
        'statusCode': int(rule['response_code']),
        'redirectURL': redirectUrl,
        'useIncomingQueryString': useIncomingQueryString,
        'useRelativeUrl': useRelativeUrl,
        'matches': matches
    }

    match_rules.append(match_rule)
    return match_rules

def parseFilter(inputFilter, matches):
    # Check it can be handled
    unhandleableRegex = '.*[\s]*\|[\s]*\(.*'
    if re.match(unhandleableRegex, inputFilter):
        print('-- WARNING: Filter "{f}" is not something we can handle, so is being skipped'.format(f = inputFilter))
        return matches

    filterMatch = '([a-zA-Z\-]+)[\s]*(==|!=|contains|not-contains|starts-with|ends-with|does not start with|does not end with)[\s]*([^\s]+)'

    filterComponents = inputFilter.split('(')

    for filterComponent in filterComponents:

        # Remove closing parantheses and trailing spaces
        filterComponent = filterComponent.replace(')','')
        filterComponent = filterComponent.rstrip()

        ## Master regex to extract filter components
        matchedFilters = re.findall(filterMatch, filterComponent)

        for matchedFilter in matchedFilters:
            filterType = matchedFilter[0]
            filterComparison = matchedFilter[1]
            filterValue = matchedFilter[2]

            # Handle query strings with multiple params
            filterValues = filterValue.split('&')
            for value in filterValues:
                parseCondition(filterType,filterComparison,value, matches)

    return matches

# from here on down - added by ralvarez
def traverse_dict(dict):

    for rule in dict['delivery_rules']['Redirect']:
        parseFilter(rule['filter'])
        parseFrom(rule['from'])

def read_files(filepath):
    with open (filepath, 'r') as f:
        data=json.load(f)
        return data

def mainf():

    #start = datetime.now()

    # Set options
    usage = "usage: python convertImperva.py --file /path/to/file.json"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        '-f', '--file',
        action='store', dest='file',
        help='Rules file')
    
    parser.add_option(
        '-d', '--debug', default=False,
        action='store_true', dest='debug',
        help='Debug mode')
    
    global options
    (options, args) = parser.parse_args()

    # if options.file is None:
    #     parser.error('You must supply a value for -f/--file')

    # JSON Templates
    global simpleRuleTemplate, headerRuleTemplate, regexRuleTemplate
    simpleRuleTemplate = '''{
        "matchValue": "",
        "matchOperator": "equals",
        "negate": false,
        "caseSensitive": false,
        "matchType": ""
    }'''

    headerRuleTemplate = '''{
        "objectMatchValue": {
        "options": {
            "value": []
        },
        "name": "",
        "type": "object"
        },
        "matchOperator": "equals",
        "negate": false,
        "caseSensitive": false,
        "matchType": "header"
    }'''

    matches = []
    matches = parseFrom('hostname.com/path*', matches)

    print('Parsing file: {f}'.format(f = options.file))
    with open (options.file, 'r') as inFile:
        json_data=json.load(inFile)

    # Set matchRules
    match_rules = []
    sorted_redirects = []
    sorted_simplified_redirects = []

    # Sort rules by priority (increasing)
    if 'Redirect' in json_data['delivery_rules'].keys():
        sorted_redirects = sorted(json_data['delivery_rules']['Redirect'], key=lambda r: int(r.get('priority', '9999')))
    if 'SimplifiedRedirect' in json_data['delivery_rules'].keys():
        sorted_simplified_redirects = sorted(json_data['delivery_rules']['SimplifiedRedirect'], key=lambda r: int(r.get('priority', '9999')))

    # Imperva applies Simplified Redirects first
    for rule in sorted_simplified_redirects:
        if options.debug:
            print('-- Parsing Simplified Redirect rule: {r}'.format(r = rule['name']))
        match_rules = parseRule(rule, match_rules)

    for rule in sorted_redirects:
        if options.debug:
            print('-- Parsing Redirect rule: {r}'.format(r = rule['name']))
        match_rules = parseRule(rule, match_rules)

    # Write file to disk
    policy_file = options.file.replace('.json', '_akamai.json')
    with open (policy_file, 'w') as outFile:
        print('-- Writing output to {f}'.format(f = policy_file))
        json.dump(match_rules, outFile, indent=4)

mainf()