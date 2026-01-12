import requests
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time
import gzip
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 1. UPDATED STABLE ENDPOINTS (2026)
BASE_URL = "https://www.tataplay.com/web-guide/api/v1"
MASTER_LIST_URL = f"{BASE_URL}/channels?limit=600"
SCHEDULE_URL_TEMPLATE = BASE_URL + "/channels/{id}/schedule?date={date}"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.tataplay.com/web-guide',
    'Accept': 'application/json'
}

# Add your channel names here
FILTER_NAMES = ["Star Plus", "Zee TV", "Sony Entertainment Television", "Colors", "Star Sports 1", "Sun TV"]

def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session

def format_xml_time(ts):
    # Standardizing timestamp to XMLTV
    dt = datetime.datetime.fromtimestamp(int(ts)/1000 if len(str(ts)) > 10 else int(ts))
    return dt.strftime("%Y%m%d%H%M%S +0530")

def fetch_epg():
    session = get_session()
    print("Connecting to Web-Guide...")
    
    try:
        resp = session.get(MASTER_LIST_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        all_channels = resp.json().get('data', {}).get('list', [])
        
        found = []
        for ch in all_channels:
            name = ch.get('channelName', '')
            if any(f.lower() in name.lower() for f in FILTER_NAMES):
                found.append({"id": str(ch.get('channelId')), "name": name})
        
        if not found:
            print("No channels matched your filters.")
            return

        root = ET.Element("tv", {"generator-info-name": "Self-Repairing-EPG"})

        for ch in found:
            c_tag = ET.SubElement(root, "channel", id=ch['name'].replace(" ", "") + ".in")
            ET.SubElement(c_tag, "display-name").text = ch['name']

        # 7-Day Catchup Loop
        for day_offset in range(-7, 1):
            target_date = (datetime.datetime.now() + datetime.timedelta(days=day_offset)).strftime("%d-%m-%Y")
            print(f"--- Fetching {target_date} ---")

            for ch in found:
                url = SCHEDULE_URL_TEMPLATE.format(id=ch['id'], date=target_date)
                try:
                    s_resp = session.get(url, headers=HEADERS, timeout=10)
                    if s_resp.status_code == 200:
                        progs = s_resp.json().get('data', {}).get('schedules', [])
                        for p in progs:
                            p_tag = ET.SubElement(root, "programme", 
                                                 start=format_xml_time(p['startTime']), 
                                                 stop=format_xml_time(p['endTime']), 
                                                 channel=ch['name'].replace(" ", "") + ".in")
                            ET.SubElement(p_tag, "title").text = p.get('title', 'No Title')
                    time.sleep(0.5)
                except: continue

        # Save and Compress
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        with open("epg.xml", "w", encoding="utf-8") as f: f.write(xml_str)
        with open("epg.xml", "rb") as f_in, gzip.open("epg.xml.gz", "wb") as f_out:
            f_out.writelines(f_in)
        print("Success!")

    except Exception as e:
        print(f"Script failed: {e}")

if __name__ == "__main__":
    fetch_epg()
