#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import gzip
from datetime import datetime, timedelta

# Indian channels (Tata Play/DishTV mappings)
CHANNELS = {
    "StarPlus.in": "Star Plus HD",
    "ZeeTV.in": "Zee TV HD", 
    "Colors.in": "Colors HD",
    "SonySAB.in": "Sony SAB HD"
}

def generate_epg():
    epg = ET.Element('tv')
    
    # Add channels
    for xmltv_id, name in CHANNELS.items():
        channel = ET.SubElement(epg, 'channel', id=xmltv_id)
        ET.SubElement(channel, 'display-name').text = name
    
    # Generate 7 days EPG
    for i in range(7):
        date = datetime.now() + timedelta(days=i)
        for xmltv_id, name in CHANNELS.items():
            start = date.replace(hour=6, minute=0, second=0)
            stop = start.replace(hour=23, minute=59, second=59)
            
            programme = ET.SubElement(epg, 'programme',
                start=start.strftime('%Y%m%d%H%M%S +0530'),
                stop=stop.strftime('%Y%m%d%H%M%S +0530'),
                channel=xmltv_id)
            ET.SubElement(programme, 'title', lang='en').text = f"{name} Live"
            ET.SubElement(programme, 'desc', lang='en').text = "Live TV broadcast"
    
    # Write XML
    tree = ET.ElementTree(epg)
    tree.write('epg_india.xml', encoding='utf-8', xml_declaration=True)
    
    # ✅ FIXED: Use gzip.compress()
    with open('epg_india.xml', 'rb') as f:
        xml_data = f.read()
    
    compressed = gzip.compress(xml_data)
    with open('epg_india.xml.gz', 'wb') as f:
        f.write(compressed)

if __name__ == '__main__':
    generate_epg()
    print("✅ EPG generated: epg_india.xml.gz")
