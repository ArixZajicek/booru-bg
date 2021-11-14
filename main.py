from set import Set
import json
import sys

""" The purpose of this code is to query an image board for all images of a
certain size or larger, and a certain aspect ratio. A couple tags may
be searched for in addition, then this script further sorts through, 
excluding blacklisted tags and posts that do not contain other required
tags. See example.json for all options. """


opts = {'debug': False, 'customconfigs': False}
configs = []

# Set arguments
i = 1
while i < len(sys.argv):
    if (sys.argv[i].startswith('-')):
        c = sys.argv[i][1]
        if c == 'd' or c == 'v':
            opts['debug'] = True
            i = i + 1
        else:
            exit(f'Unknown command line option {sys.argv[i]}')
    else:
        opts['customconfigs'] = True
        configs.append(sys.argv[i])
        i = i + 1
    

if opts['customconfigs'] is False:
    configs = ['config.json']

# Open file
for path in configs:
    f = open(path, 'r')
    content = f.read()
    f.close()
    cfg = json.loads(content)
    print(f'Loaded config file {path}')
    # Loop and dooo
    for setcfg in cfg['sets']:
        print(f"Starting set {setcfg['downloadDir']}")
        set = Set(setcfg, cfg['globalCfg'] if 'globalCfg' in cfg else {}, opts)
        try:
            set.run()
        except:
            print()
            print(f"Aborted early!")
print('Goodbye!')
