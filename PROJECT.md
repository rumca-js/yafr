# PROJECT

 - The primary function of the application is searching.
 - The application searches local SQLite database
 - Search results contain links to web pages.
 - The application does not require an internet connection to search local databases.
 - Internet access is required when fetching databases, sources, or web pages.
 - This instruction should contain brief statements.
 - Do not run unit tests before making changes. You can run them after changes have been done
 - Though database supports Users table, we use only one user

A database is a searchable collection of entries.

 - It is a HTML self-hosted app

# Data
 - webtoolkit for network communication https://github.com/rumca-js/webtoolkit

# SQLite data model

 - The SQLite data model is defined by linkarchivetools.
 - The authoritative model definition is: https://github.com/rumca-js/linkarchivetools/blob/main/linkarchivetools/model/definitions.py

Naming vs Table names
 - Entries - linkdatamodel
 - Sources - sourcedatamodel
 - Search Views - searchview
 - Configuration - configurationentry
 - Visited Entries History - entryvisithistory
 - Entry Transitions History - entrytransitionhistory
 - SearchHistory - search history
 - Read Later - readlater
 - Credentials - credentials (used for email source type)
 - AppLogging - applogging (logs). Follows logging levels
 - SearchView, or Filters - searchview

linkdatamodel table dependencies:
 - linkdatamodel.id = entrycompactedtags.entry_id
 - linkdatamodel.id = socialdata.entry_id
 - linkdatamodel.source_id = sources.id
 - linkdatamodel.id = readlater.entry_id
 - linkdatamodel.id = entryvisithistory.entry_id

source table dependencies:
 - sourcedatamodel.id = sourceoperationaldata.source_id

linkarchivetools business classes (controllers) vs tables. You may propose changes to these classes
 - Entries - linkarchivetools
 - EntryTags - tags logic
 - Sources - sourcedatamodel
 - SourceData - sourceoperationaldata
 - AppLogging - applogging
 - SearchView - searchview
 - CheckLater - readlater
 - BackgroundJob - backgroundjob
 - ConfigurationEntry - configurationentry

# Views
 - EntriesListView - default 'search' google like view
 - EntryDetailView - view showing only one result (entry), similar to YouTube video preview
 - EntryEditScreen - Adds or edits an entry.
 - SourcesListView - view showing sources (RSS channels, etc.)
 - SourceListView - shows one source information
 - SourceRssEditScreen - Edits source
 - SourceEmailEditScreen - Edits source
 - SourceParseEditScreen - Edits source
 - CredentialsScreen - displays credentials information
 - JobsView - view showing jobs
 - LogsView - view showing AppLogging entries
 - EntryRulesScreen - Displays and configures entry rules.
 - AboutScreen - Shows information about the application.
 - UrlPreview - shows preview for link. Link can be passed to it from other places of software
    - it should say if link is blocked, and if it is by which rule
 - DatabaseView - shows database information
 - StatusView - shows status of app, if background task reading jobs is working
 - ConfigurationView - allows user to change configurationentry properties (display style)

It should be indicated if there are problems with Sources, or Jobs, if there are errors by some badges or indicators.

# ConfigurationView
 - DISPLAY_STYLE_LIGHT = "style-light"
 - DISPLAY_STYLE_DARK = "style-dark"

 - DISPLAY_TYPE_STANDARD = "standard"
 - DISPLAY_TYPE_GALLERY = "gallery"
 - DISPLAY_TYPE_SEARCH_ENGINE = "search-engine"
 - DISPLAY_TYPE_CONTENT_CENTRIC = "content-centric"
 - DISPLAY_TYPE_LINKS_ONLY = "links-only"

 - CONFIGURATION_SEARCH_ENGINE = "Search Engine"
 - CONFIGURATION_GALLERY = "Gallery"
 - CONFIGURATION_NEWS = "News"

 click_behavior_modal_window is used to load a modal windoww for preview (for youtube etc.)

## EntriesListView
 - if user did not input anything the input text should be quite big, and in the middle. If user enters anything the search should be above
 - Provides search widget with text input
 - search history is stored in SearchHistory table, when user inputs search, this table data is used to help user select previous texts
 - Provides buttons: to add new entry, to mark all entries as read, to navigate to top
 - Search widget has "Search" button and a button
 - provide "filters" selection to allow search only 'read later' entries
 Filters are read from SQLite table, but if it nos available by default by Date published filter should be used. Always some filter need to be applied
   -- "Visited" filter - entry results should visited entries
   -- "Read Later" filter - entry results should entries marked for read later
   -- "by Date published" - shows entries, but with this order applied (date_published)
   -- "by Votes" - shows entries, but with this order applied (page_rating_votes)
   -- "by Visits" - shows entries, but with this order applied (page_rating_visits)
 - Search supports advanced search capabilities (described later)
 - Search results support page navigation (or dynamic loading of next / prev elements)
 - Selecting an entry opens EntryDetailScreen.
 - should support selection of multiple entries, and perform actions on them (delete)
 - can support lazy loading (but does not have to) if we had many embedded youtube previews, etc
 - user should be able to change display style, or type from this place, or change if clicking on entry should lead into entry.link, or local preview, or if icons should be shown

### EntryListItem - row in EntryListScreen
There are several list styles:
 - Gallery (emphasis on thumbnail, should look like YouTube or TikTok). If entry.thumbnail is not set, or empty, and source.favicon is not, then favicon should be displayed as small icon, just as for Standard display
 - Standard (similar to gallery, but thumbnail is smaller, and on the left, should remind Feed readers
 - Search engine (emphasis on title, and showing actual link. Should look like search engine results)
 - Conent centric - reddit-like. Shows more of description. Allows user to interact with entry, like set its properties.

 Entry Item shall display:
 - entry.thumbnail or source.favicon
 - title (for safety we can display up to characters?)
 - date of publish
 - source.title
 - social data if it is defined for entry (views, followers_count, thumbs etc)
 - tags if it is defined for entry, in format #tag. These should be clickable, should lead into EntryListView with this tag
 - bookmark icon if bookmarked
 - skull indicator if dead
 - language if it is not empty, or not ""

 If thumbnail is not available, then it should be skipped.
 - Visited entries apply configurable visit alpha.
 - Dead entries apply configurable dead alpha.
 - Bookmarked entries, or entries with votes do not apply alpha (remain fully opaque).

## Search
 - Search is performed against the selected database.
 - there should be help somewhere which instructs user about the available syntax
 - Implement search input translation layer. Search should also support following operators:
    -- "=" acts like LIKE Sql operator. E.g. title=youtube shall find all entries with youtube in title
    -- "==" expects right argument to match. E.g. title==youtube shall find all entries with title exactly as youtube
 - Search expressions are translated to the underlying database format.
    -- SQLite databases use SQLite search capabilities.
    -- JSON databases provide equivalent search behavior where possible.
 - Search can match the entry title.
 - Search can match the entry description.
 - Search can support expressions such as:
 - title LIKE '%something%'
 - description LIKE '%something%'
 - Search implementation should use appropriate SQLite indexes where possible.
 - The search implementation should support large databases efficiently.
 - provide ability to support order (at least) by
    -- page rating votes
    -- date created
    -- date published
    -- followers count
    -- stars
    -- page rating visits

## EntryDetailScreen
Displays the details of an entry.

Provides the following actions:
 - Check later (adds or removes entry from Read Later).
 - Vote
 - Edit.
 - Set language
 - Url Preview.
 - Remove.
 - mark active (sets manual_status_code to 200)
 - mark dead (sets manual_status_code to 400)
 - update link data
 - reset link data
 - change publication date

The screen displays, where available:
 - Thumbnail, or video playback frame (if thumbnail is available, if icons are enabled in configuration)
 - Title.
 - Link.
 - Date of publish
 - Tags, followed with pen icon to edit tags
 - Source information
 - Buttons for some operations like: "Check status", "Add vote"
   -- vote allows user to input digit between -100 and 100
 - Description. User should be able to select text in it. Should make https:// links a real links
 - Button to add a comment (with comments). Comments can be edited.
 - Other entry metadata.
 - Entry transition pane. The pane shows entries that the user previously visited from the current entry. Entry transitions are stored in UserEntryTransitionHistory.
 - back button returning to EntryListScreen should not refresh list, nor should scroll to the top, as it does not modify Entries, or results. It should if read later were changed and EntryList is with read later filter, or if EntryList is with sort by Visits

## EntryEditScreen
 - Allows adding a new entry or editing an existing entry.
 - Provides input fields for entry metadata (URL, title, description, tags, author, etc.).

## SourcesListScreen
 - if user did not input anything the input text should be quite big, and in the middle. If user enters anything the search should be above
 - Provides buttons
    - add - prompts user to select source type (SOURCE_TYPE_RSS or SOURCE_TYPE_EMAIL)
    - fetch - visible when any sources is outdated or has consecutive errors and can be refreshed. Prompts user if sources with errors should be refetched
 - Selecting source opens SourceDetailScreen.
 - Provides search widget, similar to EntryListScreen
 - Similarly to EntryListScreen should contain "Search" button with a button to apply filter (order by title, or fetch time)
 - Filters should be by Url, Title, Fetch time. By default by Url filter should be applied. A filter always need to be applied
 - Probably it would have to be a different search widget implementation from EntryListScreen. These can share same base class though
 - Source fetch means that body of page is fetched, should be RSS, entries are read from it, and inserted into linkdatamodel table.
 - If possible fetch/refresh button should spin if sources are being refreshed
 - Supports pull to refresh to reload sources from the active database
 - Displays a linear progress indicator showing sources update/refresh progress when SourceRefreshWorker is running
 - search widget should, just as EntryListScreen support LIKE syntax
 - should support selection of multiple entries, and perform actions on them (delete, refresh)

### SourceListItem - row in SourcesListScreen
 - Displays source thumbnail or favicon
 - Displays source title and URL
 - Displays a red dot badge on the item (top right) when the source requires refresh (outdated fetch)
 - Displays an error badge when consecutive errors occurred on fetch
 - Disabled sources apply configurable dead alpha

## SourceDetailScreen
 - Displays information about a source.
 - Provides following actions:
    -- Fetch / Update
    -- Edit.
    -- Remove.
 - The Fetch action downloads the source content from the internet.
 - The source content is expected to be RSS or a compatible feed.
 - Entries are extracted from the source content.
 - Extracted entries are inserted into the linkdatamodel table.
 - Existing entries should not be duplicated.

## SourceEditScreen
 - Allows adding a new RSS source or editing an existing source.
 - Provides input fields for source title, URL, and enabled status via shared SourceFormPane component.

## SourceEmailEditScreen
 - Allows adding a new Email source or editing an existing Email source.
 - Provides input fields for IMAP server URL, username, and password.
 - Automatically persists credentials into the credentials table and sets Source.credentials_id.
 - Saves changes to the sourcedatamodel table in the active database.
 - Only accessible when the active database is writable.
 - Email sources are supported by webtoolkit/webtoolkit/utils/emailreader. Is something is missing there indicate

## DatabaseScreen
- displays database information
- Provides the following actions:
  -- Edit - edits display name of the database
- Displays the database name.
- Displays the database type.
- Displays the local file information.
- Displays the remote URL, if applicable.
- Displays the date of creation.
- Displays the date of last refresh/update.
- Displays the number of rows in relevant tables.
- Provides an action to clear the search history.
- Provides an action to clear the user's visited entries.
- Provides an action to clear the user's read later entries.
- Provides an action to clear the social data.
- implement pull to refresh data about database
- user should be able to replace database with database from URL. It shall download and replace the database file. Should user restart process then?

## EntryRulesScreen
 - you can use fields: trigger_rule_url, rule_name, enabled, priority, block, trust, auto_tag, apply_age_limit, source_id. Other fields do not have to be used right now
 - trigger_rule_url supports re syntax ".*reddit.com.*" should work
 - multiple rules can be defined in a single rule, eg. ".*reddit.com.*, .*github.com.*"

# JobsView
 - displays list of jobs
 - allows to create a job
 - user can select jobs to remove, or pause, or resume
 - user should be able to select order of jobs (by enabled, date_created, errors)
 - user should be able to filter by type (infos, errors, warnings, etc)

# Browsing
 - Every entry visit is recorded (if configured so).
 - Visit information is stored in the UserEntryVisitHistory SQLite table (`entryvisithistory`).
 - The application can display the user's visited entries.
 - The application can clear the user's visit history.
 - Entries can be saved to read later, stored in the `readlater` SQLite table.
 - The application can display and clear the user's read later entries.
 - When EntryDetailScreen is visited, it contains pane below to which entries user transitions to.
 - Entry transitions are maintained by UserEntryTransitionHistory SQLite table (`entrytransitionhistory`).

## Sources refresh
 - disabled sources should be skipped
 - sources that were fetched earlier than hour since source.date\_fetch should be skipped
 - should use order of sources by last fetched (or that never have been fetched)
 - should change date\_fetch, but only after attempt to read source has been made
 - if database is change, the worker should not process any older data for previous database
 - source.SourceOperationalDataRepository has page_hash (entire source hash), and body_hash (body, or entries hash). If it is not different than previous one, you can skip refresh, and mark as read
 - SourceOperationalDataRepository stores the amount of source entries, consecutive_errors contain the amount of consecutive errors. Is cleared when valid response is received.
 - source is marked as read when it's response is valid, if it is not consecutive errors counter is incremented

# Jobs
 - There should be a background task. It should handle processing of jobs.
 - use information linkarchivetools.BackgroundJob to identify which kind of jobs there are
 - when there are no jobs, then check if any of source requires refresh

# Code Requirements
 - prefer having small server functions that returns JSON data.
    -- for example /api/source-disable/123 should disable source 123, and provide JSON response
 - provide interactive UI, that fetches data when necessary
 - use bootstrap 5, you can use javascript, jQuery
 - pages should be quite responsive. Not all page contents need to be refreshed when action is performed, some sections can be fetched as needed
 - prefer using css files for styles
 - when removing rows remember to remove rows that depend on it. For example some tables depend on linkdatamodel entries
 - Use small functions.
 - Keep classes small and focused.
 - Divide functionality into small files.
 - Give each class a clear responsibility.
 - Avoid duplicating database access logic.
 - Keep UI code separate from database and networking code.
 - Use repositories for database access.
 - Use appropriate abstractions for downloading files and fetching web pages.
 - Provide API documentation using Doxygen-style comments.
 - Document public classes.
 - Document public methods.
 - Document non-obvious implementation decisions.
 - Use descriptive names for classes, methods, and variables.
 - Prefer simple implementations over unnecessary abstractions.
 - Prefer simiplicity of calls and structure
 - When handling SQLite tables, then apply some storage limits. For example, we may store history of user searches. Do not allow for infinite growth, but allow only a fixed amount of entries to be added. New entries replace old ones. One exception is Entries. There is no limit for them

# General Requirements
 - The application must remain usable when the device is offline.
 - use reasonable directory structure. UI elements, or components should have their directories, controller logic should be separated, model, etc.
 - Network operations must not block the UI thread.
 - Network failures must be handled gracefully.
 - Use webtoolkit.Url to read links, RSS sources, parse sources
 - Database failures must be reported to the user (eg. SQLite errors).
 - Long-running operations must expose their current state.
 - Destructive operations must require user confirmation.
 - The application must preserve locally available databases when network operations fail.
 - The application must not modify a local database unless the user explicitly requests an update or refresh.
 - If a modification control cannot be hidden, it must be disabled.
 - if network is disabled network related widgets, like buttons should be not visible
