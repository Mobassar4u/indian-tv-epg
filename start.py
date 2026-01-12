import requests
import json
import datetime
import os

# Configuration
prevEpgDayCount = 1
nextEpgDayCount = 1
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json"
}

channelList = []

def getChannels():
    print("Fetching Channel List...")
    reqUrl = "https://jiotv.data.cdn.jio.com/apis/v1.4/getMobileChannelList/get/?os=android&devicetype=phone"
    try:
        response = requests.get(reqUrl, headers=headers, timeout=10)
        if response.status_code == 200:
            apiData = response.json()
            return apiData.get("result", [])
        return []
    except Exception as e:
        print(f"Error fetching channels: {e}")
        return []

def getEpg(channelId, offset, langId):
    try:
        reqUrl = f"https://jiotv.data.cdn.jio.com/apis/v1.3/getepg/get?channel_id={channelId}&offset={offset}&langId={langId}"
        response = requests.get(reqUrl, headers=headers, timeout=5)
        if response.status_code == 200:
            apiData = response.json()
            return apiData.get("epg", [])
        return []
    except Exception:
        return []

def clean_text(text):
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;")

def writeEpgChannel(id, name, iconId, fp):
    if id is None or name is None: return
    name = clean_text(name)
    fp.write(f'\t<channel id="{id}">\n')
    fp.write(f'\t\t<display-name>{name}</display-name>\n')
    fp.write(f'\t\t<icon src="https://jiotv.catchup.cdn.jio.com/dare_images/images/{iconId}"></icon>\n')
    fp.write('\t</channel>\n')

def writeEpgProgram(channelId, epg, fp):
    try:
        start_ts = int(epg.get("startEpoch", 0) / 1000)
        end_ts = int(epg.get("endEpoch", 0) / 1000)
        
        progStart = datetime.datetime.fromtimestamp(start_ts).strftime("%Y%m%d%H%M%S +0000")
        progEnd = datetime.datetime.fromtimestamp(end_ts).strftime("%Y%m%d%H%M%S +0000")

        title = clean_text(epg.get("showname", "No Title"))
        description = clean_text(epg.get("episode_desc") or epg.get("description") or "")
        category = clean_text(epg.get("showCategory", ""))
        
        fp.write(f'\t<programme start="{progStart}" stop="{progEnd}" channel="{channelId}">\n')
        fp.write(f'\t\t<title lang="en">{title}</title>\n')
        fp.write(f'\t\t<desc lang="en">{description}</desc>\n')
        
        if category:
            fp.write(f'\t\t<category lang="en">{category}</category>\n')
        
        icon = epg.get("episodePoster")
        if icon:
            fp.write(f'\t\t<icon src="https://jiotv.catchup.cdn.jio.com/dare_images/shows/{icon}"></icon>\n')
        fp.write('\t</programme>\n')
    except Exception as e:
        pass # Skip malformed entries

def grabEpgAllChannel(day):
    print(f"\nProcessing Day {day}...")
    filename = f"program{day}.xml"
    with open(filename, "w", encoding='utf-8') as programFile:
        for idx, channel in enumerate(channelList):
            cid = channel.get("channel_id")
            cname = channel.get("channel_name")
            epgData = getEpg(cid, day, 6)
            for epg in epgData:
                writeEpgProgram(cid, epg, programFile)
            if idx % 10 == 0:
                print(f"Progress: {idx}/{len(channelList)} channels done", end="\r")

def rotateEpg():
    print("Rotating old EPG files...")
    for day in range((prevEpgDayCount * -1), nextEpgDayCount - 1):
        target = f'./program{day}.xml'
        source = f'./program{day+1}.xml'
        if os.path.exists(source):
            if os.path.exists(target): os.remove(target)
            os.rename(source, target)

def mergeEpgData():
    print("\nMerging files into epg.xml...")
    try:
        with open("epg.xml", "w", encoding='utf-8') as epgFile:
            epgFile.write('<?xml version="1.0" encoding="utf-8"?>\n')
            epgFile.write('<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
            epgFile.write('<tv generator-info-name="EPG-Grabber">\n')
            
            if os.path.exists("channels.xml"):
                with open("channels.xml", "r", encoding="utf-8") as f:
                    epgFile.write(f.read())
            
            for day in range((prevEpgDayCount * -1), nextEpgDayCount):
                fname = f'program{day}.xml'
                if os.path.exists(fname):
                    with open(fname, "r", encoding='utf-8') as f:
                        epgFile.write(f.read())
            
            epgFile.write("</tv>\n")
    except Exception as e:
        print(f"Merge failed: {e}")

# Main Execution
if __name__ == "__main__":
    channelList = getChannels()
    if not channelList:
        print("Failed to retrieve channels. API might be down or blocked.")
    else:
        # 1. Write Channels file
        with open("channels.xml", "w", encoding='utf-8') as channelFile:
            for channel in channelList:
                writeEpgChannel(channel.get("channel_id"), channel.get("channel_name"), channel.get("logoUrl"), channelFile)
        
        # 2. Rotate and Grab
        rotateEpg()
        for day in range((prevEpgDayCount * -1), nextEpgDayCount):
            # If program file doesn't exist for the day, grab it
            if not os.path.exists(f'program{day}.xml'):
                grabEpgAllChannel(day)
        
        # 3. Final Merge
        mergeEpgData()
        print("\nAction complete. Generated epg.xml")
