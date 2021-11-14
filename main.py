from set import Set
import json

""" The purpose of this code is to query an image board for all images of a
certain size or larger, and a certain aspect ratio. A couple tags may
be searched for in addition, then this script further sorts through, 
excluding blacklisted tags and posts that do not contain other required
tags. See example.json for all options. """


# Open file
f = open('config.json', 'r')
content = f.read()
f.close()
cfg = json.loads(content)

# Loop and dooo
for setcfg in cfg['sets']:
    print(f"Starting bulk download of set '{setcfg['downloadDir']}'")
    set = Set(setcfg, cfg['globalBlacklist'], cfg['rootDir'])
    
    try:
        set.run()
        print(f"Completed bulk download of set '{setcfg['downloadDir']}'")
    except:
        print(f"Set '{setcfg['downloadDir']}' aborted early! Last post ID: {set.last_id}")
    print(f"Downloaded {set.totaldownloads} new file{'' if set.totaldownloads == 1 else 's'}! {set.totalskipped} skipped (already downloaded).")
print('Goodbye!')
