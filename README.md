# booru-bg
Bulk-download images from popular image board sites. This was designed primarily around finding wallpapers so image dimension options are included. Filter by tags, blacklist, size, ratio, score, and filetype. Create multiple search queries that each download into their own folders.

## Requirements
Requires Python 3 and the `requests` module.

## config.json
You must create a config.json file in the project's root directory. See example.json for a typical use-case or follow along below for specifics.

The config.json file has two sections, outlined below. Most all values are optional, but you must specify a `url` in either the default set values or in each set individually.

### Global Configs
Typically, config.json would include a `globalCfg` object. Each option is shown with its default value (the value that will be used if the property does not exist).

`"blacklist": []` - An array of tags to filter out from ALL sets, assuming the set does not have `"ignoreBlacklist": true`.

`"rootDir": "."` is just the base directory prepended to all sets' download directories.

`"simultaneousDownloads": 8` - The maximum number of concurrent downloads. Increase this if you have a fast PC and internet, decrease on limited devices or bandwidth.

`"defaults": {...}` - The default parameters for all sets, to be used when omitted from each set below. Will use built-in parameters if there is no value here or in a set.

### Sets
config.json must include a `sets` array that contains each set that you wish to bulk download. Omitting a property will resort to the value found in `defaults`, or if it doesn't exist there, it will use the built-in default. Each set object contains the following properties (defaults listed):

`"type": "search"` - Type of set. Reserved for future use, but must be set to `"search"` for the set to be active. (Set to any other value to skip the set temporarily).

`"downloadDir": "downloads"` - Directory to download this set's filed.

`"url": [No Default]` - Base URL, must be listed in the set or in defaults.

`"auth": null` - HTTP Basic Auth credentials. Can either be `null` or `{"username": "your username here", "password": "your password or API token here"}`. While this script does not modify your account in any way, some sites may require an authenticated user to view some content. Additionally, some sites require you to enable API access and use an API token as your password instead of your regular one. Check in your account settings for more info.

`"search": []` - Search tags - all posts must include these tags.

`"exclude": []` - Exclude tags, all posts must not include these tags. Note, this does not override the `blacklist` parameter but rather works in conjunction with it. If `ignoreBlacklist` is `true`, then only this list is used.

`"minsize": null` - Minimum dimensions. Must either be null, or contain an object of the form `{"width": 1920, "height": 1080}`.

`"ratio": null` - Image ratio. Must contain a string of the form `"16:9"`, `"16/9"`, or a decimal number `1.78`. Tolerance is +/- 0.01.

`"minscore": null` - Minimum score of the post.

`"excludeFileTypes": []` - Used to exclude filetypes like `swf` and `webm` in cases where you only desire an image. Do not include the leading `.`, just the extension.

`"ignoreBlacklist": false` - Used to ignore the global blacklist. Useful in situations where you want to download a pool and don't want to skip over any sequential images that you might otherwise have blacklisted.

`"stopEarly": false` - Used to stop immediately when an existing post is found. The default is a thorough search to make sure every file in the search is downloaded, but if you only care about the most recent ones, you can set this to true to stop searching as soon as you reach a post you've already downloaded.

`"moveNonmatching": false` - Used to move all non-matching files out of a directory and into a 'purged' subfolder. Useful when you want to modify a search slightly and remove any files that no longer match the search. While this attempts to only move media files it could have created, there is no guarantee that it won't affect other files. Use with caution. Additionally, this currently does not work when multiple sets output into the same download folder. Weird behavior WILL occur!

`"deleteNonmatching": false` - Same as `moveNonmatching` but deletes these files instead of simply moving them. The same warnings thus apply, use with even more caution!!

## Running
`python3 main.py [options]`
Run with no arguments to use the default file, config.json.

`python3 main.py [options] config1.json [config2.json [...]]`
Specify one or more config files to run instead of the default config.json.

### Options
`-d` or `-v` - Debug output, not currently used.

`-P` - Enable `moveNonmatching` temporarily for all sets. See warning above.
