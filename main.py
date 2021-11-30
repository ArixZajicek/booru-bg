from copy import deepcopy
from set import Set, tp
from cfgtypes import *
import json
import sys
import time


""" The purpose of this code is to query an image board for all images of a
certain size or larger, and a certain aspect ratio. A couple tags may
be searched for in addition, then this script further sorts through, 
excluding blacklisted tags and posts that do not contain other required
tags. See example.json for all options. """

if __name__ == "__main__":
	# Parse command line options
	cmdopts = CommandOptions(sys.argv)

	# Open config JSON files one by one
	for path in cmdopts.configs:
		# Load file content into json object
		f = open(path, 'r')
		json_cfg = json.loads(f.read())
		f.close()
		tp(f'Loaded config file {path}')

		# Parse global config first
		gcfg = GlobalConfig(json_cfg['globalCfg'])
		gcfg.defaults.moveNonmatching = (gcfg.defaults.moveNonmatching or cmdopts.purge)

		for json_setcfg in json_cfg['sets']:
			# Now load set config and add values, if any.
			setcfg = deepcopy(gcfg.defaults)
			setcfg.addValues(json_setcfg)

			tp(f"Starting set {setcfg.downloadDir}")
			set = Set(setcfg, gcfg)
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