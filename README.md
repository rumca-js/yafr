# yafr
Yet another feed reader

```
usage: yafr.py [-h] [--timeout TIMEOUT] [--port PORT] [-o OUTPUT_DIR] [--add ADD] [--bookmark] [--unbookmark]
               [--entry ENTRY] [--source SOURCE] [-r] [--force] [--stats] [--cleanup] [--follow FOLLOW]
               [--unfollow UNFOLLOW] [--enable ENABLE] [--disable DISABLE] [--list-bookmarks] [--list-entries]
               [--list-sources] [--init-sources] [--page-details PAGE_DETAILS] [--search SEARCH] [-v] [--db DB]

RSS feed program.

optional arguments:
  -h, --help            show this help message and exit
  --timeout TIMEOUT     Timeout expressed in seconds
  --port PORT           Port, if using web scraping server
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        HTML output directory
  --add ADD             Adds entry with the specified URL
  --bookmark            makes bookmarked
  --unbookmark          makes bookmarked
  --entry ENTRY         Select entry by ID
  --source SOURCE       Select source by ID
  -r, --refresh-on-start
                        Refreshes links, fetches on start
  --force               Force refresh
  --stats               Show table stats
  --cleanup             Remove unreferenced items
  --follow FOLLOW       Follows specific source
  --unfollow UNFOLLOW   Unfollows specific source
  --enable ENABLE       Enables specific source
  --disable DISABLE     Disables specific source
  --list-bookmarks      Prints bookmarks to stdout
  --list-entries        Prints data to stdout
  --list-sources        Lists sources
  --init-sources        Initializes sources
  --page-details PAGE_DETAILS
                        Shows page details for specified URL
  --search SEARCH       Search entries. Example: --search "title=Elon"
  -v, --verbose         Verbose
  --db DB               SQLite database file name
```

# Alternative software

 - https://newsboat.org/index.html
 - https://github.com/guyfedwards/nom
 - https://github.com/iamaziz/TermFeed
 - https://feed2exec.readthedocs.io
 - https://github.com/kpman/newsroom

# Alternative software - GUI

 - https://github.com/FreshRSS/FreshRSS
 - https://github.com/yang991178/fluent-reader
 - https://github.com/samuelclay/NewsBlur
 - https://github.com/stringer-rss/stringer
 - https://github.com/hello-efficiency-inc/raven-reader
 - https://tt-rss.org/
 - https://github.com/nkanaev/yarr
 - ...and more...

# where to find feed urls

most of the times you have to search.

try checking Github, some awesome, curated lists 

 - https://github.com/plenaryapp/awesome-rss-feeds
 - https://github.com/tuan3w/awesome-tech-rss
 - https://github.com/DongjunLee/awesome-feeds
 - https://github.com/foorilla/allainews_sources

Other places

 - https://nownownow.com/
 - https://searchmysite.net/
 - https://downloads.marginalia.nu/
 - https://aboutideasnow.com/
 - https://neocities.org/

# Other things

 - https://github.com/AboutRSS/ALL-about-RSS
 - https://github.com/voidfiles/awesome-rss standards
 
find interesting page, and try to follow it. if page contains valid RSS link this software should be able to follow it
