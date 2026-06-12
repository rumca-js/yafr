

function getSearchSuggestsions() {
   let initial_search_suggestions = getInitialSearchSuggestsions();

   return [...search_suggestions, ...initial_search_suggestions];
}


function getVersionInformation() {
   return "File version:" + getFileVersion() + " System version:" + getSystemVersion();
}


function getSystemInformationHtml() {
   let file_name = getFileName();
   let version = getVersionInformation();

   let text = "";

   text += `<div>File name ${file_name}</div>`;
   text += `<div>${version}</div>`;

   text += `<div>Current sort setting:${sort_function}</div>`;

   return text;
}


function fillEntireListData() {
    let data = object_list_data;

    $('#listData').html("");

    let entries = data.entries;

    if (!entries || entries.length == 0) {
        $('#statusLine').html("No entries found");
        $('#listData').html("");
        $('#pagination').html("");
        return;
    }

    fillListDataInternal(entries);

    $('#statusLine').html("")
}


function fillListDataInternal(entries) {
    var finished_text = getEntriesList(entries);

    $('#listData').html(finished_text);
}


function filterEntries(entries, searchText) {
    let filteredEntries = entries.filter(entry =>
        isEntrySearchHit(entry, searchText)
    );

    return filteredEntries;
}


function fillListData() {
   console.log("fillListData");
   fillEntireListData();
}


function getPaginationText() {
    let page_num = parseInt(getQueryParam("page")) || 1;

    if (initialization_mode == "json") {
        let page_size = default_page_size;
        let countElements = entries_length;

        return GetPaginationNav(page_num, countElements/page_size, countElements);
    }
    else {
        if (object_list_data == null) {
            return "No data";
        }
        if (object_list_data.entries == null) {
            return "No data";
        }
        if (object_list_data.entries.length == 0) {
            return "No data";
        }
        return GetPaginationNavSimple(page_num);
    }
}


function getProjectListText() {
    let files = getFileList();
    
    let html = `
        <div id="projectList">
            <h3>Projects</h3>
    `;
    
    files.forEach(file => {
        //let projectName = file.replace(".zip", "");
        let projectName = file;
        html += `<a class="btn btn-secondary projectButton" href="/${projectName}">${projectName}</a>`;
    });
    
    html += `</div>`;
    
    return html;
}


function getNavBar() {
    if (isMobile()) {
       return getNavBarMobile();
    }
    else {
       return getNavBarDesktop();
    }
}


function getNavBarMobile() {
    let home_text = getNavHomeButton();
    let navbar_search_form = getNavSearchForm();
    let navbar_files_menu = getNavFiles();
    let navbar_view_menu = getNavBarViewMenu();
    let suggestions = getSearchSuggestionContainer();

    let nav_text = `
    <nav id="navbar" class="navbar sticky-top navbar-expand-lg navbar-light bg-light container-fluid">
      <div class="container-fluid">
      <!--div class="d-flex justify-content-end align-items-center w-100"-->
        ${home_text}

        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
      </div>

      <div class="container-fluid">
        ${navbar_search_form}
      </div>

        <div class="collapse navbar-collapse" id="navbarSupportedContent">
            <ul class="navbar-nav mr-auto">
               ${navbar_files_menu}

               ${navbar_view_menu}

               <li class="nav-item">
                 <a id="helpButton" class="nav-link" href="#">More</a>
               </li>
            </ul>
        </div>

      </div>
    </nav>

    ${suggestions}
    `;

    return nav_text;
}


function getNavBarDesktop() {
    let home_text = getNavHomeButton();
    let navbar_search_form = getNavSearchForm();
    let navbar_files_menu = getNavFiles();
    let navbar_view_menu = getNavBarViewMenu();
    let suggestions = getSearchSuggestionContainer();

    let nav_text = `
    <nav id="navbar" class="navbar sticky-top navbar-expand-lg navbar-light bg-light container-fluid">
      <div class="container-fluid">
        ${home_text}

        ${navbar_search_form}

        <!-- Navbar toggler button, aligned to the right -->
        <button class="navbar-toggler ms-auto" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
      </div>

      <div class="collapse navbar-collapse" id="navbarSupportedContent">
          <ul class="navbar-nav mr-auto">
             ${navbar_files_menu}

             ${navbar_view_menu}

             <li class="nav-item">
               <a id="helpButton" class="nav-link" href="#">More</a>
             </li>
          </ul>
      </div>
    </nav>

    ${suggestions}
    `;


    return nav_text;
}


function getNavSearchForm() {
    return `
        <form class="d-flex w-100 ms-3" id="searchContainer">
          <div class="input-group">
            <input id="searchInput" class="form-control me-1 flex-grow-1" type="search" placeholder="Search" autofocus aria-label="Search">
            <button id="dropdownButton" class="btn btn-outline-secondary" type="button">⌄</button>
            <button id="searchButton" class="btn btn-outline-success" type="submit">🔍</button>
          </div>
        </form>
        `;
}


function getNavHomeButton() {
    let home_location = getHomeLocation();
    return `<a id="homeButton" class="d-flex align-items-right px-3 mb-2" href="#">🏠</a>`;
}


function getNavFiles() {
    let project_text = getProjectListTextNav();
    if (project_text == null)
        return "";

    return `
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
              Files
            </a>
            <ul class="dropdown-menu" aria-labelledby="navbarDropdown">
                ${project_text}
            </ul>
          </li>`;
}


function getProjectListTextNav() {
    let files = getFileList();
    if (files.length == 0) {
        return;
    }
    
    let html = ``;
    
    files.forEach(file => {
        //let projectName = file.replace(".zip", "");
        let projectName = file;
        html += `<li><a class="dropdown-item projectButton" href="/${projectName}">${projectName}</a></li>`;
    });
    
    return html;
}


function getSearchSuggestionContainer() {
    const suggestions = getSearchSuggestsions();
    let listItems = suggestions.map(suggestion =>
        `<li class="list-group-item suggestion-item" style="cursor:pointer" data-search="${suggestion}">🔍${suggestion}</li>`
    ).join("");

    let html = `
        <div id="search-suggestions" class="mt-2" style="display:none;">
            <ul class="list-group" id="suggestion-list">
               ${listItems}
            </ul>
        </div>
    `;
    return html;
}


function getOrderButtons(prefix = "") {

    let text = "";
    for (const style of getOrderPossibilities())
    {
        let style_real = style[0];
        let style_name = style[1];
        let id = prefix + "order" + style_real;
        text += `
                <li>
                    <div class="dropdown-item form-check">
                        <input class="form-check-input me-2" type="radio" name="order_by" id="${id}" value="${style_real}">
                        <label class="form-check-label" for="${id}">Order by ${style_name}</label>
                    </div>
                </li>
          `;
    }

    return text;
}


function getViewButtons(prefix = "") {

    let text = "";
    for (const style of getViewStyles())
    {
        let id = prefix + "view-" + style;
        text += `
                <li>
                    <div class="dropdown-item form-check">
                        <input class="form-check-input me-2" type="radio" name="viewMode" id="${id}" value="${style}">
                        <label class="form-check-label" for="${id}">${style}</label>
                    </div>
                </li>
                `;
    }

    return text;
}


function getThemeButtons(prefix = "") {
	return `
                <li>
                    <div class="dropdown-item form-check">
                        <input class="form-check-input me-2" type="radio" name="theme" id="${prefix}displayLight" value="style-light">
                        <label class="form-check-label" for="${prefix}displayLight">Light</label>
                    </div>
                </li>
                <li>
                    <div class="dropdown-item form-check">
                        <input class="form-check-input me-2" type="radio" name="theme" id="${prefix}displayDark" value="style-dark">
                        <label class="form-check-label" for="${prefix}displayDark">Dark</label>
                    </div>
                </li>`;
}


function getCheckBoxes(prefix = "")  {
	return `
                <li>
                    <div class="dropdown-item form-check">
                        <input class="form-check-input me-2" type="checkbox" name="showIcons" id="${prefix}showIcons">
                        <label class="form-check-label" for="${prefix}showIcons">Show icons</label>
                    </div>
                </li>

                <li><hr class="dropdown-divider"></li>

                <li>
                    <div class="dropdown-item form-check">
                        <input class="form-check-input me-2" type="checkbox" name="modal-preview" id="${prefix}modal-preview">
                        <label class="form-check-label" for="${prefix}modal-preview" title="Click on entry opens preview">Modal preview</label>
                    </div>
                </li>

                <li><hr class="dropdown-divider"></li>

                <li>
                    <div class="dropdown-item form-check">
                        <input class="form-check-input me-2" type="checkbox" name="directLinks" id="${prefix}directLinks">
                        <label class="form-check-label" for="${prefix}directLinks" title="Links lead directly to URL">Direct links</label>
                    </div>
                </li>

                <li><hr class="dropdown-divider"></li>

                <li>
                    <div class="dropdown-item form-check">
                        <input class="form-check-input me-2" type="checkbox" name="highlight-bookmarks" id="${prefix}highlight-bookmarks">
                        <label class="form-check-label" for="${prefix}highlight-bookmarks" title="Highlights bookmarks">Highlight bookmark</label>
                    </div>
                </li>
		`;
}


function getNavBarViewMenu() {

    return `
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" id="navbarViewDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
              View
            </a>
            <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="navbarViewDropdown" id="navBarViewDiv">
		<div></div>
            </ul>
          </li>
          `;
}


function getConfigurationElements() {
    let view_buttons = getViewButtons("help-");
    let order_buttons = getOrderButtons("help-");
    let theme_buttons = getThemeButtons("help-");
    let check_boxes = getCheckBoxes("help-");

    return `
    <div class="card mb-3 shadow-sm">
        <div class="card-body">
            <h6 class="card-subtitle mb-3 text-muted">View Settings</h6>
            <div class="d-flex flex-wrap gap-2 mb-4">
                <div class="dropdown">
                    <button class="btn btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        Views
                    </button>
                    <ul class="dropdown-menu">
                        ${view_buttons}
                    </ul>
                </div>
                <div class="dropdown">
                    <button class="btn btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        Order by
                    </button>
                    <ul class="dropdown-menu">
                        ${order_buttons}
                    </ul>
                </div>

                <div class="dropdown">
                    <button class="btn btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        Theme
                    </button>
                    <ul class="dropdown-menu">
		        ${theme_buttons}
                    </ul>
                </div>

                <div class="dropdown">
                    <button class="btn btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        Checks
                    </button>
                    <ul class="dropdown-menu">
		        ${check_boxes}
                    </ul>
                </div>
            </div>
            
            <h6 class="card-subtitle mb-3 text-muted">Quick Links</h6>
            <div class="d-flex flex-wrap gap-2">
                <a class="btn btn-primary" href="/check-later-list">Check later</a>
                <a class="btn btn-primary" href="/sources">Sources</a>
                <a class="btn btn-primary" href="/status">Status</a>
                <a class="btn btn-primary" href="/admin">Admin</a>
            </div>
        </div>
    </div>
    `;
}


function hideSearchSuggestions() {
   let search_suggestions = document.getElementById("search-suggestions");
   search_suggestions.style.display = "none";
   $("#dropdownButton").html("⌄");
}


function showSearchSuggestions() {
   let search_suggestions = document.getElementById("search-suggestions");
   search_suggestions.style.display = "block";
   $("#dropdownButton").html("^");
}


function setLightMode() {
    view_display_style = "style-light";

    // const linkElement = document.querySelector('link[rel="stylesheet"][href*="styles.css_style-"]');
    // if (linkElement) {
    //     // TODO replace rsshistory with something else
    //     //linkElement.href = "/django/rsshistory/css/styles.css_style-light.css";
    // }

    const htmlElement = document.documentElement;
    htmlElement.setAttribute("data-bs-theme", "light");

    const navbar = document.getElementById('navbar');
    navbar.classList.remove('navbar-dark', 'bg-dark');
    navbar.classList.add('navbar-light', 'bg-light');
}


function setDarkMode() {
    view_display_style = "style-dark";

    // const linkElement = document.querySelector('link[rel="stylesheet"][href*="styles.css_style-"]');
    // if (linkElement) {
    //     //linkElement.href = "/django/rsshistory/css/styles.css_style-dark.css";
    // }

    const htmlElement = document.documentElement;
    htmlElement.setAttribute("data-bs-theme", "dark");

    const navbar = document.getElementById('navbar');
    navbar.classList.remove('navbar-light', 'bg-light');
    navbar.classList.add('navbar-dark', 'bg-dark');
}


function updateWidgets() {
    $('input[name="viewMode"][value="' + view_display_type + '"]').prop('checked', true);
    $('input[name="theme"][value="' + view_display_style + '"]').prop('checked', true);
    $('input[name="order_by"][value="' + sort_function + '"]').prop('checked', true);

    $('input[name="showIcons"').prop('checked', view_show_icons);
    $('input[name="directLinks"').prop('checked', entries_direct_links);
    $('input[name="highlight-bookmarks"').prop('checked', highlight_bookmarks);
    $('input[name="modal-preview"').prop('checked', click_behavior_modal_window);
}


// properties
function getCollapsedPropertyItem(name, data) {
    let escaped_name = name.replace(/\s+/g, "-");

    htmlOutput = `
    <a class="btn btn-secondary" data-bs-toggle="collapse" href="#collapse${escaped_name}" role="button" aria-expanded="false" aria-controls="collapse${escaped_name}">
        ${name} Details
    </a>
    <div class="collapse" id="collapse${escaped_name}"><pre>${data}</pre></div>`;

    return htmlOutput;
}


function displayProperty(propertyEntry) {
   let htmlOutput = "";
   for (const [key, value] of Object.entries(propertyEntry)) {
       if (key != "description")
       {
           htmlOutput += `
           <div>
               <strong>${key}:</strong> ${value ?? "N/A"}
           </div>
       `;
       }
   }

   return htmlOutput;
}


function isPropertySupported(property) {
    if (property.name == "Text")
       return false;
    if (property.name == "Binary")
       return false;

    return true;
}


function GetAllPropertiesTextProperty(property) {
    let htmlOutput = "";

    let property_name = property.name;

    if (!isPropertySupported(property)) {
        return htmlOutput;
    }

    htmlOutput += `<h1>${property_name}</h1>`;

    if (property.name == "Text") {
    }
    else if (property.name == "Binary") {
    }
    else if (property.name == "PropertiesHash") {
    }
    else if (property.name == "Streams") {
        for (const [key, stream_data] of Object.entries(property.data)) {
            let escapedContents = escapeHtml(stream_data);
            htmlOutput += getCollapsedPropertyItem(key, escapedContents);
        }
    }
    else if (property.name == "Entries") {
        htmlOutput += getEntriesList(property.data);
    }
    else {
        for (const [key, value] of Object.entries(property.data)) {
            if (key == "contents" || key == "text" || key == "binary") {
                continue
            }

            if (key == "settings") {
               let props = displayProperty(value);
               htmlOutput += `
               <div>
                 <strong>${key}:</strong> <div class="cotainer">${props}</div>
               </div>
               `;
            }
            else {
               htmlOutput += `
               <div>
                   <strong>${key}:</strong> ${value ?? "N/A"}
               </div>
                `;
            }
        }
    }

    return htmlOutput;
}


function GetPropertyWithName(page_properties, name) {
    if (page_properties && page_properties.length > 0) {
        return page_properties.find(property => property.name === name);
    }
    return null;
}


function GetAllPropertiesText(page_properties) {
    let htmlOutput = "";

    let properties_property = GetPropertyWithName(page_properties, "Properties");
    if (properties_property) 
       htmlOutput += GetAllPropertiesTextProperty(properties_property);

    let entries_property = GetPropertyWithName(page_properties, "Entries")
    if (entries_property) 
       htmlOutput += GetAllPropertiesTextProperty(entries_property);

    let request_property = GetPropertyWithName(page_properties, "Request")
    if (request_property) 
       htmlOutput += GetAllPropertiesTextProperty(request_property);

    let response_property = GetPropertyWithName(page_properties, "Response")
    if (response_property) 
       htmlOutput += GetAllPropertiesTextProperty(response_property);

    let headers_property = GetPropertyWithName(page_properties, "Headers")
    if (headers_property) 
       htmlOutput += GetAllPropertiesTextProperty(headers_property);

    return htmlOutput;
}
