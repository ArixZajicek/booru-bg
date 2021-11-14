# booru-bg

Bulk-download images from popular booru sites. Filter by tags, blacklist, size, ratio, score, and filetype. Create multiple search queries that each download into their own folders.
## Requirements
Uses the urllib module, so you may need to run `pip install urllib`.

## config.json
You must create a config.json file in the project's root directory. See example.json for a typical use-case or follow along below for specifics.

The config.json file has two sections, outlined below. Most all values are optional, but you must specify a `url` in either the default set values or in each set individually.

### Global Configs
Typically, config.json would include a `globalCfg` object with a `blacklist` array, `rootDir`, and `defaults` object. Each option is shown with its default value (the value that will be used if the property does not exist).

`"blacklist": []` - An array of tags to filter out from ALL sets, assuming the set does not have `"ignoreBlacklist": true`.

`"rootDir": "."` is just the base directory prepended to all sets' download directories.

`"defaults": {...}` - The default parameters for all sets, to be used when omitted from each set below. Will use built-in parameters if there is no value here or in a set.

### Sets
config.json must include a `sets` array that contains each set that you wish to bulk download. Omitting a property will resort to the value found in `defaults`, or if it doesn't exist there, it will use the built-in default. Each set object contains the following properties (defaults listed):

`"type": "search"` - Type of set. Reserved for future use, but must be set to `"search"` for the set to be active. (Set to any other value to skip the set temporarily).

`"downloadDir": "downloads"` - Directory to download this set's filed.

`"url": **No Default**` - Base URL, must be listed in the set or in defaults.

`"search": []` - Search tags - all posts must include these tags.

`"exclude": []` - Exclude tags, all posts must not include these tags. Note, this does not override the `blacklist` parameter but rather works in conjunction with it if `ignoreBlacklist` is not `true`.

`"minsize": null` - Minimum dimensions. Must either be null, or contain an object of the form `{"width": 1920, "height": 1080}`.

`"ratio": null` - Image ratio. Must contain a string of the form `"16:9"`, `"16/9"`, or a decimal number `1.78`. Tolerance is +/- 0.01.

`"minscore": null` - Minimum score of the post.

`"excludeFileTypes": []` - Used to exclude filetypes like `swf` and `webm` in cases where you only desire an image. Do not include the leading `.`, just the extension.

`"ignoreBlacklist": false` - Used to ignore the global blacklist. Useful in situations where you want to download a pool and don't want to skip over any sequential images that you might otherwise have blacklisted.

## Running
`python3 main.py`
Run with no arguments to use the default file, config.txt.

`python3 main.py config1.json [config2.json [...]]`
Specify one or more config files to run instead of the default config.json.
