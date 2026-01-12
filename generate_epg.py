import requests
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Configuration: Site ID is the Tata Play Channel Number
CHANNELS = [
    {"id": "117", "name": "Star Plus", "xmlid": "StarPlus.in"},
    {"id": "143", "name": "Zee TV", "xmlid": "ZeeTV.in"},
    {"id": "130", "name": "Sony SET", "xmlid": "SonySET.in"},
    {"id": "402", "name": "Star Sports 1", "xmlid": "StarSports1.in"},
    {"id": "509", "name": "Aaj Tak", "xmlid": "AajTak.in"}
]

def get_tata_date():
    return datetime.datetime.now().strftime("%d-%m-%Y")

def format_xml_time(ts):
    # Converts timestamp to XMLTV format: YYYYMMDDHHMMSS +0530
    dt = datetime.datetime.fromtimestamp(int(ts)/1000)
    return dt.strftime("%Y%m%d%H%M%S +0530")

def fetch_epg():
    root = ET.Element("tv")
    date_str = get_tata_date()

    # 1. Create Channel Headers
    for ch in CHANNELS:
        c_tag = ET.SubElement(root, "channel", id=ch['xmlid'])
        ET.SubElement(c_tag, "display-name").text = ch['name']

    # 2. Fetch Program Data
    for ch in CHANNELS:
        print(f"Fetching {ch['name']}...")
        url = f"https://tm-api.tataplay.com/content-detail/pub/api/v1/channels/{ch['id']}/schedule?date={date_str}"
        try:
            response = requests.get(url, timeout=10).json()
            programs = response.get('data', {}).get('schedules', [])

            for prog in programs:
                p_tag = ET.SubElement(root, "programme", 
                                     start=format_xml_time(prog['startTime']), 
                                     stop=format_xml_time(prog['endTime']), 
                                     channel=ch['xmlid'])
                ET.SubElement(p_tag, "title", lang="hi").text = prog['title']
                ET.SubElement(p_tag, "desc", lang="hi").text = prog.get('description', 'No description available')
        except Exception as e:
            print(f"Error fetching {ch['name']}: {e}")

    # 3. Save to File
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)

if __name__ == "__main__":
    fetch_epg()