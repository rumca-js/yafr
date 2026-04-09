let worker = null;
let db = null;
let object_list_data = null;   // all objects lists
let system_initialized = false;

let view_display_type = "gallery";
let view_display_style = "style-light";
let view_show_icons = true;
let view_small_icons = false;
let user_age = 1;
let debug_mode = false;

let entries_direct_links = true;
let highlight_bookmarks = false;
let perform_auto_search = true;
let click_behavior_modal_window = true;
let sort_function = "-page_rating_votes"; // page_rating_votes, date_published
let default_page_size = 200;

let entries_visit_alpha=1.0;
let entries_dead_alpha=0.5;


function getDefaultFileName() {
    return;
}


function getEntryAPI() {
   return `/api/entries`;
}


function getEntryEditAPI() {
   return `/entry-edit`;
}


function getEntryTagAPI() {
   return `/entry-tag`;
}


function getEntryVoteAPI() {
   return `/entry-vote`;
}


function getEntryUpdateAPI() {
   return `/entry-update`;
}


function getEntryResetAPI() {
   return `/entry-reset`;
}


function getEntryRemoveAPI() {
   return `/remove-entry`;
}


function getEntryLocalLink(entry) {
    return `?entry_id=${entry.id}`;
}


function getHomeLocation() {
    return "/";
}


function getFileList() {
    return [
    ];
}


function getDefaultFileLocation() {
    return "/data/";
}


function getFileVersion() {
    /* Forces refresh of the file */
    return "71";
}


function getSystemVersion() {
    return "1.0.4";
}


function getInitialSearchSuggestsions() {
    return [
        "tag=artificial intelligence",
        "tag=artificial intelligence bot",
        "tag=search engine",
        "tag=operating system",
        "tag=technology",
        "tag=science",
        "tag=news",
        "tag=music artist",
        "tag=music band",
        "tag==web browser",
        "tag=video games",
        "tag==video game",
        "tag=personal",
        "tag=personal sites source",
        "tag=interesting",
        "tag=interesting page design",
        "tag=interesting page contents",
        "tag=anime",
        "tag=self-host",
        "tag=programming",
        "tag=programming language",
        "tag=open source",
        "tag=wtf",
        "tag=funny",
        "language=pl",
        "link=youtube.com/channel",
        "link=github.com/",
        "link=reddit.com/",
        "link=x.com/",
    ];
}


function getViewStyles() {
    return [
        "standard",
        "gallery",
        "search-engine",
        "content-centric",
        "accordion",
        "links-only",
    ];
}


function getOrderPossibilities() {
    return [
        ['page_rating_votes', "Votes ASC"],
        ['-page_rating_votes', "Votes DESC"],
        ['view_count', "Views ASC"],
        ['-view_count', "Views DESC"],
        ['date_published', "Date published ASC"],
        ['-date_published', "Date published DESC"],
        ['followers_count', "Followers ASC"],
        ['-followers_count', "Followers DESC"],
        ['stars', "Stars ASC"],
        ['-stars', "Stars DESC"],
    ];
}


function notify(text) {
    console.log(text);
}

function debug(text) {
    if (debug_mode) {
    console.log(text);
    }
}
