import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import time
import sys
import gzip

# --- CONFIGURATION ---
M3U_URL = "https://jiotv.gradelabs.in/playlist.m3u?q=high&c=language&l=Hindi,Kannada,Marathi"
OUTPUT_FILE = "epg.xml.gz"

# Base URLs
CHANNEL_ICON_BASE = "https://jiotv.gradelabs.in/jtvimage/"
SHOW_ICON_BASE = "https://jiotvimages.cdn.jio.com/dare_images/shows/"

def format_date_xmltv(timestamp_ms):
    dt = datetime.fromtimestamp(int(timestamp_ms) / 1000, timezone.utc)
    return dt.strftime('%Y%m%d%H%M%S +0000')

def get_copyright_date(timestamp_ms):
    dt = datetime.fromtimestamp(int(timestamp_ms) / 1000, timezone.utc)
    return dt.strftime('%Y%m%d')

def get_program_date_path(timestamp_ms):
    dt = datetime.fromtimestamp(int(timestamp_ms) / 1000, timezone.utc)
    return dt.strftime('%Y-%m-%d')

def generate_epg():
    print(f"Starting EPG generation at {datetime.now()}")
    
    api_headers = {
        'User-Agent': 'okhttp/4.9.3',
        'host': 'jiotvapi.cdn.jio.com',
        'Accept-Encoding': 'gzip'
    }
    
    m3u_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # 1. Initialize XML
    root = ET.Element('tv', {
        'generator-info-name': 'JioTV EPG via GitHub Actions',
        'generator-info-url': 'https://github.com/mitthu786/tvepg'
    })

    # 2. Fetch M3U
    try:
        print(f"Fetching M3U from {M3U_URL}...")
        resp = requests.get(M3U_URL, headers=m3u_headers, timeout=30)
        resp.raise_for_status()
        m3u_content = resp.text
    except Exception as e:
        print(f"Critical Error: Could not download M3U. {e}")
        sys.exit(1)

    channels = re.findall(r'tvg-id="(\d+)".*tvg-logo="([^"]+)".*,(.*)', m3u_content)

    if not channels:
        print("Error: No channels found in M3U.")
        sys.exit(1)

    total_channels = len(channels)
    print(f"Found {total_channels} channels. Processing...\n")

    # 3. Process Channels with Logging
    # Enumerate gives us a counter (i) starting at 1
    for i, (ch_id, ch_logo_raw, ch_name) in enumerate(channels, 1):
        ch_name = ch_name.strip()
        
        # Log the current progress
        print(f"[{i}/{total_channels}] Processing: {ch_name} (ID: {ch_id})...", end='', flush=True)
        
        logo_filename = ch_logo_raw.split('/')[-1]
        final_logo_url = CHANNEL_ICON_BASE + logo_filename
        
        channel_node = ET.SubElement(root, 'channel', id=ch_id)
        ET.SubElement(channel_node, 'display-name').text = ch_name
        ET.SubElement(channel_node, 'icon', src=final_logo_url)

        try:
            resp = requests.get(
                f"https://jiotvapi.cdn.jio.com/apis/v1.3/getepg/get?channel_id={ch_id}&offset=0", 
                headers=api_headers, 
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                programmes = data.get('epg', [])
                
                # Print success message on the same line
                print(f" Done. ({len(programmes)} programs)")
                
                for item in programmes:
                    program_id = str(item.get('startEpoch', ''))
                    
                    prog = ET.SubElement(root, 'programme', {
                        'start': format_date_xmltv(item['startEpoch']),
                        'stop': format_date_xmltv(item['endEpoch']),
                        'channel': ch_id,
                        'catchup-id': program_id
                    })
                    
                    ET.SubElement(prog, 'title').text = item.get('showname', 'No Title')
                    ET.SubElement(prog, 'desc').text = item.get('description', 'No description.')
                    if item.get('episode_desc'):
                         ET.SubElement(prog, 'sub-title').text = item.get('episode_desc')
                    ET.SubElement(prog, 'category').text = item.get('showCategory', 'Series')
                    ET.SubElement(prog, 'date').text = get_copyright_date(item['startEpoch'])

                    # Image Logic
                    prog_img = None
                    image_keys = ['episodePoster', 'episode_poster', 'poster', 'episodeThumbnail', 'episode_thumbnail']
                    found_image = None
                    for key in image_keys:
                        if item.get(key):
                            found_image = item.get(key)
                            break 
                    
                    if found_image:
                        if "http" in found_image:
                            prog_img = found_image
                        else:
                            prog_img = SHOW_ICON_BASE + found_image
                    else:
                        date_folder = get_program_date_path(item['startEpoch'])
                        prog_img = f"{SHOW_ICON_BASE}{date_folder}/{program_id}.jpg"

                    if prog_img:
                        ET.SubElement(prog, 'icon', src=prog_img)
                    else:
                        ET.SubElement(prog, 'icon', src=final_logo_url)

                    if item.get('episode_num'):
                        ep_num = ET.SubElement(prog, 'episode-num', system="onscreen")
                        ep_num.text = str(item.get('episode_num'))

                    credits_list = []
                    if item.get('director'): credits_list.append(('director', item['director']))
                    if item.get('starCast'):
                        stars = item['starCast'].split(',') if isinstance(item['starCast'], str) else item['starCast']
                        for star in stars: credits_list.append(('actor', star.strip()))
                    
                    if credits_list:
                        credits_node = ET.SubElement(prog, 'credits')
                        for role, name in credits_list:
                            ET.SubElement(credits_node, role).text = name
            else:
                print(f" Failed (HTTP {resp.status_code})")
            
            time.sleep(0.1)

        except Exception as e:
            print(f" Error: {e}")

    # 4. Save as GZIP
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    
    with gzip.open(OUTPUT_FILE, 'wb') as f:
        tree.write(f, encoding='utf-8', xml_declaration=True)
        
    print(f"\nSuccess! Saved GZIP to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_epg()