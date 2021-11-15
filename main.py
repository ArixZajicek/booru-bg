from set import Set
import json
import sys
import time

""" The purpose of this code is to query an image board for all images of a
certain size or larger, and a certain aspect ratio. A couple tags may
be searched for in addition, then this script further sorts through, 
excluding blacklisted tags and posts that do not contain other required
tags. See example.json for all options. """


def tp(str, end='\n', flush=False):
    if str.startswith('\r'):
        print(f'\r[{time.strftime("%Y-%m-%d %H:%M:%S")}] {str[1:]}', end=end, flush=flush)
    else:
        print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {str}', end=end, flush=flush)

if __name__ == "__main__":
    opts = {'debug': False, 'customconfigs': False, 'purge': False}
    configs = []

    # Set arguments
    i = 1
    while i < len(sys.argv):
        if (sys.argv[i].startswith('-')):
            c = sys.argv[i][1]
            if c == 'd' or c == 'v':
                opts['debug'] = True
                i = i + 1
            elif c == 'P':
                opts['purge'] = True
                i = i + 1
            else:
                exit(f'Unknown command line option {sys.argv[i]}')
        else:
            opts['customconfigs'] = True
            configs.append(sys.argv[i])
            if not configs[-1].lower().endswith('.json'):
                configs[-1] += '.json'
            i = i + 1

    if opts['customconfigs'] is False:
        configs = ['config.json']

    # Open file
    for path in configs:
        f = open(path, 'r')
        content = f.read()
        f.close()
        cfg = json.loads(content)
        tp(f'Loaded config file {path}')
        for setcfg in cfg['sets']:
            tp(f"Starting set {setcfg['downloadDir']}")
            set = Set(setcfg, cfg['globalCfg'] if 'globalCfg' in cfg else {}, opts)
            try:
                set.run()
            except KeyboardInterrupt:
                print()
                tp(f"Aborted set early! Press Ctrl+C within the next 5 seconds to exit, otherwise next set will begin.")
                try:
                    time.sleep(5)
                except KeyboardInterrupt:
                    tp('Program completed!')
                    exit()
    tp('Program completed!')
