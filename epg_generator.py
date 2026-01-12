import requests
import gzip
import datetime
import time
import os

# --- CONFIGURATION ---
CHANNELS_API = "https://jiotv.data.cdn.jio.com/apis/v3.0/getMobileChannelList/get/?langId=6&os=android&devicetype=phone"
EPG_API = "http://jiotv.data.cdn.jio.com/apis/v1.3/getepg/get"

# Use GitHub Secrets for your proxy to keep it private
# Format: http://username:password@ip:port
PROXY_URL = os.getenv("INDIAN_PROXY") 

HEADERS = {
    "User-Agent": "JioTV/7.0.9 (Linux; Android 13; SM-G960F Build/R16NW; wv)",
    "app-name": "RJIL_JioTV",
    "os": "android",
    "devicetype": "phone",
    "x-api-key": "l7xx938b6684ee9e4bbe8831a9a682b8e19f",
    "Accept": "application/json"
}

def generate_epg():
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Apply proxy if available
    if PROXY_URL:
        session.proxies = {"http": PROXY_URL, "https": PROXY_URL}
        print("Using Indian Proxy for request...")

    try:
        print("Fetching Channels...")
        response = session.get(CHANNELS_API, timeout=30)
        
        if response.status_code == 450:
            print("❌ Still blocked by 450. Your proxy is either not Indian or is blacklisted.")
            return

        channels = response.json().get('result', [])
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n'
        
        # Process first 20 channels as a test
        for ch in channels[:20]:
            cid = str(ch.get("channel_id"))
            name = ch.get("channel_name", "Unknown").replace("&", "&amp;")
            xml += f'  <channel id="{cid}"><display-name>{name}</display-name></channel>\n'

            # Fetch EPG for each
            try:
                epg_val = session.get(EPG_API, params={"offset":0, "channel_id":cid, "langId":6}, timeout=10)
                if epg_val.status_code == 200:
                    for p in epg_val.json().get("epg", []):
                        start = datetime.datetime.fromtimestamp(p['startEpoch']/1000).strftime('%Y%m%d%H%M%S +0530')
                        stop = datetime.datetime.fromtimestamp(p['endEpoch']/1000).strftime('%Y%m%d%H%M%S +0530')
                        title = p.get("showname", "No Title").replace("&", "&amp;")
                        xml += f'  <programme start="{start}" stop="{stop}" channel="{cid}"><title>{title}</title></programme>\n'
                time.sleep(1) # Delay to stay under the radar
            except:
                continue

        xml += '</tv>'
        with gzip.open("epg.xml.gz", "wb") as f:
            f.write(xml.encode("utf-8"))
        print("✅ Success! epg.xml.gz created.")

    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    generate_epg()
