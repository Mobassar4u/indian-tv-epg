import requests
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time

# Add your Tata Play IDs here
CHANNELS = [
    {"id": "117", "name": "Star Plus", "xmlid": "StarPlus.in"},
    {"id": "402", "name": "Star Sports 1", "xmlid": "StarSports1.in"},
]

def format_xml_time(ts):
    dt = datetime.datetime.fromtimestamp(int(ts)/1000)
    return dt.strftime("%Y%m%d%H%M%S +0530")

def fetch_epg():
    root = ET.Element("tv", {
        "generator-info-name": "Self-EPG-Generator",
        "generator-info-url": "https://github.com/your-username"
    })
    
    for ch in CHANNELS:
        c_tag = ET.SubElement(root, "channel", id=ch['xmlid'])
        ET.SubElement(c_tag, "display-name").text = ch['name']

    # Fetch 7 days of past data + today
    for day_offset in range(-7, 1):
        target_date = (datetime.datetime.now() + datetime.timedelta(days=day_offset)).strftime("%d-%m-%Y")
        
        for ch in CHANNELS:
            url = f"https://tm-api.tataplay.com/content-detail/pub/api/v1/channels/{ch['id']}/schedule?date={target_date}"
            try:
                response = requests.get(url, timeout=15).json()
                programs = response.get('data', {}).get('schedules', [])
                for prog in programs:
                    p_tag = ET.SubElement(root, "programme", 
                                         start=format_xml_time(prog['startTime']), 
                                         stop=format_xml_time(prog['endTime']), 
                                         channel=ch['xmlid'])
                    ET.SubElement(p_tag, "title", lang="hi").text = prog['title']
                    ET.SubElement(p_tag, "desc", lang="hi").text = prog.get('description', 'No info')
                time.sleep(0.5) # Anti-block delay
            except Exception as e:
                print(f"Error: {e}")

    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)

if __name__ == "__main__":
    fetch_epg()
