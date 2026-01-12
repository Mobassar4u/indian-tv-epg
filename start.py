import requests
import json
import datetime
import os

# 2026 Updated Headers
HEADERS = {
    "User-Agent": "JioTV 7.0.5 (Android 10)",
    "appkey": "NzNiMDhlYzQyNjJm",
    "devicetype": "phone",
    "os": "android",
    "versionCode": "300",
    "Accept": "application/json"
}

def get_channels():
    # Primary 2026 endpoint for channel lists
    url = "https://jiotv.data.cdn.jio.com/apis/v1.3/getMobileChannelList/get/?os=android&devicetype=phone&version=300"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.json().get("result", [])
    except Exception as e:
        print(f"Error fetching channels: {e}")
    return []

def generate_xmltv():
    channels = get_channels()
    if not channels:
        print("Failed to fetch channels. API may be blocked or changed.")
        return

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
        f.write('<tv generator-info-name="Indian-EPG-Grabber">\n')
        
        # Write Channel Data
        for c in channels:
            cid = c.get("channel_id")
            name = c.get("channel_name", "Unknown").replace("&", "&amp;")
            logo = c.get("logoUrl", "")
            f.write(f'  <channel id="{cid}">\n')
            f.write(f'    <display-name>{name}</display-name>\n')
            f.write(f'    <icon src="{logo}" />\n')
            f.write(f'  </channel>\n')
        
        # Note: In a full version, you would loop getEpg() here for each channel ID
        f.write('</tv>')
    print("epg.xml generated successfully.")

if __name__ == "__main__":
    generate_xmltv()
