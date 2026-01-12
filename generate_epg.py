import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time
import gzip
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 1. UPDATED STABLE ENDPOINTS
# Switched from tm-api (unresolvable) to www (stable)
BASE_URL = "https://ts-api.videoready.tv/content-detail/pub/api/v1"
CHANNELS_URL = f"{BASE_URL}/channels?limit=1000"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Referer': 'https://ts-api.videoready.tv',
    'Accept': 'application/json'
}

def get_secure_session():
    session = requests.Session()
    # Retry mechanism for stability
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session

def fetch_channels():
    session = get_secure_session()
    print("Connecting to Tata Play Web Guide...")
    
    try:
        response = session.get(CHANNELS_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        channels_list = data.get('data', {}).get('list', [])
        if not channels_list:
            print("No channels found.")
            return

        root = ET.Element("channels")

        for ch in channels_list:
            s_id = str(ch.get('channelId') or ch.get('id', ''))
            ch_name = ch.get('channelName') or ch.get('name') or f"Channel_{s_id}"
            
            # Correct Logo reconstruction
            logo_url = ch.get('logo') or ch.get('channelLogoUrl') or ""
            if not logo_url.startswith('http') and s_id:
                logo_url = f"https://pwa-api.tataplay.com/content/detail/{s_id}/logo.png"

            # Create node
            channel_node = ET.SubElement(root, "channel", {
                "site": "tataplay.com",
                "xmltv_id": f"ts{s_id}",
                "site_id": s_id,
                "logo": logo_url
            })
            channel_node.text = ch_name

        # Save and Pretty Print
        xml_bytes = ET.tostring(root, encoding='utf-8')
        xml_str = xml_bytes.decode('utf-8')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")

        with open("indian_channels.xml", "w", encoding="utf-8") as f:
            f.write(pretty_xml)
            
        print(f"Success! Generated indian_channels.xml with {len(channels_list)} channels.")

    except Exception as e:
        print(f"Connection Failed: {e}")
        print("Tip: Check your internet connection or try using a VPN if the domain is blocked in your region.")

if __name__ == "__main__":
    fetch_channels()
