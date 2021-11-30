
import json


class CommandOptions:
	debug: bool = False
	""" Whether or not debug output should be generated """

	configs: list = ['config.json']
	""" List of configs to use """

	useCustomConfigs: bool = False

	purge: bool = False
	""" Whether or not a purge should be done on this run (moveNonmatching) """

	def __init__(self, args) -> None:
		""" Initialize with given command line arguments arguments """
		# Set arguments
		i = 1
		while i < len(args):
			if (args[i].startswith('-')):
				c = args[i][1]
				if c == 'd' or c == 'v':
					debug = True
					i = i + 1
				elif c == 'P':
					purge = True
					i = i + 1
				else:
					exit(f'Unknown command line option {args[i]}')
			else:
				if self.useCustomConfigs is False:
					configs = []
					self.useCustomConfigs = True
				configs.append(args[i])
				if not configs[-1].lower().endswith('.json'):
					configs[-1] += '.json'
				i = i + 1

class SiteAuthentication:
	username: str
	""" Username for HTTP Basic Auth """
	password: str
	""" Password for HTTP Basic Auth """

class Dimensions:
	width: int
	""" Media width in pixels """
	height: int
	""" Media height in pixels """

class SetConfig:
	url: str = None
	""" The site's base URL"""

	type: str = 'search'
	""" Set type (only search is implemented, all others disable the set) """

	downloadDir: str = 'downloads'
	""" Download directory relative to global root """

	auth: SiteAuthentication = None
	""" HTTP Basic Auth Parameters """

	search: list = []
	""" List of required search terms """

	exclude: list = []
	""" List of terms to exclude """

	minsize: Dimensions = None
	""" Minimum media dimensions """

	ratio: str = None
	""" Ratio of media, in string form """

	ratioFloat: float = None
	""" Ratio of media, in floating point form """

	minscore: int = None
	""" Minimum user rating of all posts """

	excludeFileTypes: list = []
	""" Filetypes to exclude """

	ignoreBlacklist: bool = False
	""" Whether this set should ignore the blacklist """

	stopEarly: bool = False
	""" Whether the download should stop upon the first duplicate downloaded """

	moveNonmatching: bool = False
	""" Whether non-matching files should be moved to a 'nonmatching' subdirectory """

	deleteNonmatching: bool = False
	""" Whether non-matching files should be deleted entirely """

	def addValues(self, json_cfg):
		""" Updates set's values with all values provided in the given jsonobj """

		# Loop through dumb values first
		for k in json_cfg:
			if k in SetConfig.__dict__:
				self.__dict__[k] = json_cfg[k]
		
		# Now do objects if they exist
		if 'auth' in json_cfg:
			self.auth = SiteAuthentication()
			self.auth.username = json_cfg['auth']['username']
			self.auth.password = json_cfg['auth']['password']

		if 'minsize' in json_cfg:
			self.minsize = Dimensions()
			self.minsize.width = json_cfg['minsize']['width']
			self.minsize.height = json_cfg['minsize']['height']

		# Ratio is a little more complicated because it must be calculated
		if self.ratio is not None:
			if self.ratio.count(':') == 1:
				temp = self.ratio.split(':', 1)
				self.ratioFloat = float(temp[0]) / float(temp[1])
			elif self.ratio.count('/') == 1:
				temp = self.ratio.split('/', 1)
				self.ratioFloat = float(temp[0]) / float(temp[1])
			else:
				try:
					self.ratioFloat = float(self.ratio)
				except ValueError:
					self.ratioFloat = None
		else:
			self.ratioFloat = None

class GlobalConfig:
	rootDir: str = '.'
	""" Root download directory """

	blacklist: list = []
	""" Global tag blacklist """

	simultaneousDownloads: int = 8
	""" Simultaneous download limit """

	defaults: SetConfig = SetConfig()
	""" Set defaults (fallback in case a set does not have values) """

	def __init__(self, json_gcfg) -> None:
		if 'simultaneousDownloads' in json_gcfg:
			self.simultaneousDownloads = json_gcfg['simultaneousDownloads']
		
		if 'blacklist' in json_gcfg:
			self.blacklist = json_gcfg['blacklist']
		
		if 'rootDir' in json_gcfg:
			self.rootDir = json_gcfg['rootDir']
		
		if 'defaults' in json_gcfg:
			self.defaults.addValues(json_gcfg['defaults'])
