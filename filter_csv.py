import csv

mylist = []
with open('/home/ralvarez/Downloads/edgehostnames.csv', 'r') as csv_file:
    row = csv.DictReader(csv_file)
    for line in row:
        if line["ttl"] != '21600':
            mylist.append(line["recordName"])
            
mylist.sort()
print(mylist) 
#print('{} has a TTL of {}'.format(line["recordName"],line["ttl"]))
