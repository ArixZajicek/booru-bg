# booru-bg

Bulk-download images from popular booru sites. Filter by tags, blacklist, size, ratio, score, and filetype. Create multiple search queries that each download into their own folders.
## Requirements
Uses the urllib module, so you may need to run `pip install urllib`.

## How to Use
1. Create a config.json in the project's root directory. 
	- See example.json for templating. When you don't want to filter by a value, use either `null` or `[]` where appropriate. See the second example in example.json. This would download everything with no filters applied.
2. Run `python3 main.py`.
3. Wait for downloads to complete.
