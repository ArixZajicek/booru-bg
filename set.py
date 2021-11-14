import time
import json
import urllib
from urllib import request
import os
from os.path import exists

class Set:
    def __init__(self, cfg, gcfg, opts):
        self.opts = opts
        # Set defaults if they don't exist.
        for prop in [   ('type', 'search'), ('downloadDir', 'downloads'), ('url', ''), \
                        ('search', []), ('exclude', []), ('minsize', None), ('ratio', None), \
                        ('minscore', None), ('excludeFileTypes', []), ('ignoreBlacklist', False)]:
            if not prop[0] in cfg:
                if 'defaults' in gcfg and prop[0] in gcfg['defaults']:
                    cfg[prop[0]] = gcfg['defaults'][prop[0]]
                else:
                    cfg[prop[0]] = prop[1]
        
        # Now set class values
        self.last_id = None
        self.type = cfg['type']
        if 'blacklist' in gcfg:
            self.blacklist = gcfg['blacklist']
        else:
            self.blacklist = []
        self.download_dir = cfg['downloadDir']
        self.ignore_blacklist = cfg['ignoreBlacklist']
        if 'rootDir' in gcfg:
            self.download_dir = gcfg['rootDir'] + '/' + self.download_dir
        else:
            self.download_dir = './' + self.download_dir
        if not exists(self.download_dir + '/'):
            os.makedirs(self.download_dir + '/')
        
        if self.type == 'search':
            self.tags_excluded = cfg['exclude']
            self.bad_filetypes = cfg['excludeFileTypes']
            if cfg['ratio'] is not None:
                if cfg['ratio'].count(':') == 1:
                    temp = cfg['ratio'].split(':', 1)
                    self.ratio = float(temp[0]) / float(temp[1])
                elif cfg['ratio'].count('/') == 1:
                    temp = cfg['ratio'].split('/', 1)
                    self.ratio = float(temp[0]) / float(temp[1])
                else:
                    try:
                        self.ratio = float(cfg['ratio'])
                    except ValueError:
                        self.ratio = None
            else:
                self.ratio = None
            
            self.make_query(cfg['url'], (cfg['minsize']['width'], cfg['minsize']['height']) if cfg['minsize'] is not None else None, cfg['minscore'], cfg['search'])
            
            
    
    def make_query(self, url, minsize, minscore, search) -> None:
        tags = ''
        # First, use filtering tags for width, height, and score
        count = 0
        if minsize is not None:
            tags = f'width:>={minsize[0]} height:>={minsize[1]}'
            count = 2
        if minscore is not None:
            tags = f'{tags} score:>={minscore}'
            count += 1

        # Now add as many search tags as possible, up to 6.
        while count < 6 and len(search) > 0:
            tags = f'{tags} {search[0].strip()}'
            search = search[1:] if len(search) > 1 else []

        if (len(search) > 1):
            self.tags_required = search[1:]
        else:
            self.tags_required = []

        # Convert tags to a URL sage string
        tags = tags.replace(' ', '+')

        self.req_string = f'{url}/posts.json?tags={tags}&limit=320'

    # Get posts with an ID lower than the last ID searched
    def get_posts(self) -> list:
        page = ''
        if self.last_id is not None:
            page = f'&page=b{self.last_id}'

        req = urllib.request.Request(self.req_string + page, headers={'user-agent': 'Booru-BG/0.0.1'})
        with urllib.request.urlopen(req) as response:
            content = response.read()
            return json.loads(content)["posts"]

    # Perform criteria checking on an individual post
    def verify_post(self, p) -> bool:
        # Check that URL exists (not deleted/taken down)
        if not type(p['file']['url']) is str:
            return False
        
        # Verify file type is not flash, and not a video if not allowed
        if p['file']['ext'] in self.bad_filetypes:
            return False

        # Verify aspect ratio
        if self.ratio is not None and abs(p['file']['width'] / p['file']['height'] - self.ratio) >= 0.01:
            return False

        # flatten post tags
        ptags = []
        for subsection in p['tags']:
            for tag in p['tags'][subsection]:
                ptags.append(tag)

        # Check required tags
        for tag in self.tags_required:
            if not tag in ptags:
                return False
        
        # Check no excluded tags
        for tag in self.tags_excluded:
            if tag in ptags:
                return False
        
        # Check global blacklist tags
        if self.ignore_blacklist is False:
            for tag in self.blacklist:
                if tag in ptags:
                    return False
        
        # All good!
        return True

    # Download the post. Returns false if already exists.
    def download_post(self, p) -> bool:
        if not exists(f"{self.download_dir}/{p['id']}.{p['file']['ext']}"):
            urllib.request.urlretrieve(p['file']['url'].replace('https://', 'http://'), f"{self.download_dir}/{p['id']}.{p['file']['ext']}")
            return True
        else:
            return False

    # Begins downloading.
    def run(self) -> None:
        self.totaldownloads = 0
        self.totalskipped = 0

        if self.type != 'search':
            return

        postcount = -1
        
        # Once no posts are returned in a query, we will stop looping
        while postcount != 0:
            posts = self.get_posts()
            postcount = len(posts)
            if postcount > 0:
                self.last_id = posts[postcount - 1]["id"]

                for p in posts:
                    if self.verify_post(p) is True:
                        if self.download_post(p):
                            if self.opts['debug'] is True:
                                print(f"\r{p['id']} rated {p['score']['total']}: {p['file']['url']}")
                            self.totaldownloads += 1
                        else:
                            if self.opts['debug'] is True:
                                print(f"{p['id']} rated {p['score']['total']}: Already Exists")
                            self.totalskipped += 1
                        if self.opts['debug'] is False:
                            print(f'Downloaded {self.totaldownloads}, skipped {self.totalskipped} existing, last ID is {self.last_id}        ', end='\r', flush=True)
            # Delay is required for API rate limiting
            time.sleep(0.25)
        print()
