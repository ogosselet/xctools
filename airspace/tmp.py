from lxml import etree

data = etree.parse('./tests/aixm_4.5_extract.xml')
root = data.getroot()
print(len(root.findall('Ase')))
