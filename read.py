import urllib.request
import xml.etree.ElementTree as ET
import json

winzones_url = 'https://raw.githubusercontent.com/unicode-org/cldr/4fc49910fb9ee18d373ab41b581ac3b878898e50/common/supplemental/windowsZones.xml'
winzones_xml = urllib.request.urlopen(winzones_url).read().decode()
winzones = ET.fromstring(winzones_xml)

with open("icalevents/zones.py", "w") as outfile:
    outfile.write("zones = {\n")
    for zone in winzones.findall('.//mapZone'):
        if zone.attrib['territory'] == '001':
            outfile.write(f'\t"{zone.attrib["other"]}":"{zone.attrib["type"]}",\n')

    outfile.write("}\n")
