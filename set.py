from posixpath import split
import time
import json
import requests
import os
from os.path import exists
from concurrent.futures import ThreadPoolExecutor

class Set:
    def __init__(self, cfg, gcfg, opts):
        self.opts = opts
        # Set defaults if they don't exist.
        for prop in [   ('type', 'search'), ('downloadDir', 'downloads'), ('url', ''), ('auth', None), \
                        ('search', []), ('exclude', []), ('minsize', None), ('ratio', None), ('stopEarly', False), \
                        ('minscore', None), ('excludeFileTypes', []), ('ignoreBlacklist', False)]:
            if not prop[0] in cfg:
                if 'defaults' in gcfg and prop[0] in gcfg['defaults']:
                    cfg[prop[0]] = gcfg['defaults'][prop[0]]
                else:
                    cfg[prop[0]] = prop[1]
        
        # Now set class values
        self.last_id = None
        self.last_api_call = 0
        self.auth = cfg['auth']
        self.type = cfg['type']
        if 'simultaneousDownloads' in gcfg:
            self.dlworkers = gcfg['simultaneousDownloads']
        else:
            self.dlworkers = 8
        if 'blacklist' in gcfg:
            self.blacklist = gcfg['blacklist']
        else:
            self.blacklist = []
        self.download_dir = cfg['downloadDir']
        self.ignore_blacklist = cfg['ignoreBlacklist']
        self.stop_early = cfg['stopEarly']
        self.dup_found = False
        if 'rootDir' in gcfg:
            self.download_dir = gcfg['rootDir'] + '/' + self.download_dir
        else:
            self.download_dir = './' + self.download_dir
        if not exists(self.download_dir + '/'):
            os.makedirs(self.download_dir + '/')
        elif self.opts['purge']:
            self.stop_early = False
            def file_is_ours(file: str):
                if file.count('.') != 1: return False
                name, ext = file.split('.')
                return name.isnumeric() and ext in ['png', 'jpeg', 'jpg', 'gif', 'webm', 'swf']
            self.files_to_purge = list(filter(file_is_ours, os.listdir(self.download_dir)))

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
        if self.ratio is not None:
            tags = f'{tags} ratio:{round(self.ratio, 2)}'
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
        # Follow rate-limit requirements and wait a minimum of 1 second between API calls
        now = time.time()
        if now - self.last_api_call < 1:
            time.sleep(1 - (now - self.last_api_call))
        self.last_api_call = time.time()

        # Page string if needed
        page = ''
        if self.last_id is not None:
            page = f'&page=b{self.last_id}'
        
        # Use current session to get response.
        response = self.session.get(self.req_string + page)
        if response.status_code == 200:
            return json.loads(response.content)["posts"]
        else:
            exit(f'\nError!\nResponse ({response.status_code}):\n{response.text}')

    # Perform criteria checking on an individual post
    def verify_post(self, p) -> bool:
        # Check that URL exists (not deleted/taken down/hidden)
        if not type(p['file']['url']) is str:
            return False
        
        # Verify file type is allowed
        if p['file']['ext'] in self.bad_filetypes:
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
    def download_post(self, p) -> None:
        if not exists(f"{self.download_dir}/{p['id']}.{p['file']['ext']}"):
            response = self.session.get(p['file']['url'])
            open(f"{self.download_dir}/{p['id']}.{p['file']['ext']}", 'wb').write(response.content)
            self.totaldownloads += 1
        else:
            self.totalskipped += 1
            self.dup_found = True
        if time.time() - self.last_print_time > 0.5:
            self.tp(f'\rD{self.totaldownloads}/S{self.totalskipped}/@{p["id"]}   ', end='', flush=True)
            self.last_print_time = time.time()


    # Begins downloading.
    def run(self) -> None:
        self.totaldownloads = 0
        self.totalskipped = 0
        self.last_print_time = 0
        
        if self.type != 'search':
            return

        postcount = -1
        self.session = requests.Session()
        self.session.headers.update({'user-agent': 'Booru-BG/0.0.1'})
        if self.auth is not None:
            self.session.auth = (self.auth['username'], self.auth['password'])
        while postcount != 0 and not (self.stop_early and self.dup_found):
            raw_posts = self.get_posts()
            posts = list(filter(lambda p: self.verify_post(p), raw_posts))
            
            if self.opts['purge']:
                for p in posts:
                    fname = f"{p['id']}.{p['file']['ext']}"
                    if fname in self.files_to_purge:
                        self.files_to_purge.remove(fname)

            postcount = len(posts)
            if postcount > 0:
                self.last_id = posts[-1]["id"]
                with ThreadPoolExecutor(max_workers=8) as pool:
                    pool.map(self.download_post, posts)
            
        print()
        if (self.stop_early and self.dup_found):
            self.tp(f'Stopped early, duplicate found.')
        
        if self.opts['purge']:
            if len(self.files_to_purge) > 0:
                self.tp(f"Beginning purge of {len(self.files_to_purge)} nonmatching files...")
                if not exists(self.download_dir + '/purged/'):
                    os.makedirs(self.download_dir + '/purged/')
                prog = 0
                for file in self.files_to_purge:
                    os.rename(self.download_dir + '/' + file, self.download_dir + '/purged/' + file)
                    prog += 1
                    self.tp(f'\rPurged {prog} of {len(self.files_to_purge)}.', end='', flush=True)
                self.tp(f'Purged {len(self.files_to_purge)} file{"s" if len(self.files_to_purge) != 1 else ""}.')
            else:
                self.tp('No files were purged.')
    
    def tp(self, str, end='\n', flush=False):
        if str.startswith('\r'):
            print(f'\r[{time.strftime("%Y-%m-%d %H:%M:%S")}] {str[1:]}', end=end, flush=flush)
        else:
            print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {str}', end=end, flush=flush)

    def dp(self, str, end='\n', flush=False):
        if self.opts['debug']:
            self.tp(str, end, flush)
