# yafr
Yet another feed reader

```
usage: yafr.py [-h] [--timeout TIMEOUT] [--port PORT] [-o OUTPUT_DIR]
               [--print PRINT] [-r] [--force] [--stats] [--cleanup]
               [--follow FOLLOW] [--unfollow UNFOLLOW] [--list-sources]
               [--init-sources] [-v] [--db DB]

Data analyzer program

options:
  -h, --help            show this help message and exit
  --timeout TIMEOUT     Timeout expressed in seconds
  --port PORT           Port
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        HTML output directory
  --print PRINT         Print entries to stdout
  -r, --refresh-on-start
                        Refreshes on start
  --force               Forces refresh
  --stats               Show statistics
  --cleanup             Remove unreferenced items
  --follow FOLLOW       Follows specific url
  --unfollow UNFOLLOW   Unfollows specific url
  --list-sources        Lists sources
  --init-sources        Initializes sources
  -v, --verbose         Verbose
  --db DB               SQLite database file
```
# Alternative software

https://github.com/nkanaev/yarr

https://github.com/goniszewski/grimoire

newsboat, etc.

# where to find feed urls

most of the timesnyou have to search.

try checking Github, some awesome, curated lists https://github.com/plenaryapp/awesome-rss-feeds

find interesting page, and try to follow it. if page contains valid RSS link this software should be able to follow it
