
let all_entries = null;
let entries_length = 0;
let search_suggestions = [];
let original_title = "";
let common_indicators = null;


function getFileName() {
    let file_name = getQueryParam('file') || getDefaultFileName();
    if (file_name == null) {
	return;
    }

    let adir = getDefaultFileLocation();

    if (file_name.indexOf(".zip") === -1 && file_name.indexOf(".db") === -1)
        file_name = file_name + ".zip";

    if (file_name.indexOf(adir) === -1)
        file_name = adir + file_name

    return file_name;
}


function getPageNumber() {
    return parseInt(getQueryParam("page")) || 1;
}


function setTitle() {
    let page_number = getQueryParam("page");

    const search_input = $("#searchInput").val();
    if (search_input.trim() != "") {
        if (page_number != null) {
           document.title = search_input + " " + page_number;
	}
        else
	{
           document.title = search_input;
	}
    }
    else {
        document.title = original_title;
    }
}


function isWorkerNeeded(fileName) {
    if (fileName.indexOf("db") != -1 || fileName.indexOf("db.zip") != -1) {
        return true;
    }
    return false;
}


function sortAndFilter() {
    console.log("sortAndFilter");

    const search_text = $("#searchInput").val();

    let entries = all_entries.entries;

    entries = sortEntries(entries);

    if (search_text != "") {
       entries = filterEntries(entries, search_text);
    }

    entries_length = entries.length;

    let page_num = getPageNumber();
    let page_size = default_page_size;

    let start_index = (page_num-1) * page_size;
    let end_index = page_num * page_size;

    object_list_data.entries = entries.slice(start_index, end_index);
}




function performSearchJSON() {
    if (!system_initialized) {
        $("#statusLine").html(`<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Reading data...`);
        return;
    }

    let entry_id = getQueryParam("entry_id");

    if (entry_id) {
       setEntryIdAsListData(entry_id);
    }
    else {
       sortAndFilter();

       fillListData();

       $('#pagination').html(getPaginationText());

       onSearchStop();
    }
}


function performSearchDb() {
    if (!worker) {
        $('#statusLine').html("Worker problem");
        return;
    }
    if (!system_initialized) {
        $('#statusLine').html("Cannot make query - database is not ready");
    }

    let query = getQueryText(default_page_size);
    console.log("Sent entries message: " + query);
    worker.postMessage({ type:"entries", query:query });

    // if we want to have precise message
    //console.log("Sent pagination message: " + query);
    //worker.postMessage({ type:"pagination", query:query });
}


function performSearchAPI() {
    let page_num = getPageNumber();
    const userInput = $("#searchInput").val();
    let order_by = getQueryParam("order_by");
    let view = getQueryParam("view");

    getEntriesJson(function(data) {
       object_list_data = data;
       fillListData();
       $('#pagination').html(getPaginationText());
       onSearchStop();
    }, page=page_num, search=userInput, order_by=order_by, view=view);
}


function performSearch() {
    let file_name = getFileName();

    setTitle();

    const userInput = $("#searchInput").val();
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('search', userInput);
    window.history.pushState({}, '', currentUrl);

    onSearchStart();

    if (file_name) {
      if (isWorkerNeeded(file_name)) {
         return performSearchDb();
      }
      else {
         return performSearchJSON();
      }
    }
    else
    {
        return performSearchAPI();
    }
}


function setEntryIdAsListData(entry_id) {
    let entry = getEntry(entry_id);
    setEntryAsListData(entry);
}


function setEntryAsListData(entry) {
    if (entry) {
       let entry_detail_text = getEntryDetailText(entry);
       let data = `<a href="" class="btn btn-primary go-back-button m-1">Go back</a>`;
       data += `<a href="" class="btn btn-primary copy-link m-1">Copy Link</a>`;
       data += entry_detail_text;
       $("#listData").html(data);
       $('#pagination').html("");

       document.title = entry.title;
    }
    else {
       $("#statusLine").html("Invalid entry");
    }
}


async function InitializeForDb() {
  if (!object_list_data) {
    if (!worker) {
       initWorker();
    }
  }
}


async function InitializeForJSON() {
   let file_name = getFileName();
   system_initialized = false;
   let spinner_text_1 = getSpinnerText("Initializing - reading file");
   console.log("Initializing - reading file");
   $("#statusLine").html(spinner_text_1);
   let chunks = await getFilePartsList(file_name);
   if (!chunks || chunks.length == 0)
   {
       $("#statusLine").html("Cannot find files...");
       return false;
   }

   console.log("Requesting file list");
   let fileBlob = await requestFileChunksFromList(chunks);
   if (!fileBlob)
   {
       $("#statusLine").html("Cannot find file contents...");
       return false;
   }
   let spinner_text_2 = getSpinnerText("Loading zip");
   console.log("Loading zip");
   $("#statusLine").html(spinner_text_2);
   const zip = await JSZip.loadAsync(fileBlob);
   let spinner_text_3 = getSpinnerText("Unpacking zip");
   console.log("Unpacking zip");
   $("#statusLine").html(spinner_text_3);
   await unPackFileJSONS(zip, updateListData);
   $("#statusLine").html("");

   console.log("Sorting links");

   all_entries = { ...object_list_data };

   console.log("On system ready");

   let entry_id = getQueryParam("entry_id");
   if (!entry_id) {
      sortAndFilter();
      fillListData();

      $('#pagination').html(getPaginationText());
   }
}


async function initWorker() {
    console.log("Init worker");
    let spinner_text = getSpinnerText("Initializing worker");
    $('#statusLine').html(spinner_text);

    worker = new Worker('scripts/dbworker.js?i=' + getSystemVersion());

    let file_name = getFileName();

    worker.postMessage({ type: "filename", fileName:  file_name});

    worker.onmessage = workerFunction;
    console.log("Init worker done");
    $('#statusLine').html("");
}


function SetFooterStatusLine(custom_error = "") {
   let error_line = custom_error;

   if (common_indicators) {
       if (common_indicators.sources_error && common_indicators.sources_error.status) {
           error_line += add_text(error_line, "Sources");
       }
       if (common_indicators.threads_error && common_indicators.threads_error.status) {
           error_line += add_text(error_line, "Threads");
       }
       if (common_indicators.jobs_error && common_indicators.jobs_error.status) {
           error_line += add_text(error_line, "Jobs");
       }
       if (common_indicators.configuration_error && common_indicators.configuration_error.status) {
           error_line += add_text(error_line, "Configuration");
       }
       if (common_indicators.internet_error && common_indicators.internet_error.status) {
           error_line += add_text(error_line, "Internet");
       }
       if (common_indicators.crawling_server_error && common_indicators.crawling_server_error.status) {
           error_line += add_text(error_line, "Crawling server");
       }
       if (common_indicators.is_reading && common_indicators.is_reading.status) {
           error_line += add_text(error_line, common_indicators.is_reading.message);
       }
   }

   if (error_line == "") {
       $("#footerLine").html("");
       $("#footerLine").hide();
   }
   else {
       $("#footerLine").html(error_line);
       $("#footerLine").show();
   }
}


function getIndicators(callback=null, error_callback=null) {
    let url_address = getStatusAPI();

    getDynamicJson(url_address, function (data) { 
       if (callback) {
         callback(data);
       }
    }, error_callback);
}

function getSystemIndicators() {
   getIndicators(function(data) {
       common_indicators = data.indicators;

       SetFooterStatusLine();
   }, function() {
       SetFooterStatusLine("Connection error");
   });
}


function getBasicPageElements() {
    getSystemIndicators();
}


async function Initialize() {
    let file_name = getFileName();
    original_title = document.title;

    $('#searchInput').prop('disabled', true);

    getBasicPageElements();

    if (getDefaultFileName()) {
      if (isWorkerNeeded(file_name)) {
         initialization_mode = "database";
         await InitializeForDb();
         // onSystemReady is called when message about db being ready is received
      }
      else {
         await InitializeForJSON();
         initialization_mode = "json";
         onSystemReady();
      }
    }
    else {
       initialization_mode = "api";
       onSystemReady();
    }
}


function onSystemReady() {
    system_initialized = true;
    $('#searchInput').prop('disabled', false);
    $('#searchInput').focus();

    let search = getQueryParam("search");
    let entry_id = getQueryParam("entry_id");

    if (entry_id || perform_auto_search) {
       performSearch();
    }
    else {
       $('#statusLine').html("System is ready! You can perform search now");
    }
}


function getEntriesJson(callback=null, page=1, search=null, order_by=null, view=null) {
   let url_location = getEntryAPI();
   // TODO most likely there is some fancy javascript to encode it
   let params = new URLSearchParams({});

   if (search != null) {
       params.append("search", search);
   }
   if (order_by != null) {
       params.append("order_by", order_by);
   }
   if (view != null) {
       params.append("view", view);
   }
   if (page != null) {
       params.append("p", page);
   }

   let url_address = `${url_location}?${params.toString()}`;

   getDynamicJson(url_address, function(data) {
       if (callback) {
          callback(data);
       }
   });
}


function getEntriesVisitJson(entry_id, callback=null, page=1, search=null, order_by=null) {
   let url_location = getEntryVisitAPI();
   let url_address = `${url_location}?id=${entry_id}`;

   getDynamicJson(url_address, function(data) {
       if (callback) {
          callback(data);
       }
   });
}



function resetParams() {
   const currentUrl = new URL(window.location.href);
   currentUrl.searchParams.delete('page')
   currentUrl.searchParams.delete('search')
   currentUrl.searchParams.delete('entry_id')
   // currentUrl.searchParams.delete('order_by')
   window.history.pushState({}, '', currentUrl);
}


function readConfig() {
    const urlParams = new URLSearchParams(window.location.search);

    if (urlParams.has("view_show_icons")) {
        view_show_icons = urlParams.get("view_show_icons");
    }
    if (urlParams.has("view_display_type")) {
        view_display_type = urlParams.get("view_display_type");
    }
    if (urlParams.has("order_by")) {
        sort_function = urlParams.get('order_by');
    }

    if (urlParams.has("default_page_size")) {
        default_page_size = parseInt(urlParams.get('default_page_size'), 10);
    }
}


function updateListData(jsonData) {
    if (!object_list_data) {
        object_list_data = { entries: [] };
    }

    if (!object_list_data.entries) {
        object_list_data.entries = [];
    }

    if (jsonData && Array.isArray(jsonData.entries)) {
        object_list_data.entries.push(...jsonData.entries);
    } else if (jsonData && Array.isArray(jsonData)) {
        object_list_data.entries.push(...jsonData);
    } else {
        console.error("Invalid JSON data: jsonData.entries is either not defined or not an array.");
    }
}


