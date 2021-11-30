from cfgtypes import *
from copy import deepcopy
import time
import json
import requests
import os
from os.path import exists
from concurrent.futures import ThreadPoolExecutor

class Set:
    c: SetConfig
    """ Local set configuration """
    gc: GlobalConfig
    """ Global configuration """
    dir: str
    """ Download directory (root + set) """
    reqStr: str
    """ Base request string for API """
    nonmatchingFiles: list
    """ List of files that are not found from the search. """
    tagsRequired: list
    """ List of required tags that didn't make it into the query due to search limits """

    def __init__(self, setcfg: SetConfig, globalcfg: GlobalConfig):
        # Set the options dict which contains command-line arg settings
        self.c = setcfg
        self.gc = globalcfg

        # Helper variables
        self.lastId = None
        self.lastApiCall = 0
        self.dupFound = False

        # Combine global root dir and local set dir into download directory
        self.dir = self.gc.rootDir + '/' + self.c.downloadDir
        
        # Create the download directory
        if not exists(self.dir + '/'):
            os.makedirs(self.dir + '/')
        
        # Index all existing files in the directory if we need to track them
        if self.c.moveNonmatching or self.c.deleteNonmatching:
            self.c.stopEarly = False # Must not stop early when indexing all files
            def file_is_ours(file: str):
                if file.count('.') != 1: return False
                name, ext = file.split('.')
                return name.isnumeric() and ext in ['png', 'jpeg', 'jpg', 'gif', 'webm', 'swf']
            self.nonmatchingFiles = list(filter(file_is_ours, os.listdir(self.dir + '/')))

        # Create the request query from the set options
        self.reqStr = self.generate_query()
            
    def generate_query(self) -> str:
        """ Create the request string using stored config values. Will attempt to use the maximum number of
        filter strings (6). """
        tags = ''

        search = deepcopy(self.c.search)

        # First, use filtering tags for width, height, score, and ratio
        count = 0
        if self.c.minsize is not None:
            tags = f'width:>={self.c.minsize.width} height:>={self.c.minsize.height}'
            count = 2
        if self.c.minscore is not None:
            tags = f'{tags} score:>={self.c.minscore}'
            count += 1
        if self.c.ratioFloat is not None:
            tags = f'{tags} ratio:{round(self.c.ratioFloat, 2)}'
            count += 1

        # Now add as many search tags as possible, up to 6.
        while count < 6 and len(search) > 0:
            tags = f'{tags} {search[0].strip()}'
            search = search[1:] if len(search) > 1 else []

        # Any remaining search tags go into the "tagsRequired" list
        if (len(search) >= 1):
            self.tagsRequired = search[1:]
        else:
            self.tagsRequired = []

        # Convert tags to a URL safe string
        tags = tags.replace(' ', '+')

        # Return the request string (320 is max page size).
        return f'{self.c.url}/posts.json?tags={tags}&limit=320'

    def get_posts(self) -> list:
        """ Get posts with an ID lower than the last ID searched """

        # Follow rate-limit requirements and wait a minimum of 1 second between API calls
        now = time.time()
        if now - self.lastApiCall < 1:
            time.sleep(1 - (now - self.lastApiCall))
        self.lastApiCall = time.time()

        # Page string if needed
        page = ''
        if self.lastId is not None:
            page = f'&page=b{self.lastId}'
        
        # Use current session to get response.
        response = self.session.get(self.reqStr + page)
        if response.status_code == 200:
            return json.loads(response.content)["posts"]
        else:
            exit(f'\nError!\nResponse ({response.status_code}):\n{response.text}')

    """ Perform criteria checking on an individual post"""
    def verify_post(self, p) -> bool:
        # Check that URL exists (not deleted/taken down/hidden)
        if not type(p['file']['url']) is str:
            return False
        
        # Verify file type is allowed
        if p['file']['ext'] in self.c.excludeFileTypes:
            return False

        # flatten post tags
        ptags = []
        for subsection in p['tags']:
            for tag in p['tags'][subsection]:
                ptags.append(tag)

        # Check required tags
        for tag in self.tagsRequired:
            if not tag in ptags:
                return False
        
        # Check no excluded tags
        for tag in self.c.exclude:
            if tag in ptags:
                return False
        
        # Check global blacklist tags
        if self.c.ignoreBlacklist is False:
            for tag in self.gc.blacklist:
                if tag in ptags:
                    return False
        
        # All good!
        return True

    def download_post(self, p) -> None:
        """ Download the post or returns false if already exists. """
        # Only download if file does not exist
        if not exists(f"{self.dir}/{p['id']}.{p['file']['ext']}"):
            response = self.session.get(p['file']['url'])
            open(f"{self.dir}/{p['id']}.{p['file']['ext']}", 'wb').write(response.content)
            self.totaldownloads += 1
        else:
            self.totalskipped += 1
            self.dupFound = True
        if time.time() - self.lastPrintTime > 0.5:
            tp(f'\rD{self.totaldownloads}/S{self.totalskipped}/@{p["id"]}   ', end='', flush=True)
            self.lastPrintTime = time.time()


    def run(self) -> None:
        """ Begins the fetch and download loop. """
        # Helper variables for tracking stuff.
        self.totaldownloads = 0
        self.totalskipped = 0
        self.lastPrintTime = 0
        
        # TODO: Implement types
        if self.c.type != 'search':
            return
        
        # Create a new session object so we don't have to do an SSL handshake every time.
        self.session = requests.Session()
        self.session.headers.update({'user-agent': 'Booru-BG/0.0.1'})

        # Add auth parameters to session if they exist
        if self.c.auth is not None:
            self.session.auth = (self.c.auth.username, self.c.auth.password)
        
        # Outer loop does one request each time.
        postcount = -1
        while postcount != 0 and not (self.c.stopEarly and self.dupFound):
            all_posts = self.get_posts()
            posts = list(filter(lambda p: self.verify_post(p), all_posts))
            
            # Index posts found in this search so they do not get removed
            if self.c.moveNonmatching or self.c.deleteNonmatching:
                for p in posts:
                    fname = f"{p['id']}.{p['file']['ext']}"
                    if fname in self.nonmatchingFiles:
                        self.nonmatchingFiles.remove(fname)

            # Count number of posts
            postcount = len(posts)
            if postcount > 0:
                # Save ID of last post in this set so we can get the next page next time.
                self.lastId = posts[-1]["id"]
                # Use multithreading to download all posts
                with ThreadPoolExecutor(max_workers=self.gc.simultaneousDownloads) as pool:
                    pool.map(self.download_post, posts)
        
        # Set download finished.
        tp(f'\rD{self.totaldownloads}/S{self.totalskipped} - Finished   ')

        # If we stopped because a duplicate was found, let user know.
        if (self.c.stopEarly and self.dupFound):
            tp(f'Stopped early, duplicate found.')
        
        # Purge/Delete nonmatching files if option is set
        if self.c.moveNonmatching:
            if len(self.nonmatchingFiles) > 0:
                tp(f"Beginning move of {len(self.nonmatchingFiles)} nonmatching files...")
                if not exists(self.dir + '/purged/'):
                    os.makedirs(self.dir + '/purged/')
                prog = 0
                for file in self.nonmatchingFiles:
                    os.rename(self.dir + '/' + file, self.dir + '/purged/' + file)
                    prog += 1
                    tp(f'\rMoved {prog} of {len(self.nonmatchingFiles)}.', end='', flush=True)
        elif self.c.deleteNonmatching:
            if len(self.nonmatchingFiles) > 0:
                tp(f"Beginning deletion of {len(self.nonmatchingFiles)} nonmatching files...")
                prog = 0
                for file in self.nonmatchingFiles:
                    os.remove(self.dir + '/' + file)
                    prog += 1
                    tp(f'\Deleted {prog} of {len(self.nonmatchingFiles)}.', end='', flush=True)

def tp(str, end='\n', flush=False):
    if str.startswith('\r'):
        print(f'\r[{time.strftime("%Y-%m-%d %H:%M:%S")}] {str[1:]}', end=end, flush=flush)
    else:
        print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {str}', end=end, flush=flush)