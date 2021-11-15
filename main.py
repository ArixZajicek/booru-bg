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
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {str}', end=end, flush=flush)

if __name__ == "__main__":
    opts = {'debug': False, 'customconfigs': False, 'username': None, 'password': None}
    configs = []

    # Set arguments
    i = 1
    while i < len(sys.argv):
        if (sys.argv[i].startswith('-')):
            c = sys.argv[i][1]
            if c == 'd' or c == 'v':
                opts['debug'] = True
                i = i + 1
            elif c == 'u' and i < len(sys.argv) - 1:
                opts['username'] = sys.argv[i + 1]
                i = i + 2
            elif c == 'p' and i < len(sys.argv) - 1:
                opts['password'] = sys.argv[i + 1]
                i = i + 2
            else:
                exit(f'Unknown command line option {sys.argv[i]}')
        else:
            opts['customconfigs'] = True
            configs.append(sys.argv[i])
            i = i + 1

    # Prompt for password if username given but no password
    if opts['username'] is not None and opts['password'] is None:
        # sys.stdout.write("\033[F") # Cursor up one line
        opts['password'] = input(f'Please enter the password for user {opts["username"]}: ')

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
