"""
Simple RSS reader
"""
import os
import sys
import threading
import argparse
import shutil
from pathlib import Path
from urllib.parse import unquote
from sqlalchemy import select, or_
from collections import OrderedDict
from flask import (
   Flask,
   render_template_string,
   jsonify,
   request,
   send_from_directory,
   url_for,
   redirect,
   Response,
)

from linkarchivetools.model import (
   DbConnection,
   BackgroundJob,
   BlockEntry,
   Entries,
   CheckLater,
   EntryRules,
   SocialData,
   Sources,
   AppLogging,
   SearchView,
   EntryVotes,
   EntryTags,
   ConfigurationEntry,
   entry_to_json,
   source_to_json,
   source_and_entries_to_rss,
)
from linkarchivetools.utils.reflected import ReflectedTable

from src.urlhandler import UrlHandler
from templates.templates import *
from src.taskrunner import TaskRunner
from src.controller import Controller
from src.system import System



def get_project_version(pyproject_text):
    for line in pyproject_text.split("\n"):
        wh = line.find("version")
        if wh >= 0:
            sp = line.split("=")
            trimmed = sp[1].strip()
            return trimmed[1:-1]
    return "0.0.0"

def get_project_name(pyproject_text):
    for line in pyproject_text.split("\n"):
        wh = line.find("name")
        if wh >= 0:
            sp = line.split("=")
            trimmed = sp[1].strip()
            return trimmed[1:-1]


path = Path("pyproject.toml")
pyproject_text = path.read_text()
__version__ = get_project_version(pyproject_text)
__project_name__ = get_project_name(pyproject_text)


page_size = 100

app = Flask(__name__)
app.config["DB_FILE"] = Path("data") / "table.db"
app.config["input_file"] = Path("data") / "input.db"

if not app.config["DB_FILE"].exists():
    print("Created db from scratch")
    shutil.copyfile(app.config["input_file"], app.config["DB_FILE"])


runner = TaskRunner(app.config["DB_FILE"])


@app.before_request
def check_initialization():
    if request.endpoint in ("initialization_wizard", "scripts", "styles", "static"):
        return

    connection = DbConnection(app.config["DB_FILE"])
    Controller(connection).add_configuration()

    config = connection.configurationentry.get_first()
    connection.close()

    if not config or not config.initialized:
        return redirect(url_for("initialization_wizard"))


class PagePagination:
    def __init__(self, request):
        self.request = request

    def get_page(self):
        page = self.request.args.get("p", default=1, type=int)
        return max(page, 1)

    def get_offset(self):
        page = self.get_page()
        return (page - 1) * page_size

    def get_limit(self):
        return page_size


def parse_search(search, table, tags_table):
    """
    Supports:
      - "keyword"                  → search all fields
      - "title=keyword"            → search specific field
      - URL-encoded input supported (e.g. title%3Dkeyword)
    """
    if not search:
        return None

    search = unquote(search).strip()

    searchable_fields = {
        "id": table.c.id,
        "title": table.c.title,
        "description": table.c.description,
        "link": table.c.link,
        "source_url": table.c.source_url,
        "source_id": table.c.source_id,
        "tag": tags_table.c.tag,
    }

    if "==" in search:
        field, value = search.split("==", 1)
        field = field.strip()
        value = value.strip()

        column = searchable_fields.get(field)
        if column is not None and value:
            return [column == value]

    elif "=" in search:
        field, value = search.split("=", 1)
        field = field.strip()
        value = value.strip()

        column = searchable_fields.get(field)
        if column is not None and value:
            return [column.ilike(f"%{value}%")]

    return [
          table.c.title.ilike(f"%{search}%"),
          table.c.description.ilike(f"%{search}%"),
          table.c.link.ilike(f"%{search}%"),
          table.c.source_url.ilike(f"%{search}%"),
          tags_table.c.tag.ilike(f"%{search}%"),
    ]


def get_view_conditions(view=None):
    if not view:
        # TODO linkarchive should contain default view obtainer
        # views = SearchView()
        defaults = views_table.get_where({"default" : True})
        for default in defaults:
            view = default
    else:
        searched_views = views_table.get_where({id : view})
        for searched_view in searched_views:
            view = searched_view


def get_entries_for_request(connection, order_by, limit, offset, search=None, view_id=None):
    table = connection.entries_table.get_table()
    tags_table = connection.entrycompactedtags.get_table()
    social_table = connection.socialdata.get_table()
    views_table = connection.searchview

    print(f"View : {view_id}")
    view = None
    if not view_id:
        # TODO linkarchive should contain default view obtainer
        # views = SearchView()
        defaults = views_table.get_where({"default" : True})
        for default in defaults:
            print("Using default view")
            view = default
    else:
        searched_views = views_table.get_where({"id" : view_id})
        for searched_view in searched_views:
            print("Using search view")
            view = searched_view
    print(f"Found view {view}")

    conditions = parse_search(search, table, tags_table)

    view_conditions = None
    if view and view.filter_statement == "bookmarked=True":
        print("Setting view conditions")
        view_conditions = [table.c.bookmarked == True]

    if not order_by and view:
        order_by = view.order_by
    print(f"Using order by {order_by}")

    order_bys = [table.c.date_published.desc()]
    if order_by == "-view_count":
        order_bys = [social_table.c.view_count.desc()]
    elif order_by == "view_count":
        order_bys = [social_table.c.view_count.asc()]
    elif order_by == "-stars":
        order_bys = [social_table.c.stars.desc()]
    elif order_by == "stars":
        order_bys = [social_table.c.stars.asc()]
    elif order_by == "-followers_count":
        order_bys = [social_table.c.followers_count.desc()]
    elif order_by == "followers_count":
        order_bys = [social_table.c.followers_count.asc()]
    elif order_by == "-date_published":
        order_bys = [table.c.date_published.desc()]
    elif order_by == "date_published":
        order_bys = [table.c.date_published.asc()]
    elif order_by == "-date_created":
        order_bys = [table.c.date_created.desc()]
    elif order_by == "date_created":
        order_bys = [table.c.date_created.asc()]
    elif order_by == "-link":
        order_bys = [table.c.link.desc()]
    elif order_by == "link":
        order_bys = [table.c.link.asc()]
    elif order_by == "-page_rating_votes":
        order_bys = [table.c.page_rating_votes.desc()]
    elif order_by == "page_rating_votes":
        order_bys = [table.c.page_rating_votes.asc()]
    else:
        order_bys = [table.c.date_published.desc()]

    entries_select = (select(table,
                             tags_table.c.tag,
                             social_table.c.thumbs_up,
                             social_table.c.thumbs_down,
                             social_table.c.view_count,
                             social_table.c.followers_count,
                             social_table.c.stars,
                             social_table.c.upvote_ratio,
                             social_table.c.upvote_diff,
                             social_table.c.upvote_view_ratio,
                             )
                     .outerjoin(tags_table, table.c.id == tags_table.c.entry_id)
                     .outerjoin(social_table, table.c.id == social_table.c.entry_id)
                     .order_by(*order_bys)
                     )

    if conditions:
        conditions = or_(*conditions)
        if view_conditions:
            conditions = and_(*view_conditions, conditions)
    elif view_conditions:
        conditions = or_(*view_conditions)

    if conditions is not None:
        print("Using search conditions")
        print(conditions)
        entries_select = entries_select.where(conditions)
    if offset is not None:
        entries_select = entries_select.offset(offset)
    if limit is not None:
        entries_select = entries_select.limit(limit)

    entries = connection.connection.execute(entries_select)

    entries = list(entries)

    return entries


def get_sources_for_request(connection, limit, offset, search=None):
    table = connection.sources_table.get_table()

    order_by = [
      connection.sources_table.get_table().c.title.desc()
    ]

    if search and search != "":
        conditions = [
          table.c.title.ilike(f"%{search}%"),
          table.c.url.ilike(f"%{search}%"),
        ]
        sources = list(connection.sources_table.get_where(limit=limit,
                                                          offset=offset,
                                                          order_by=order_by,
                                                          conditions=conditions))
    else:
        sources = list(connection.sources_table.get_where(limit=limit,
                                                          offset=offset,
                                                          order_by=order_by))
    print(f"len {sources}")
    return sources


@app.route("/")
def main_index():
    return redirect(url_for("search"))


@app.route("/index")
def index():
    connection = DbConnection(app.config["DB_FILE"])
    config = connection.configurationentry.get_first()
    html_text = get_view(INDEX_TEMPLATE, title=config.instance_title)
    return render_template_string(html_text, version=__version__, title=config.instance_title)


@app.route('/scripts/<path:filename>')
def scripts(filename):
    return send_from_directory("scripts/", filename)


@app.route('/styles/<path:filename>')
def styles(filename):
    return send_from_directory("styles/", filename)


@app.route("/search")
def search():
    connection = DbConnection(app.config["DB_FILE"])
    config = connection.configurationentry.get_first()

    default_values = {}
    default_values["view_display_type"] = config.display_type

    return render_template_string(PROJECT_TEMPLATE, title=config.instance_title, default_values=default_values)


@app.route("/sources")
def sources():
    connection = DbConnection(app.config["DB_FILE"])

    search = request.args.get("search")

    pagination = PagePagination(request)
    limit = pagination.get_limit()
    offset = pagination.get_offset()

    page = pagination.get_page()
    prev_page = page - 1
    next_page = page + 1

    pagination_text = "";
    pagination_text += '<div id="pagination">'
    pagination_text += '<nav>'
    pagination_text += '<ul class="pagination">'
    if page > 2:
        pagination_text += '<a href="?p=1" class="btnNavigation page-link">|&lt;</a>';
    if page > 1:
        pagination_text += f'<a href="?p={prev_page}" class="btnNavigation page-link">&lt;</a>';
    pagination_text += '<li class="page-item">'
    pagination_text += f'<a href="?p={next_page}" class="btnNavigation page-link" >&gt;</a>';
    pagination_text += '</li>'
    pagination_text += '</ul>'
    pagination_text += '</nav>'
    pagination_text += '</div>'

    sources_len = connection.sources_table.count()

    sources = get_sources_for_request(connection, limit, offset, search)
    template_text = SOURCES_LIST_TEMPLATE
    template_text = template_text.replace("{{pagination_text}}", pagination_text)
    if search is None:
        template_text = template_text.replace("{{search_value}}", "")
    else:
        template_text = template_text.replace("{{search_value}}", search)

    html_text = get_view(template_text, title="Sources")

    return render_template_string(html_text, sources=sources, sources_length=sources_len)


@app.route("/sources-fetch-period", methods=["GET", "POST"])
def sources_fetch_period():
    connection = DbConnection(app.config["DB_FILE"])

    if request.method == "POST":
        fetch_period = request.form.get("fetch-period", 0)
        sourcedatas = connection.sourceoperationaldata.get_where()
        for source_data in sourcedatas:
            json_data = {}
            json_data["fetch_period"] = fetch_period
            connection.sources_table.update_json_data(id=source_data.id, json_data=json_data)

    connection.close()
    html_text = get_view(SOURCES_FETCH_TIME, title="Set sources fetch period")
    return render_template_string(html_text)


@app.route("/source/<int:source_id>", methods=["GET", "POST"])
def source(source_id):
    connection = DbConnection(app.config["DB_FILE"])

    source_item = connection.sources_table.get(id=source_id)
    source_ops = list(connection.sourceoperationaldata.get_where({"source_obj_id" : source_id}))
    source_op = None
    if len(source_ops) > 0:
        source_op = source_ops[0]

    if request.method == "POST":
        data["fetch_period"] = request.form.get("fetch_period", 0)
        data["xpath"] = request.form.get("xpath", "")
        connection.sources_table.update_json_data(id=source_op.id, json_data=data)
        html_text = get_view(OK_TEMPLATE, title="Updated")
        connection.close()
        return render_template_string(html_text)

    if source_item:
        html_text = get_view(SOURCE_TEMPLATE, title=source_item.title)

        return render_template_string(html_text, source_item=source_item, source_op_data = source_op)
    else:
        html_text = get_view(NOK_TEMPLATE, title="Cannot find source")
        return render_template_string(html_text)


@app.route("/source-edit", methods=["GET", "POST"])
def source_edit():
    connection = DbConnection(app.config["DB_FILE"])

    source_id = request.args.get("id")
    controller = Sources(connection)
    source = controller.get(id=source_id)

    if request.method == "POST":
        title = request.form.get("title", "")
        url = request.form.get("url", "")
        language = request.form.get("language", "")

        json = {}
        json["title"] = title
        json["url"] = url
        json["language"] = language

        controller.get_table().update_json_data(id=source_id, json_data=json)

        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
        html_text = get_view(template_html, title="OK")
        connection.close()
        return render_template_string(html_text)

    html_text = get_view(SOURCE_EDIT_TEMPLATE, title="Edit source")
    return render_template_string(html_text, source=source)


@app.route("/source-fetch")
def source_fetch():
    connection = DbConnection(app.config["DB_FILE"])

    source_id = request.args.get("id")
    if source_id:
        source = sources.get_table().get(id=source_id)

        job = BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source.id))

        template_html = STR_TEMPLATE.replace("{template_string}", "Added source read job")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)
    else:
        template_html = STR_TEMPLATE.replace("{template_string}", "Cannot fetch source")
        html_text = get_view(template_html, title="NOK")
        return render_template_string(html_text)


@app.route("/add-sources", methods=["GET", "POST"])
def add_sources():
    connection = DbConnection(app.config["DB_FILE"])

    if request.method == "POST":
        raw_text = request.form.get("sources", "")

        controller = Controller(connection)
        controller.add_sources_text(raw_text)
        connection.close()

        template_html = STR_TEMPLATE.replace("{template_string}", "Wait until sources are added")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)

    html_text = get_view(ADD_SOURCES_TEMPLATE, title="Add sources")
    return render_template_string(html_text, raw_data="")


@app.route("/add-links", methods=["GET", "POST"])
def add_links():
    connection = DbConnection(app.config["DB_FILE"])

    if request.method == "POST":
        raw_text = request.form.get("sources", "")

        controller = Controller(connection)
        controller.add_links_text(raw_text)
        connection.close()

        template_html = STR_TEMPLATE.replace("{template_string}", "Wait until links are added")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)

    html_text = get_view(ADD_LINKS_TEMPLATE, title="Add links")
    return render_template_string(html_text, raw_data="")


@app.route("/entry", methods=["GET"])
def entry():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")
    entries = Entries(connection=connection)
    entry = entries.get(id=entry_id)

    html_text = get_view(ENTRY_TEMPLATE, title="Entry")
    return render_template_string(html_text, entry=entry)


@app.route("/entry-bookmark")
def entry_bookmark():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")
    entries = Entries(connection=connection)
    entry = entries.get(id=entry_id)

    if entry:
        json_data = {}
        json_data["bookmarked"] = True
        entries.get_table().update_json_data(entry.id, json_data=json_data)
        connection.close()

        return redirect(url_for("search"))


@app.route("/entry-unbookmark")
def entry_unbookmark():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")
    entries = Entries(connection=connection)
    entry = entries.get(id=entry_id)

    if entry:
        json_data = {}
        json_data["bookmarked"] = False
        entries.get_table().update_json_data(entry.id, json_data=json_data)
        connection.close()

        return redirect(url_for("search"))


@app.route("/check-later-list")
def check_later_list():
    connection = DbConnection(app.config["DB_FILE"])

    check_controller = CheckLater(connection=connection)
    entries = check_controller.get_entries()

    html_text = get_view(CHECK_LATER_LIST_TEMPLATE, title="Check later list")
    return render_template_string(html_text, entries=entries)


@app.route("/check-later-clear", methods=["GET"])
def check_later_clear():
    connection = DbConnection(app.config["DB_FILE"])

    check_controller = CheckLater(connection=connection)
    check_controller.truncate()

    template_html = STR_TEMPLATE.replace("{template_string}", "OK")
    html_text = get_view(template_html, title="OK")
    return render_template_string(html_text)


@app.route("/entry-dynamic-data", methods=["GET"])
def entry_dynamic_detail():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")
    entries = Entries(connection)
    entry = entries.get(id=entry_id)

    script = """
   let url_location = `/api/dynamic`;
   let url_address = `${url_location}?link=${link}`;
   getDynamicJson(url_address, function(data) {
      let text = GetAllPropertiesText(data);
      $("#listData").html(text);
   });
    """

    script = script.replace("${link}", entry.link)
    template = PROJECT_TEMPLATE_MAIN.replace("{{script}}", script)

    return render_template_string(template, title=entry.title, script=script)


@app.route("/entry-check-later", methods=["GET"])
def entry_check_later():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")

    entry_controller = Entries(connection=connection)
    entry = entry_controller.get(id=entry_id)
    if not entry:
        template_html = STR_TEMPLATE.replace("{template_string}", "NOK")
        html_text = get_view(template_html, title="NOK")
        return render_template_string(html_text)

    check_controller = CheckLater(connection=connection)
    status = check_controller.check_later(entry)

    if status:
        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
    else:
        template_html = STR_TEMPLATE.replace("{template_string}", "NOK")

    html_text = get_view(template_html, title="OK")
    return render_template_string(html_text)


@app.route("/entry-not-check-later", methods=["GET"])
def entry_not_check_later():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")

    entry_controller = Entries(connection=connection)
    entry = entry_controller.get(id=entry_id)
    if not entry:
        template_html = STR_TEMPLATE.replace("{template_string}", "NOK")
        html_text = get_view(template_html, title="NOK")
        return render_template_string(html_text)

    check_controller = CheckLater(connection=connection)
    status = check_controller.not_check_later(entry)

    if status:
        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
    else:
        template_html = STR_TEMPLATE.replace("{template_string}", "NOK")
    html_text = get_view(template_html, title="OK")
    return render_template_string(html_text)


@app.route("/entry-edit", methods=["GET", "POST"])
def entry_edit():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")
    if not entry_id:
        template_html = STR_TEMPLATE.replace("{template_string}", "NOK - cannot read ID")
        html_text = get_view(template_html, title="NOK")
        return render_template_string(html_text)

    entries = Entries(connection)
    entry = entries.get(id=entry_id)

    if not entry:
        template_html = STR_TEMPLATE.replace("{template_string}", "NOK - cannot find entry")
        html_text = get_view(template_html, title="NOK")
        return render_template_string(html_text)

    if request.method == "POST":
        title = request.form.get("title", "")
        link = request.form.get("link", "")
        description = request.form.get("description", "")
        age = request.form.get("age", "")
        language = request.form.get("language", "")

        age_int = 0
        try:
            age_int = int(age)
        except Exception as E:
            pass

        json = {}
        json["title"] = title
        json["link"] = link
        json["description"] = description
        json["language"] = language
        json["age"] = age_int

        entries.get_table().update_json_data(id=entry_id, json_data=json)
        connection.close()

        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)

    html_text = get_view(ENTRY_EDIT_TEMPLATE, title="Edit entry")
    return render_template_string(html_text, entry=entry)


@app.route("/entry-update")
def entry_update():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")

    if entry_id:
        is_job = BackgroundJob(connection).is_job(job_name=BackgroundJob.JOB_LINK_UPDATE_DATA, subject=str(entry_id))

        if is_job:
            template_html = STR_TEMPLATE.replace("{template_string}", "NOK - exists")
            html_text = get_view(template_html, title="OK")
            return render_template_string(html_text)

        BackgroundJob(connection).create_single_job(job_name=BackgroundJob.JOB_LINK_UPDATE_DATA, subject=str(entry_id))
        connection.close()

        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)

    else:
        template_html = STR_TEMPLATE.replace("{template_string}", "NOK - cannot find entry")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)


@app.route("/entry-reset")
def entry_reset():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")

    if entry_id:
        BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_RESET_DATA, subject=str(entry_id))
        connection.close()

        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)

    else:
        template_html = STR_TEMPLATE.replace("{template_string}", "NOK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)


@app.route("/entry-vote", methods=["GET", "POST"])
def entry_vote():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")
    current_vote = 0
    votes = EntryVotes(connection=connection)

    if request.method == "POST":
        entry_vote = request.form.get("entry-vote", "")

        votes.set(entry_id=entry_id, vote=entry_vote)
        connection.close()

        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)
    else:
        current_vote = votes.get(entry_id=entry_id)

    html_text = get_view(ENTRY_VOTE_TEMPLATE, title="Vote entry")
    return render_template_string(html_text, entry_id=entry_id, current_vote=current_vote)


@app.route("/entry-tag", methods=["GET", "POST"])
def entry_tag():
    connection = DbConnection(app.config["DB_FILE"])
    table = ReflectedTable(connection.engine, connection.connection)
    table.vacuum()

    entry_id = request.args.get("id")
    entries = Entries(connection=connection)
    entry = entries.get(id=entry_id)

    tags = EntryTags(connection=connection)

    if request.method == "POST":
        entry_tags = request.form.get("entry-tag", "")

        tags.set(entry_id=entry_id, tags=entry_tags)
        connection.close()

        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)
    else:
        current_tags = tags.get(entry_id=entry_id)

    html_text = get_view(ENTRY_TAG_TEMPLATE, title="Tag entry")
    return render_template_string(html_text, entry_id=entry_id, current_tags=current_tags, entry=entry)


@app.route("/rss/<int:source_id>")
def rss(source_id):
    connection = DbConnection(app.config["DB_FILE"])

    source = connection.sources_table.get(id=source_id)
    entries = connection.entries_table.get_where({"source_id":source_id})

    entry_list = []
    for entry in entries:
        entry_json = entry_to_json(entry)
        entry_list.append(entry_json)

    source_json = source_to_json(source)

    rss_text = source_and_entries_to_rss(source_json, entry_list)
    return Response(rss_text, mimetype="application/rss+xml")


@app.route("/block-rules")
def block_rules():
    html_text = get_view(BLOCK_RULES_TEMPLATE, title="Block rules")
    return render_template_string(html_text)


@app.route("/block-url", methods=["GET", "POST"])
def block_url():
    connection = DbConnection(app.config["DB_FILE"])

    controller = BlockEntry(connection = connection)

    if request.method == "POST":
        raw_text = request.form.get("sources", "")

        split_text = raw_text.split("\n")
        for line in split_text:
            stripped = line.strip()
            if stripped:
                controller.add(stripped)
        connection.close()
        return redirect(url_for("index"))

    sources = []
    html_text = get_view(ADD_BLOCK_ENTRIES_TEMPLATE, title="Block URL")

    raw_data = ""

    return render_template_string(html_text, raw_data=raw_data)


@app.route("/define-block-rules", methods=["GET", "POST"])
def define_block_rules():
    connection = DbConnection(app.config["DB_FILE"])

    controller = BlockEntry(connection = connection)

    if request.method == "POST":
        controller.truncate()

        raw_text = request.form.get("sources", "")
        split_text = raw_text.split("\n")
        for line in split_text:
            stripped = line.strip()
            if stripped:
                controller.add(stripped)
        connection.close()
        return redirect(url_for("index"))

    sources = []
    html_text = get_view(DEFINE_BLOCK_ENTRIES_TEMPLATE, title="Set Block Rules")

    blocks = controller.get_table().get_where({})

    raw_data = ""
    for block in blocks:
        raw_data += "\r\n" + block.url

    return render_template_string(html_text, raw_data=raw_data)


@app.route("/entry-rules")
def entry_rules():
    connection = DbConnection(app.config["DB_FILE"])
    controller = Controller(connection)

    rules = EntryRules(connection = connection)

    rule_objects = rules.get_table().get_where({})

    html_text = get_view(ENTRY_RULES_TEMPLATE, title="Entry rules")
    return render_template_string(html_text, rules = rule_objects)


@app.route("/entry-rule")
def entry_rule():
    connection = DbConnection(app.config["DB_FILE"])
    controller = Controller(connection)

    entry_rule_id = request.args.get("id")

    rules = EntryRules(connection = connection)

    rule = rules.get(id=entry_rule_id)

    html_text = get_view(ENTRY_RULE_TEMPLATE, title="Entry rule")
    return render_template_string(html_text, rule=rule)


@app.route("/entry-rule-add", methods=["GET", "POST"])
def entry_rule_add():
    connection = DbConnection(app.config["DB_FILE"])
    controller = Controller(connection)

    if request.method == "POST":
        rules = EntryRules(connection = connection)

        html_text = get_view(ENTRY_RULE_ADD_TEMPLATE, title="Entry rule")
        connection.close()
        return render_template_string(html_text, rule=rule)

    html_text = get_view(ENTRY_RULE_ADD_TEMPLATE, title="Entry rule")
    return render_template_string(html_text, rule=rule)


@app.route("/entry-rule-edit", methods=["GET", "POST"])
def entry_rule_edit():
    connection = DbConnection(app.config["DB_FILE"])
    controller = Controller(connection)

    entry_rule_id = request.args.get("id")
    if request.method == "POST":
        connection.close()
        html_text = get_view(ENTRY_RULE_EDIT_TEMPLATE, title="Entry rule")
        return render_template_string(html_text, rule=rule)

    html_text = get_view(ENTRY_RULE_EDIT_TEMPLATE, title="Entry rule")
    return render_template_string(html_text, rule=rule)


@app.route("/entry-rule-remove")
def entry_rule_remove():
    connection = DbConnection(app.config["DB_FILE"])
    controller = Controller(connection)

    entry_rule_id = request.args.get("id")

    rules = EntryRules(connection = connection)
    rules.delete(id=entry_rule_id)

    html_text = get_view(OK_TEMPLATE, title="Remove rule")
    return render_template_string(html_text)


@app.route("/views")
def views():
    connection = DbConnection(app.config["DB_FILE"])
    controller = Controller(connection)

    views = SearchView(connection = connection)

    view_objects = views.get_table().get_where({})

    html_text = get_view(VIEWS_TEMPLATE, title="Views")
    return render_template_string(html_text, views = view_objects)


@app.route("/view")
def view():
    connection = DbConnection(app.config["DB_FILE"])
    controller = Controller(connection)

    entry_rule_id = request.args.get("id")

    views = SearchView(connection = connection)

    view = views.get(id=entry_rule_id)

    html_text = get_view(VIEW_TEMPLATE, title="View")
    return render_template_string(html_text, view=view)


@app.route("/view-add", methods=["GET", "POST"])
def view_add():
    connection = DbConnection(app.config["DB_FILE"])
    controller = Controller(connection)

    if request.method == "POST":
        views = SearchView(connection = connection)
        view_id = views.add()
        view = views.get(id=view_id)

        html_text = get_view(VIEW_ADD_TEMPLATE, title="View add")
        connection.close()
        return render_template_string(html_text, view=view)

    html_text = get_view(VIEW_ADD_TEMPLATE, title="View add")
    connection.close()
    return render_template_string(html_text)


@app.route("/view-edit", methods=["GET", "POST"])
def view_edit():
    connection = DbConnection(app.config["DB_FILE"])
    controller = Controller(connection)

    view_id = request.args.get("id")
    views = SearchView(connection = connection)
    view = views.get(id=view_id)

    if request.method == "POST":
        json_data = {}
        json_data["name"] = request.args.get("name")
        json_data["default"] = request.args.get("default")
        json_data["priority"] = request.args.get("priority")
        json_data["filter_statement"] = request.args.get("filter_statement")
        json_data["order_by"] = request.args.get("order_by")

        json_data["default"] = json_data["default"] == "True"

        connection.searchview.update_json_data(id = view_id, json_data=json_data)

        connection.close()
        html_text = get_view(VIEW_ADD_TEMPLATE, title="View edit")
        return render_template_string(html_text, view=view)

    html_text = get_view(VIEW_ADD_TEMPLATE, title="View edit")
    connection.close()
    return render_template_string(html_text, view=view)


@app.route("/view-remove")
def view_remove():
    connection = DbConnection(app.config["DB_FILE"])
    controller = Controller(connection)

    view_id = request.args.get("id")

    connection.searchview.delete(id=view_id)

    html_text = get_view(OK_TEMPLATE, title="Remove view")
    connection.close()
    return render_template_string(html_text)


@app.route("/remove-all-entries")
def remove_all_entries():
    connection = DbConnection(app.config["DB_FILE"])

    connection.entries_table.truncate()
    connection.socialdata.truncate()

    connection.usertags.truncate()
    connection.compactedtags.truncate()
    connection.usercompactedtags.truncate()
    connection.entrycompactedtags.truncate()

    connection.uservotes.truncate()

    connection.close()

    html_text = get_view(OK_TEMPLATE, title="Remove all entries")
    return render_template_string(html_text)


@app.route("/remove-all-logs")
def remove_all_logs():
    connection = DbConnection(app.config["DB_FILE"])

    connection.applogging.truncate()
    connection.close()

    html_text = get_view(OK_TEMPLATE, title="Remove all logs")
    return render_template_string(html_text)


@app.route("/remove-all-jobs")
def remove_all_jobs():
    connection = DbConnection(app.config["DB_FILE"])

    connection.backgroundjob.truncate()
    connection.close()

    html_text = get_view(OK_TEMPLATE, title="Remove all jobs")
    return render_template_string(html_text)


@app.route("/remove-all-sources")
def remove_all_sources():
    connection = DbConnection(app.config["DB_FILE"])

    connection.sources_table.truncate()
    connection.sourceoperationaldata.truncate()
    connection.close()

    html_text = get_view(OK_TEMPLATE, title="Remove all sources")
    return render_template_string(html_text)


@app.route("/remove-all-social-data")
def remove_all_social_data():
    connection = DbConnection(app.config["DB_FILE"])

    connection.socialdata.truncate()
    connection.close()

    html_text = get_view(OK_TEMPLATE, title="Remove social data OK")
    return render_template_string(html_text)


@app.route("/remove-all-tags")
def remove_all_tags():
    connection = DbConnection(app.config["DB_FILE"])

    connection.usertags.truncate()
    connection.compactedtags.truncate()
    connection.usercompactedtags.truncate()
    connection.entrycompactedtags.truncate()
    connection.close()

    html_text = get_view(OK_TEMPLATE, title="Remove tags OK")
    return render_template_string(html_text)


@app.route("/remove-all-votes")
def remove_all_votes():
    connection = DbConnection(app.config["DB_FILE"])
    connection.uservotes.truncate()
    connection.close()

    html_text = get_view(OK_TEMPLATE, title="Remove votes OK")
    return render_template_string(html_text)


@app.route("/remove-all-entry-rules")
def remove_all_entry_rules():
    connection = DbConnection(app.config["DB_FILE"])
    connection.entry_rules.truncate()
    connection.close()

    html_text = get_view(OK_TEMPLATE, title="Remove entry rules OK")
    return render_template_string(html_text)


@app.route("/remove-all-views")
def remove_all_views():
    connection = DbConnection(app.config["DB_FILE"])
    connection.searchview.truncate()
    connection.close()

    html_text = get_view(OK_TEMPLATE, title="Remove Search views OK")
    return render_template_string(html_text)


@app.route("/remove-all-block-entries")
def remove_all_block_entries():
    connection = DbConnection(app.config["DB_FILE"])
    connection.blockentry.truncate()

    rules_controller = EntryRules(connection)
    block_entries = BlockEntry(connection)

    if rules_controller.count() != 0 and block_entries.count() == 0:
        rules = rules_controller.get_where({})
        for rule in rules:
            if rule.trigger_rule_url:
                block_entries.add(rule.trigger_rule_url)

    connection.close()

    html_text = get_view(OK_TEMPLATE, title="Block entry remove OK")
    return render_template_string(html_text)


@app.route("/remove-source")
def remove_source():
    connection = DbConnection(app.config["DB_FILE"])

    source_id = request.args.get("id")

    source = connection.sources_table.get(id=source_id)
    if source:
        sources = Sources(connection)
        sources.delete(id=source.id)

        html_text = get_view(OK_TEMPLATE, title="Remove source")
        return render_template_string(html_text)
    else:
        html_text = get_view(NOK_TEMPLATE, title="Remove source")
        return render_template_string(html_text)


@app.route("/remove-entry")
def remove_entry():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")

    entry = connection.entries_table.get(id=entry_id)
    if source:
        connection.entries_table.delete_where({"id" : entry.id})

    html_text = get_view(OK_TEMPLATE, title="Remove entry")
    return render_template_string(html_text)


#### System


@app.route("/logs")
def logs():
    connection = DbConnection(app.config["DB_FILE"])

    html_text = get_view(LOGS_TEMPLATE, title="Logs")

    order_by = [
            connection.applogging.get_table().c.date.desc()
            ]

    logs = list(connection.applogging.get_where(order_by=order_by))
    len_logs = len(logs)

    return render_template_string(html_text, logs=logs, len_logs=len_logs)


@app.route("/jobs")
def jobs():
    connection = DbConnection(app.config["DB_FILE"])

    html_text = get_view(JOBS_TEMPLATE, title="Jobs")

    order_by = [
            connection.backgroundjob.get_table().c.date_created.desc()
            ]

    jobs = list(connection.backgroundjob.get_where(order_by=order_by))
    len_jobs = len(jobs)

    return render_template_string(html_text, jobs=jobs, len_jobs=len_jobs)


@app.route("/add-job", methods=["GET", "POST"])
def add_job():
    connection = DbConnection(app.config["DB_FILE"])

    if request.method == "POST":
        job_name = request.form.get("job_name", "")
        args = request.form.get("args", "")
        subject = request.form.get("subject", "")

        job_controller = BackgroundJob(connection)
        job_id = job_controller.create_single_job(job_name = job_name, subject=subject, args=args)
        if job_id is None:
            template_html = STR_TEMPLATE.replace("{template_string}", "Could not add job")
            html_text = get_view(template_html, title="NOK")
            return render_template_string(html_text)

        template_html = STR_TEMPLATE.replace("{template_string}", "Job added")
        html_text = get_view(template_html, title="NOK")
        return render_template_string(html_text)

    html_text = get_view(ADD_JOB_TEMPLATE, title="Add job")
    return render_template_string(html_text, raw_data="")


def get_stats_map(connection):
    stats_map = {}

    stats_map["Entries"] = connection.entries_table.count()
    stats_map["Sources"] = connection.sources_table.count()
    stats_map["Sources Operational Data"] = connection.sourceoperationaldata.count()
    stats_map["Entry rules"] = connection.entry_rules.count()
    stats_map["Social data"] = connection.socialdata.count()
    stats_map["AppLogging"] = connection.applogging.count()
    stats_map["ConfigurationEntry"] = connection.configurationentry.count()
    stats_map["BackgroundJobs"] = connection.backgroundjob.count()
    stats_map["BackgroundJobsHistory"] = connection.backgroundjobhistory.count()
    stats_map["UserTags"] = connection.usertags.count()
    stats_map["CompactedTags"] = connection.compactedtags.count()
    stats_map["UserCompactedTags"] = connection.usercompactedtags.count()
    stats_map["EntryCompactedTags"] = connection.entrycompactedtags.count()
    stats_map["UserVotes"] = connection.uservotes.count()
    stats_map["ReadLater"] = connection.readlater.count()
    stats_map["SearchView"] = connection.searchview.count()
    stats_map["Block entries"] = connection.blockentry.count()

    system = System.get_object()
    stats_map["System state"] = system.is_system_ok()
    return stats_map


@app.route("/status")
def status():
    connection = DbConnection(app.config["DB_FILE"])

    stats_map = get_stats_map(connection)

    program_info = OrderedDict()
    program_info["Name"] = __project_name__
    program_info["version"] = __version__

    html_text = get_view(STATS_TEMPLATE, title="Stats")
    return render_template_string(html_text, stats=stats_map, program_info=program_info)


@app.route("/admin")
def admin():
    connection = DbConnection(app.config["DB_FILE"])

    html_text = get_view(ADMIN_TEMPLATE, title="Admin")
    return render_template_string(html_text)


def to_bool(variable):
    if not variable:
        return False
    if variable == "true":
        return True
    if variable == "True":
        return True
    if variable == "1":
        return True
    return False


@app.route("/initialization-wizard", methods=["GET", "POST"])
def initialization_wizard():
    connection = DbConnection(app.config["DB_FILE"])
    config = connection.configurationentry.get_first()

    if request.method == "POST":
        initialization_type = request.form.get("initialization_type", "")
        display_type = request.form.get("display_type", "")

        if not config:
            Controller(connection).add_configuration()
            config = connection.configurationentry.get_first()

        data = {}
        data["initialized"] = True
        data["initialization_type"] = initialization_type
        data["display_type"] = display_type

        connection.configurationentry.update_json_data(id=config.id, json_data=data)
        connection.close()

        return redirect(url_for("search"))

    html_text = get_view(INITIALIZATION_WIZARD_TEMPLATE, title="Initialization Wizard")
    return render_template_string(html_text)


@app.route("/configuration", methods=["GET", "POST"])
def configuration():
    connection = DbConnection(app.config["DB_FILE"])

    system = System.get_object()
    config = connection.configurationentry.get_first()

    if request.method == "POST":
        title = request.form.get("instance_title", "")
        description = request.form.get("instance_description", "")
        remote_webtools_server_location = request.form.get("remote_webtools_server_location", "")
        display_type = request.form.get("display_type", "")
        enable_social_data = request.form.get("enable_social_data", "")
        new_entries_fetch_social_data = request.form.get("new_entries_fetch_social_data", "")
        entry_update_fetches_social_data = request.form.get("entry_update_fetches_social_data", "")

        data = {}
        if title != "None":
            data["instance_title"] = title
        if description != "None":
            data["instance_description"] = description
        if display_type != "None":
            data["display_type"] = display_type
        if remote_webtools_server_location != "None":
            data["remote_webtools_server_location"] = remote_webtools_server_location

        data["enable_social_data"] = to_bool(enable_social_data)
        data["new_entries_fetch_social_data"] = to_bool(new_entries_fetch_social_data)
        data["entry_update_fetches_social_data"] = to_bool(entry_update_fetches_social_data)
        data["number_of_update_entries"] = request.form.get("number_of_update_entries", "")
        data["initialization_type"] = request.form.get("initialization_type", "")

        connection.configurationentry.update_json_data(id=config.id, json_data=data)
        connection.close()

        html_text = get_view(OK_TEMPLATE, title="Changes applied")
        return render_template_string(html_text)

    instance_fields = {}
    instance_fields["instance_title"] = config.instance_title
    instance_fields["instance_description"] = config.instance_description
    instance_fields["initialization_type"] = config.initialization_type
    instance_fields["display_type"] = config.display_type
    instance_fields["remote_webtools_server_location"] = config.remote_webtools_server_location
    instance_fields["enable_social_data"] = config.enable_social_data
    instance_fields["new_entries_fetch_social_data"] = config.new_entries_fetch_social_data
    instance_fields["entry_update_fetches_social_data"] = config.entry_update_fetches_social_data
    instance_fields["number_of_update_entries"] = config.number_of_update_entries

    html_text = get_view(CONFIGURATION_TEMPLATE, title="Configuration")
    return render_template_string(html_text, configuration=instance_fields)


#### Tools

@app.route("/link-test", methods=["GET"])
def link_test():
    connection = DbConnection(app.config["DB_FILE"])

    link = request.args.get("link")

    if link:
        text = ""

        exists = connection.entries_table.exists(link=link)
        if exists:
            text += "Link already exists in entries table"

        blocks = BlockEntry(connection)
        if blocks.is_blocked(link):
            text += "Link is blocked by block rules"

        rules = EntryRules(connection)
        if rules.is_url_blocked(link):
            text += "Link is blocked by entry rules"

        if not text:
            text = f"Link {link} is OK"

        template_html = STR_TEMPLATE.replace("{template_string}", text)
        html_text = get_view(template_html, title="OK")
        connection.close()
        return render_template_string(html_text)

    # TODO add form
    template_html = STR_TEMPLATE.replace("{template_string}",
                                         f"Provide a link")
    html_text = get_view(template_html, title="OK")
    connection.close()
    return render_template_string(html_text)


#### JSON

@app.route("/api/entries")
def api_entries():
    connection = DbConnection(app.config["DB_FILE"])

    pagination = PagePagination(request)
    limit = pagination.get_limit()
    offset = pagination.get_offset()

    search = request.args.get("search")
    order_by = request.args.get("order_by")
    view = request.args.get("view")

    json_entries = []
    entries = get_entries_for_request(connection=connection,
                                      order_by=order_by,
                                      limit=limit,
                                      offset=offset,
                                      search=search,
                                      view_id=view)

    for entry in entries:
        socialdata = SocialData(connection=connection)
        social_data_object = socialdata.get(entry_id=entry.id)

        tags = EntryTags(connection)
        tags = tags.get_map(entry_id=entry.id)

        if entry.source_id:
            entry_source = connection.sources_table.get(id=entry.source_id)

            json_entry_data = entry_to_json(entry,
                                            with_id=True,
                                            source=entry_source,
                                            social_data=social_data_object,
                                            tags=tags)
            json_entries.append(json_entry_data)
        else:
            json_entry_data = entry_to_json(entry,
                                            with_id=True,
                                            source=None,
                                            social_data=social_data_object,
                                            tags=tags)
            json_entries.append(json_entry_data)

    json_data = {}
    json_data["entries"] = json_entries

    return jsonify(json_data)


@app.route("/api/entry")
def api_entry():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")
    entry_controller = Entries(connection)
    entry = entry_controller.get(id=entry_id)

    #search_entries = entry_controller.get_table().get_where({"id" : entry_id})
    #entry=None
    #for search_entry in search_entries:
    #    entry = search_entry

    if entry:
        socialdata = SocialData(connection=connection)
        social_data_object = socialdata.get(entry_id=entry.id)

        tags = EntryTags(connection)
        tags = tags.get_map(entry_id=entry.id)

        if entry.source_id:
            entry_source = connection.sources_table.get(id=entry.source_id)

            json_entry_data = entry_to_json(entry,
                                            with_id=True,
                                            source=entry_source,
                                            social_data=social_data_object,
                                            tags=tags)
        else:
            json_entry_data = entry_to_json(entry,
                                            with_id=True,
                                            source=None,
                                            social_data=social_data_object,
                                            tags=tags)

        return jsonify(json_entry_data)
    else:
        print("Cannot find entry")
        return jsonify({})


@app.route("/api/entry-visit")
def api_entry_visit():
    connection = DbConnection(app.config["DB_FILE"])

    entry_id = request.args.get("id")
    entries = Entries(connection)
    entry = entries.get(id=entry_id)

    if entry:
        json_data = {}
        json_data["page_rating_visits"] = entry.page_rating_visits + 1

        connection = DbConnection(app.config["DB_FILE"])
        connection.entries_table.update_json_data(entry.id, json_data)

        props = {}
        props["status"] = True
        return jsonify(props)
    else:
        props = {}
        props["status"] = False
        print(f"Cannot find entry with ID:{entry_id}")
        return jsonify(props)


@app.route("/api/dynamic")
def api_dynamic():
    connection = DbConnection(app.config["DB_FILE"])
    link = request.args.get("link")

    handler = UrlHandler(connection=connection, link=link)
    url = handler.get_link_url()
    url.get_response()

    props = url.get_all_properties()

    return jsonify(props)


@app.route("/api/stats")
def api_stats():
    connection = DbConnection(app.config["DB_FILE"])

    stats_map = get_stats_map(connection)

    return jsonify(stats_map)


@app.route("/api/status")
def api_status():
    connection = DbConnection(app.config["DB_FILE"])

    system = System.get_object()
    indicators = system.get_indicators()

    return jsonify({"indicators": indicators})


@app.route("/api/sources")
def api_sources():
    connection = DbConnection(app.config["DB_FILE"])

    pagination = PagePagination(request)
    limit = pagination.get_limit()
    offset = pagination.get_offset()

    json_sources = []
    sources = get_sources_for_request(connection, limit, offset)

    for source in sources:
        json_data_source = source_to_json(source, with_id=True)
        json_sources.append(json_data_source)

    json_data = {}
    json_data["sources"] = json_sources

    return jsonify(json_data)


def print_file(afile):
    path = Path(afile)
    text = path.read_text()
    lines = text.split("\n")
    lines=set(lines)
    return lines


def parse_args():
    parser = argparse.ArgumentParser(description="Run Flask server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host address to bind the server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind the server (default: 5000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run Flask in debug mode"
    )
    return parser.parse_args()


if __name__ == "__main__":
    debug_mode = False

    args = parse_args()
    debug_mode = args.debug

    if (debug_mode and os.environ.get("WERKZEUG_RUN_MAIN") == "true") or not debug_mode:
        thread = threading.Thread(
            target=runner.start,
            args=(),
            daemon=True
        )

        thread.start()

    host = args.host
    port = args.port

    if "YAFR_HOST" in os.environ:
        host = os.environ["YAFR_HOST"]
    if "YAFR_PORT" in os.environ:
        port = os.environ["YAFR_PORT"]

    app.run(host=host, port=port, debug=False)
