import requests
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time

# Same list as before - add your IDs here
CHANNELS = [
    {"id": "117", "name": "Star Plus", "xmlid": "StarPlus.in"},
    {"id": "402", "name": "Star Sports 1", "xmlid": "StarSports1.in"},
    {"id": "1502", "name": "Sun TV", "xmlid": "SunTV.in"},
]

def format_xml_time(ts):
    dt = datetime.datetime.fromtimestamp(int(ts)/1000)
    return dt.strftime("%Y%m%d%H%M%S +0530")

def fetch_epg():
    root = ET.Element("tv")
    
    # 1. Create Channel Headers with Catchup Metadata
    for ch in CHANNELS:
        c_tag = ET.SubElement(root, "channel", id=ch['xmlid'])
        ET.SubElement(c_tag, "display-name").text = ch['name']

    # 2. Fetch Data for Today and the Past 7 Days
    # We loop from -7 (7 days ago) to 0 (today)
    for day_offset in range(-7, 1):
        target_date = (datetime.datetime.now() + datetime.timedelta(days=day_offset)).strftime("%d-%m-%Y")
        print(f"--- Fetching Data for Date: {target_date} ---")

        for ch in CHANNELS:
            print(f"Grabbing {ch['name']}...")
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
                
                # Small sleep to avoid getting blocked by the API
                time.sleep(0.5)
            except Exception as e:
                print(f"Error for {ch['name']} on {target_date}: {e}")

    # 3. Save to File
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)
    print("Success: epg.xml generated with 7 days of catchup data.")

if __name__ == "__main__":
    fetch_epg()
