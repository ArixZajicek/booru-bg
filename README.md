# booru-bg

Bulk-download images from popular image board sites. This was designed primarily around finding wallpapers so image dimension options are included. Filter by tags, blacklist, size, ratio, score, and filetype. Create multiple search queries that each download into their own folders.
## Requirements
Requires Python 3.

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

`"auth": None` - HTTP Basic Auth credentials. Can either be `None` or `{"username": "your username here", "password": "your password or API token here"}`. While this script does not modify your account in any way, some sites may require an authenticated user to view some content. Additionally, some sites require you to enable API access and use an API token as your password instead of your regular one. Check in your account settings for more info.

`"search": []` - Search tags - all posts must include these tags.

`"exclude": []` - Exclude tags, all posts must not include these tags. Note, this does not override the `blacklist` parameter but rather works in conjunction with it if `ignoreBlacklist` is not `true`.

`"minsize": null` - Minimum dimensions. Must either be null, or contain an object of the form `{"width": 1920, "height": 1080}`.

`"ratio": null` - Image ratio. Must contain a string of the form `"16:9"`, `"16/9"`, or a decimal number `1.78`. Tolerance is +/- 0.01.

`"minscore": null` - Minimum score of the post.

`"excludeFileTypes": []` - Used to exclude filetypes like `swf` and `webm` in cases where you only desire an image. Do not include the leading `.`, just the extension.

`"ignoreBlacklist": false` - Used to ignore the global blacklist. Useful in situations where you want to download a pool and don't want to skip over any sequential images that you might otherwise have blacklisted.

`"stopEarly": false` - Used to stop immediately when an existing post is found. The default is a thorough search to make sure every file in the search is downloaded, but if you only care about the most recent ones, you can set this to true to stop searching as soon as you reach a post you've already downloaded.

## Running
`python3 main.py [options]`
Run with no arguments to use the default file, config.txt.

`python3 main.py [options] config1.json [config2.json [...]]`
Specify one or more config files to run instead of the default config.json.

### Options
`-d or -v` - Debug output, not currently used.

`-P` - Purge files that no longer match into a `purged` subfolder to be deleted as desired. Note! While this application makes an attempt to only move files it could have created, there is no guarantee that it won't move other files. Namely, the best it can do is verify that the name is all numbers and the extension is recognized, but that's it. Therefore, be careful if doing this in a shared folder. Additionally, if multiple sets output into the same folder, weird behavior WILL occur and files that should be there will be purged. Use with caution!!
