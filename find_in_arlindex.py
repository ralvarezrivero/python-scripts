import os
from xml.etree import ElementTree

file_name = 'Downloads/arlindex.xml'
home = os.path.expanduser("~")
full_file = os.path.join(home, file_name)

print(full_file)

arl_index = ElementTree.parse(full_file)
root = arl_index.getroot()

print (root.tag)
print (root.attrib)

for child in root:
	print(child.tag, child.attrib)

# arl_file = arl_index.findall('configs')
# for file in arl_file:
# 	print(file)