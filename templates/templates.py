PAGINATION="""
<div class="pagination">
    <li class="page-item">
       <a href="{{ entries_page }}?p={{ prev_page }}" class="btnNavigation page-link">&lt;</a>
    </li>
    <li class="page-item">
       <a href="{{ entries_page }}?p={{ next_page }}" class="btnNavigation page-link">&gt;</a>
    </li>
</div>
"""

def get_view(body, title=""):
    text = """
<!doctype html>
<html>
<head>
    <title>{title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    <link  href="styles/viewerzip.css?i=90" rel="stylesheet" crossorigin="anonymous">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
    </style>

</head>
<body>
   {body}
</body>
</html>
"""
    text = text.replace("{title}", title)
    return text.replace("{body}", body)


INDEX_TEMPLATE = """
<h1>{{title}} v{{version}}</h1>
<ul>
  <li><a href="/search">Search</a>
  <li><a href="/check-later-list">Check later</a>
  <li><a href="/sources">Sources</a>
  <li><a href="/status">Status</a>
  <li><a href="/admin">Admin</a>
</ul>
"""


ADMIN_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>
<h1>Admin</h1>
<ul>
  <li><a href="/logs">Logs</a>
  <li><a href="/jobs">Jobs</a>
  <li><a href="/add-links">Add links</a>
  <li><a href="/add-sources">Add sources</a>
  <li><a href="/entry-rules">Entry rules</a>
  <li><a href="/block-rules">Block rules</a>
  <li><a href="/views">Search views</a>
  <li><a href="/configuration">Configuration</a>
</ul>

<ul>
  <li><a href="/link-test">Test link</a>
  <li><a href="/download-list">Download list</a>
</ul>

<ul>
  <li><a href="/remove-all-sources">Remove all sources</a>
  <li><a href="/remove-entries-no-source">Remove entries without source</a>
  <li><a href="/remove-all-entries">Remove all entries</a>
  <li><a href="/remove-all-social-data">Remove all social data</a>
  <li><a href="/remove-all-tags">Remove all tags</a>
  <li><a href="/remove-all-votes">Remove all votes</a>
  <li><a href="/remove-all-entry-rules">Remove all entry rules</a>
  <li><a href="/remove-all-block-entries">Remove all block entries</a>
  <li><a href="/remove-all-views">Remove all views</a>
</ul>
"""


TEST_LINK_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<h1>Test link</h1>

<form method="POST">
  <label for="link">Link</label></br>
  <input type="link" id="link" name="link" value="{{search_value}}" size="100" autofocus/>
  <button type="submit">Search</button>
</form>
"""


OK_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>YouTube Feed Entries</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h2 { margin-top: 30px; }
        ul { list-style-type: none; padding-left: 0; }
        li { margin-bottom: 10px; }
        a { text-decoration: none; color: #1a0dab; }
    </style>
</head>
<body>
    <div class="nav-buttons">
        <button class="btn btn-primary" onclick="history.back()">Go back</button>
        <a class="btn btn-primary" href="/">Home</a>
    </div>
    OK
</body>
</html>
"""


NOK_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>YouTube Feed Entries</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h2 { margin-top: 30px; }
        ul { list-style-type: none; padding-left: 0; }
        li { margin-bottom: 10px; }
        a { text-decoration: none; color: #1a0dab; }
    </style>
</head>
<body>
    <div class="nav-buttons">
        <button class="btn btn-primary" onclick="history.back()">Go back</button>
        <a class="btn btn-primary" href="/">Home</a>
    </div>
    NOK
</body>
</html>
"""

STR_TEMPLATE = """
    <div class="nav-buttons">
        <button class="btn btn-primary" onclick="history.back()">Go back</button>
        <a class="btn btn-primary" href="/">Home</a>
    </div>
    {template_string}
"""


ENTRY_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<h1>YouTube Feed Entries</h1>

<div class="title">
    {% if entry.link %}
        <a href="{{ entry.link }}" target="_blank" rel="noopener">
            {{ entry.title or "Untitled entry" }}
        </a>
    {% else %}
        {{ entry.title or "Untitled entry" }}
    {% endif %}
</div>
"""


CHECK_LATER_LIST_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
    <a class="btn btn-primary" href="/check-later-clear">Clear</a>
</div>

<h1>Check later list</h1>

<ul>
{% for entry in entries %}
    <li class="entry">
        <a href="/search?search=id={{ entry.id }}">
            {{ entry.title or "Untitled entry" }}
        </a>

        <a href="/entry-not-check-later?id={{ entry.id }}">
            Do not check later
        </a>
    </li>
{% endfor %}
</ul>
"""


ENTRIES_LIST_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<h1>Entries</h1>

<ul>
{% for entry in entries %}
    <li class="entry">
    <img src="{{entry.thumbnail}}"/>
        <div class="title">
            {% if entry.link %}
                <a href="{{ entry.link }}" target="_blank" rel="noopener">
                    {{ entry.title or "Untitled entry" }}
                </a>
            {% else %}
                {{ entry.title or "Untitled entry" }}
            {% endif %}
        </div>

        <div class="meta">
            {% if entry.author %} By {{ entry.author }}{% endif %}
            {% if entry.album %} Album: {{ entry.album }}{% endif %}
            {% if entry.language %} Language: {{ entry.language }}{% endif %}
            {% if entry.status_code %} HTTP {{ entry.status_code }}{% endif %}
        </div>

        {% if entry.description %}
            <div class="description">
                {{ entry.description }}
            </div>
        {% endif %}

        <div class="stats">
            {% if entry.page_rating is not none %}
                Rating: {{ entry.page_rating }}
            {% endif %}
            {% if entry.page_rating_votes %}
                Votes: {{ entry.page_rating_votes }}
            {% endif %}
            {% if entry.page_rating_visits %}
                Visits: {{ entry.page_rating_visits }}
            {% endif %}
            {% if entry.age %}
                Age: {{ entry.age }}
            {% endif %}
        </div>

        <div class="flags">
            {% if entry.bookmarked %}
                <span class="bookmarked">★ Bookmarked</span>
            {% endif %}
            {% if entry.permanent %}
                <span class="permanent">Permanent</span>
            {% endif %}
        </div>

        <div class="dates">
            {% if entry.date_published %}
                Published: {{ entry.date_published }}
            {% endif %}
            {% if entry.date_created %}
                Created: {{ entry.date_created }}
            {% endif %}
            {% if entry.date_update_last %}
                Updated: {{ entry.date_update_last }}
            {% endif %}
            {% if entry.date_last_modified %}
                Modified: {{ entry.date_last_modified }}
            {% endif %}
            {% if entry.date_dead_since %}
                Dead since: {{ entry.date_dead_since }}
            {% endif %}
        </div>
    </li>
{% endfor %}
</ul>
"""


SOURCES_LIST_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
    <a class="btn btn-primary" href="/sources-fetch-period">Set Fetch Period</a>
    <a class="btn btn-primary" href="/add-sources">Add sources</a>
</div>

<h1>Sources {{sources_length}}</h1>

<form method="GET">
  <label for="search">Search</label></br>
  <input type="search" id="search" name="search" value="{{search_value}}" autofocus/>
  <button type="submit">Search</button>
</form>

<div class="display-grid">
    {% for source in sources %}
        <div class="display-card">
            <a href="/source/{{ source.id }}">
                <img
                    src="{{ source.favicon }}"
                    alt="Source thumbnail"
                    class="display-thumb"
                    onerror="this.style.display='none'"
                />
            </a>

            <a href="/source/{{ source.id }}">
              <div class="source-title">
                 {{ source.title or "Untitled source" }}
              </div>
            </a>
            <div class="source-title">
               {{ source.url }}
            </div>
            <div class="source-title">
               <a href="/rss/{{source.id}}">RSS</a>
            </div>
        </div>
    {% endfor %}
</div>

{{pagination_text}}
"""


SOURCE_EDIT_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<form method="POST">
    <div><label for="title">Title</label></div>
    <div><input type="search" id="title" name="title" value="{{source.title}}"/></div>
    <div><label for="url">URL</label></div>
    <div><input type="search" id="url" name="url" value="{{source.url}}"/></div>
    <div><label for="language">Language</label></div>
    <div><input type="search" id="language" name="language" value="{{source.language}}"/></div>
   <button type="submit">Save</button>
</form>
"""


SOURCE_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
    <a class="btn btn-primary" href="/source-fetch?id={{source_item.id}}">Fetch</a>
    <a class="btn btn-primary" href="/search?search=source_id=={{source_item.id}}">Search</a>
    <a class="btn btn-primary" href="/remove-source?id={{source_item.id}}">Remove</a>
</div>

<h1>{{source_item.title}}</h1>

<div>ID:{{source_item.id}}</div>
<div>Url:<a href="{{source_item.url}}">{{source_item.url}}</a></div>
<div>Enabled:{{source_item.enabled}}</div>
<div>Type:{{source_item.source_type}}</div>
<div>Thumbnail:<a href="{{source_item.favicon}}">{{source_item.favicon}}</a></div>

<p>
<div>Date fetched:{{source_op_data.date_fetched}}</div>
<div>Page hash:{{page_hash}}</div>
<div>Body hash:{{body_hash}}</div>
<div>Consecutive errors:{{source_op_data.consecutive_errors}}</div>
</p>

<form method="POST">
    <div><label for="fetch_period">Fetch period</label></div>
    <div><input type="search" id="fetch_period" name="fetch_period" value="{{source_item.fetch_period}}"/></div>
    <div><label for="xpath">Link acceptance 're' expression</label></div>
    <div><input type="search" id="xpath" name="xpath" value="{{source_item.xpath}}"/></div>
    <div><label for="language">Language</label></div>
    <div><input type="search" id="language" name="language" value="{{source_item.language}}"/></div>
    <div><label for="auto_tag">Auto tag</label></div>
    <div><input type="search" id="auto_tag" name="auto_tag" value="{{source_item.auto_tag}}"/></div>
    <button type="submit">Save</button>
</form>
"""


ADD_LINKS_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<h1>Add links</h1>

<form method="POST">
    <p>One source URL per line:</p>
    <textarea name="sources" autofocus>{{raw_data}}</textarea>
    <br>
    <button type="submit">Add</button>
</form>
"""

ADD_SOURCES_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<h1>Add Sources</h1>

<form method="POST">
    <p>One source URL per line:</p>
    <textarea name="sources" autofocus>{{raw_data}}</textarea>
    <br>
    <button type="submit">Add</button>
</form>

<p>
You can find RSS sources at:
  <ul>
   <li><a href="https://rumca-js.github.io/feeds">Rumca-js feeds</a></li>
   <li><a href="https://github.com/plenaryapp/awesome-rss-feeds">Awesome RSS feeds</a></li>
  </ul>
</p>
"""

ENTRY_EDIT_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<form method="POST">
    <div><label for="title">Title</label></div>
    <div><input type="search" id="title" name="title" value="{{entry.title}}"/></div>
    <div><label for="link">Link</label></div>
    <div><input type="search" id="link" name="link" value="{{entry.link}}"/></div>
    <div><label for="description">Description</label></div>
    <div><textarea type="search" id="description" name="description">{{entry.description}}</textarea></div>
    <div><label for="language">Language</label></div>
    <div><input type="search" id="language" name="language" value="{{properties.language}}"/></div>
    <div><label for="date_published">Date published</label></div>
    <div><input type="search" id="date_published" name="date_published" value="{{entry.date_published}}"/></div>
    <div><label for="age">Age</label></div>
    <div><input type="search" id="age" name="age" value="{{properties.age}}"/></div>
   <button type="submit">Save</button>
</form>
"""


ENTRY_VOTE_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<form method="POST">
   <div><label for="entry-vote">Vote:</label></div>
   <div>
      <input type="search" id="entry-vote" name="entry-vote" value="{{current_vote}}" autofocus/>
   </div>
   <button type="submit">Save</button>
</form>
"""


SOURCES_FETCH_TIME = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<form method="POST">
   <div><label for="fetch-period">Fetch time:</label></div>
   <div>
      <input type="fetch-period" id="fetch-period" name="fetch-period" autofocus/>
   </div>
   <button type="submit">Save</button>
</form>
"""


ENTRY_TAG_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<h1>{{entry.title}}</h1>

<form method="POST">
    <div><label for="entry-tag">Tag:</label></div>
    <div>
       <input type="search" id="entry-tag" name="entry-tag" value="{{current_tags}}" autofocus/>
    </div>
   <button type="submit">Save</button>
</form>
"""


DEFINE_ENTRY_RULES_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<h1>Define block URLs</h1>
Will block sources, and entries.

<form method="POST">
    <p>The URLs/feeds below will be blocked. One source URL per line:</p>
    <textarea name="sources" autofocus>{{raw_data}}</textarea>
    <br>
    <button type="submit">Save</button>
</form>
"""


DEFINE_BLOCK_ENTRIES_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<h1>Define block URLs</h1>

<form method="POST">
    <p>The URLs/feeds below will be blocked. One source URL per line:</p>
    <textarea name="sources" autofocus>{{raw_data}}</textarea>
    <br>
    <button type="submit">Save</button>
</form>
"""


ADD_BLOCK_ENTRIES_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<h1>Add block URLs</h1>

<form method="POST">
    <p>The URLs/feeds below will be blocked. One source URL per line:</p>
    <textarea name="sources" autofocus>{{raw_data}}</textarea>
    <br>
    <button type="submit">Save</button>
</form>
"""


BLOCK_RULES_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<h1>Block rules</h1>

<ul>
  <li><a href="/define-block-rules">Define block rules</a>
  <li><a href="/block-url">Block Url</a>
</ul>
"""


ENTRY_RULES_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
    <a class="btn btn-primary" href="/entry-rule-add">Add rule</a>
</div>

<h1>Entry rules</h1>

{% for rule in rules %}
   <div><a href="/entry-rule?id={{rule.id}}">{{rule.id}} Name:{{rule.rule_name}} Enabled:{{rule.enabled}}</a></div>
{% endfor %}
"""


ENTRY_RULE_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
    <a class="btn btn-primary" href="/entry-rule-remove?id={{rule.id}}">Remove</a>
</div>

<h1>Entry rule {{rule.rule_name}}</h1>

<div> ID:{{rule.id}} </div>
<div> Enabled:{{rule.enabled}} </div>
<div> Priority:{{rule.priority}} </div>

<div> Trigger rule url:{{rule.trigger_rule_url}} </div>

<div> Block:{{rule.block}} </div>
<div> Trust:{{rule.trust}} </div>
<div> Auto tag:{{rule.auto_tag}} </div>
<div> Apply age:{{rule.apply_age_limit}} </div>
<div> Browser id:{{rule.browser_id}} </div>

<div> Trigger text:{{rule.trigger_text}} </div>
<div> Trigger text hits:{{rule.trigger_text_hits}} </div>
<div> Trigger text fields:{{rule.trigger_text_fields}} </div>
"""


ENTRY_RULE_ADD_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
    <a class="btn btn-primary" href="/entry-rule-remove?id={{rule.id}}">Remove</a>
</div>

<form method="POST">
    <div><label for="rule_name">Rule Name</label></div>
    <div><input type="search" id="rule_name" name="rule_name" value="{{rule.rule_name}}"/></div>
    <div><label for="enabled">Enabled</label></div>
    <div><input type="search" id="enabled" name="enabled" value="{{rule.enabled}}"/></div>
    <div><label for="block">Block</label></div>
    <div><input type="search" id="block" name="block" value="{{rule.block}}"/></div>
    <div><label for="trust">Trust</label></div>
    <div><input type="search" id="trust" name="trust" value="{{rule.trust}}"/></div>
   <button type="submit">Save</button>
</form>
"""

VIEWS_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
    <a class="btn btn-primary" href="/view-add">Add view</a>
</div>

<h1>Search Views</h1>

{% for view in views %}
   <div><a href="/view?id={{view.id}}">{{view.id}} Name:{{view.name}} Default:{{view.default}}</a></div>
{% endfor %}
"""


VIEW_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
    <a class="btn btn-primary" href="/view-edit?id={{view.id}}">Edit</a>
    <a class="btn btn-primary" href="/view-remove?id={{view.id}}">Remove</a>
</div>

<h1>View {{view.name}}</h1>

<div> ID:{{view.id}} </div>
<div> Priority:{{view.priority}} </div>
<div> Default:{{view.default}} </div>
<div> Filter statement:{{view.filter_statement}} </div>
<div> Order by:{{view.order_by}} </div>
"""


VIEW_ADD_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
    <a class="btn btn-primary" href="/view-remove?id={{view.id}}">Remove</a>
</div>

<form method="POST">
    <div><label for="name">Name</label></div>
    <div><input type="search" id="name" name="name" value="{{view.name}}"/></div>
    <div><label for="name">Priority</label></div>
    <div><input type="search" id="priority" name="priority" value="{{view.priority}}"/></div>
    <div><label for="name">Default</label></div>
    <div><input type="search" id="default" name="default" value="{{view.default}}"/></div>
    <div><label for="name">Filter statement</label></div>
    <div><input type="search" id="filter_statement" name="filter_statement" value="{{view.filter_statement}}"/></div>
    <div><label for="name">Order by</label></div>
    <div><input type="search" id="order_by" name="order_by" value="{{view.order_by}}"/></div>
   <button type="submit">Save</button>
</form>
"""


LOGS_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
    <a class="btn btn-primary" href="/remove-all-logs">Clear</a>
</div>

<h1>Logs {{sources_length}}</h1>

<div>
    {% for log in logs %}
        <div>
             ID:{{log.id}}, 
             [{{log.date}}]
             Level:{{log.level}}: {{log.info_text}},
        </div>
        <div>
             {{log.detail_text}}
        </div>
    {% endfor %}
</div>

{{pagination_text}}
"""


ADD_JOB_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
    <a class="btn btn-primary" href="/remove-all-jobs">Clear</a>
</div>

<h1>Add job</h1>

<form method="POST">
    <div><label for="job_name">Job Name</label></div>
    <div><input type="search" id="job_name" name="job_name" value=""/></div>
    <div><label for="subject">Subject</label></div>
    <div><input type="search" id="subject" name="subject" value=""/></div>
    <div><label for="args">Args</label></div>
    <div><input type="search" id="args" name="args" value=""/></div>
   <button type="submit">Save</button>
</form>
"""


JOBS_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
    <a class="btn btn-primary" href="/add-job">Add job</a>
    <a class="btn btn-primary" href="/remove-all-jobs">Remove All</a>
</div>

<h1>Jobs {{len_jobs}}</h1>

<div>
    {% for job in jobs %}
        <div>
             {% if not job.enabled %}
                [DISABLED]
             {% endif %}
             ID:{{job.id}}, 
             [{{job.date_created}}]
             {{job.job}}: {{job.subject}},
             {% if not job.enabled %}
             <a class="btn btn-secondary btn-sm mx-1" href="/enable-job?id={{job.id}}">&lt;</a>
             {% endif %}
             {% if job.enabled %}
             <a class="btn btn-secondary btn-sm mx-1" href="/disable-job?id={{job.id}}">||</a>
             {% endif %}
             <a class="btn btn-secondary btn-sm mx-1" href="/remove-job?id={{job.id}}">X</a>
        </div>
    {% endfor %}
</div>

{{pagination_text}}
"""


STATS_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<h1>System</h1>
{% for stat_name, stat_counter in program_info.items() %}
    <div>{{stat_name}} {{stat_counter}}</div>
{% endfor %}

<h1>Parameters</h1>
{% for stat_name, stat_counter in stats.items() %}
    <div>{{stat_name}} {{stat_counter}}</div>
{% endfor %}

"""


CONFIGURATION_TEMPLATE = """
<div class="nav-buttons">
    <button class="btn btn-primary" onclick="history.back()">Go back</button>
    <a class="btn btn-primary" href="/">Home</a>
</div>

<form method="POST">
{% for config_setting, config_value in configuration.items() %}
    {% if config_setting == "instance_description" %}
    <div><label for="{{config_setting}}">{{config_setting}}</label></div>
    <div><textarea type="search" id="{{config_setting}}" name="{{config_setting}}" size="30">{{config_value}}</textarea></div>
    {% else %}
    <div><label for="{{config_setting}}">{{config_setting}}</label></div>
    <div><input type="search" id="{{config_setting}}" name="{{config_setting}}" value="{{config_value}}" size="30"/></div>
    {% endif %}
{% endfor %}
   <button type="submit">Search</button>
</form>
"""

INITIALIZATION_WIZARD_TEMPLATE = """
<div class="nav-buttons">
    <a class="btn btn-primary" href="/">Home</a>
</div>

<h1>Initialization Wizard</h1>

<form method="POST">
    <div class="mb-3">
        <label for="initialization_type" class="form-label">Initialization Type</label>
        <select class="form-select" id="initialization_type" name="initialization_type">
            <option value="search_engine">Search Engine</option>
            <option value="rss_reader">RSS Reader</option>
        </select>
    </div>
    
    <div class="mb-3">
        <label for="display_type" class="form-label">Display Type</label>
        <select class="form-select" id="display_type" name="display_type">
            <option value="gallery">Gallery</option>
            <option value="accordion">Accordion</option>
        </select>
    </div>
    
    <button type="submit" class="btn btn-success">Initialize</button>
</form>
"""


PROJECT_TEMPLATE = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <title>{{title}}</title>
      
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
        <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/jszip/dist/jszip.min.js"></script>
        <script src="https://unpkg.com/sql.js@1.6.0/dist/sql-wasm.js"></script>

        <link  href="styles/viewerzip.css?i=90" rel="stylesheet" crossorigin="anonymous">
        <script  src="scripts/config_python.js?i=86"></script>
        <script  src="scripts/library.js?i=86"></script>
        <script  src="scripts/webtoolkit.js?i=86"></script>
        <script  src="scripts/entries_library.js?i=86"></script>
        <script src="scripts/events.js?i=86"></script>
        <script src="scripts/ui.js?i=86"></script>
        <script src="scripts/project.js?i=86"></script>
        <script src="scripts/search.js?i=86"></script>
        <script>
         function reset() {
           {% for setting_key, setting_value in default_values.items() %}
             {{setting_key}} = "{{setting_value}}";
           {% endfor %}
         }
         reset();
        </script>
    </head>
<body style="padding-bottom: 6em;">

<div id="projectNavbar">
</div>

<div class="container">

  <div id="statusLine">
  </div>

  <div id="helpPlace" style="display: none;">
      <div id="configurationElements"></div>

      <div id="version">
      </div>
  </div>

  <span id="progressBarElement">
  </span>
  
  <span id="listData">
  </span>

  <div id="pagination">
  </div>
</div>


<!--
Unfortunately, no one can be told what the Matrix is. You have to see it for yourself.
-->


<footer id="footer" class="text-center text-lg-start bg-body-tertiary text-muted fixed-bottom">
  <div id="footerLine" class="text-center p-1" style="background-color: rgba(0, 0, 0, 0);">
  </div>

  <div class="text-center p-1" style="background-color: rgba(0, 0, 0, 0);">
      <span style="white-space: nowrap;">
      <a href="https://github.com/rumca-js/yafr/issues">Yafr server</a>.
      </span>
  </div>
</footer>

    </body>
</html>
"""

# TODO replace?
PROJECT_TEMPLATE_MAIN = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <title>{{title}}</title>
      
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
        <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/jszip/dist/jszip.min.js"></script>
        <script src="https://unpkg.com/sql.js@1.6.0/dist/sql-wasm.js"></script>

        <link  href="styles/viewerzip.css?i=90" rel="stylesheet" crossorigin="anonymous">
        <script  src="scripts/config_python.js?i=86"></script>
        <script  src="scripts/library.js?i=86"></script>
        <script  src="scripts/webtoolkit.js?i=86"></script>
        <script  src="scripts/entries_library.js?i=86"></script>
        <script src="scripts/ui.js?i=86"></script>
        <script src="scripts/project.js?i=86"></script>
        <script src="scripts/search.js?i=86"></script>
        <script>
           click_behavior_modal_window = false;
           {{script}}
        </script>
    </head>
<body style="padding-bottom: 6em;">

<div id="projectNavbar">
</div>

<div class="container">

  <div id="statusLine">
  </div>

  <div id="helpPlace" style="display: none;">
      <a class="btn btn-primary" href="/check-later-list">Check later</a>
      <a class="btn btn-primary" href="/sources">Sources</a>
      <a class="btn btn-primary" href="/status">Status</a>
      <a class="btn btn-primary" href="/admin">Admin</a>

      <div id="version">
      </div>
  </div>

  <span id="progressBarElement">
  </span>
  
  <span id="listData">
  </span>

  <div id="pagination">
  </div>
</div>


<!--
Unfortunately, no one can be told what the Matrix is. You have to see it for yourself.
-->


<footer id="footer" class="text-center text-lg-start bg-body-tertiary text-muted fixed-bottom">
  <div id="footerLine" class="text-center p-1" style="background-color: rgba(0, 0, 0, 0);">
  </div>

  <div class="text-center p-1" style="background-color: rgba(0, 0, 0, 0);">
      <span style="white-space: nowrap;">
      <a href="https://github.com/rumca-js/yafr/issues">Yafr server</a>.
      </span>
  </div>
</footer>

    </body>
</html>
"""
