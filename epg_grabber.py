#!/usr/bin/env python3
import requests
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os

# Indian channels mapping (Tata Play/DishTV IDs)
CHANNELS = {
    "StarPlus.in": {"site": "dishtv.in", "id": "1001"},
    "ZeeTV.in": {"site": "tataplay.com", "id": "ts840"},
    "Colors.in": {"site": "jiotv.com", "id": "144"}
}

def generate_epg():
    epg = ET.Element('tv')
    
    for xmltv_id, info in CHANNELS.items():
        channel = ET.SubElement(epg, 'channel', id=xmltv_id)
        ET.SubElement(channel, 'display-name').text = xmltv_id.replace('.in', ' HD')
    
    # Generate 7 days dummy EPG (replace with real API calls)
    for i in range(7):
        date = datetime.now() + timedelta(days=i)
        for xmltv_id in CHANNELS:
            programme = ET.SubElement(epg, 'programme', 
                start=date.strftime('%Y%m%d%H%M%S +0530'), 
                stop=(date.replace(hour=23, minute=59) + timedelta(minutes=1)).strftime('%Y%m%d%H%M%S +0530'),
                channel=xmltv_id)
            ET.SubElement(programme, 'title', lang='en').text = f"{xmltv_id} Show"
            ET.SubElement(programme, 'desc', lang='en').text = "Live TV Program"
    
    tree = ET.ElementTree(epg)
    tree.write('epg_india.xml', encoding='utf-8', xml_declaration=True)
    
    # Gzip
    with open('epg_india.xml', 'rb') as f_in:
        with gzip.open('epg_india.xml.gz', 'wb') as f_out:
            f_out.writestr(f_in.read())

if __name__ == '__main__':
    generate_epg()
