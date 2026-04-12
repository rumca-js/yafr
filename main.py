"""
Simple RSS reader
"""
import os
import sys
import threading
import argparse
import shutil
from pathlib import Path
from sqlalchemy import select, or_
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
   Entries,
   CheckLater,
   EntryRules,
   SocialData,
   Sources,
   AppLogging,
   EntryVotes,
   EntryTags,
   entry_to_json,
   source_to_json,
   source_and_entries_to_rss,
)
from linkarchivetools.utils.reflected import ReflectedTable

from urllib.parse import unquote

from templates.templates import *
from src.taskrunner import TaskRunner
from src.controller import Controller
from src.system import System


__version__ = "0.0.0"
path = Path("pyproject.toml")
text = path.read_text()
for line in text.split("\n"):
    wh = line.find("version")
    if wh >= 0:
        __version__ = line[11:-1]


page_size = 100

table_name = Path("data") / "table.db"
input_name = Path("data") / "input.db"

if not table_name.exists():
    print("Created db from scratch")
    shutil.copyfile(input_name, table_name)


runner = TaskRunner(table_name)
app = Flask(__name__)


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
        "title": table.c.title,
        "description": table.c.description,
        "link": table.c.link,
        "source_url": table.c.source_url,
        "source_id": table.c.source_id,
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


def get_entries_for_request(connection, order, limit, offset, search=None):
    table = connection.entries_table.get_table()
    tags_table = connection.entrycompactedtags.get_table()
    social_table = connection.socialdata.get_table()

    conditions = parse_search(search, table, tags_table)

    order_bys = [table.c.date_published.desc()]
    if order == "-view_count":
        order_bys = [social_table.c.view_count.desc()]
    elif order == "view_count":
        order_bys = [social_table.c.view_count.asc()]
    elif order == "-stars":
        order_bys = [social_table.c.stars.desc()]
    elif order == "stars":
        order_bys = [social_table.c.stars.asc()]
    elif order == "-followers_count":
        order_bys = [social_table.c.followers_count.desc()]
    elif order == "followers_count":
        order_bys = [social_table.c.followers_count.asc()]
    elif order == "-date_published":
        order_bys = [table.c.date_published.desc()]
    elif order == "date_published":
        order_bys = [table.c.date_published.asc()]
    elif order == "-date_created":
        order_bys = [table.c.date_created.desc()]
    elif order == "date_created":
        order_bys = [table.c.date_created.asc()]
    elif order == "-link":
        order_bys = [table.c.link.desc()]
    elif order == "link":
        order_bys = [table.c.link.asc()]
    elif order == "-page_rating_votes":
        order_bys = [table.c.page_rating_votes.desc()]
    elif order == "page_rating_votes":
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
        entries_select = entries_select.where(or_(*conditions))
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
def index():
    connection = DbConnection(table_name)
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
    connection = DbConnection(table_name)
    config = connection.configurationentry.get_first()

    default_values = {}
    default_values["view_display_type"] = config.display_type

    return render_template_string(PROJECT_TEMPLATE, title="Yafr search", default_values=default_values)


@app.route("/sources")
def sources():
    connection = DbConnection(table_name)

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


@app.route("/source/<int:source_id>", methods=["GET", "POST"])
def source(source_id):
    connection = DbConnection(table_name)

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
        return render_template_string(html_text)

    if source_item:
        html_text = get_view(SOURCE_TEMPLATE, title=source_item.title)

        return render_template_string(html_text, source_item=source_item, source_op_data = source_op)
    else:
        html_text = get_view(NOK_TEMPLATE, title="Cannot find source")
        return render_template_string(html_text)


@app.route("/add-sources", methods=["GET", "POST"])
def add_sources():
    connection = DbConnection(table_name)

    if request.method == "POST":
        raw_text = request.form.get("sources", "")

        controller = Controller(connection)
        controller.add_sources_text(raw_text)

        template_html = STR_TEMPLATE.replace("{template_string}", "Wait until sources are added")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)

    html_text = get_view(ADD_SOURCES_TEMPLATE, title="Add sources")
    return render_template_string(html_text, raw_data="")


@app.route("/add-links", methods=["GET", "POST"])
def add_links():
    connection = DbConnection(table_name)

    if request.method == "POST":
        raw_text = request.form.get("sources", "")

        controller = Controller(connection)
        controller.add_links_text(raw_text)

        template_html = STR_TEMPLATE.replace("{template_string}", "Wait until links are added")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)

    html_text = get_view(ADD_LINKS_TEMPLATE, title="Add links")
    return render_template_string(html_text, raw_data="")


@app.route("/entry", methods=["GET"])
def entry():
    connection = DbConnection(table_name)

    entry_id = request.args.get("id")
    entries = Entries(connection=connection)
    entry = entries.get(id=entry_id)

    html_text = get_view(ENTRY_TEMPLATE, title="Entry")
    return render_template_string(html_text, entry=entry)


@app.route("/check-later-list", methods=["GET"])
def check_later_list():
    connection = DbConnection(table_name)

    check_controller = CheckLater(connection=connection)
    entries = check_controller.get_entries()

    html_text = get_view(ENTRIES_LIST_TEMPLATE, title="Check later list")
    return render_template_string(html_text, entries=entries)


@app.route("/entry-check-later", methods=["GET"])
def check_later():
    connection = DbConnection(table_name)

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
    connection = DbConnection(table_name)

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
    connection = DbConnection(table_name)

    entry_id = request.args.get("id")

    if request.method == "POST":
        title = request.form.get("title", "")

        entries = Entries(connection)
        entry = entries.get(id=entry_id)

        json = entry_to_json(entry)
        json["title"] = title

        entries.update_json_data(id=entry_id, json_data=json)

        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)

    html_text = get_view(ENTRY_EDIT_TEMPLATE, title="Edit entry")
    return render_template_string(html_text, entry_id=entry_id)


@app.route("/entry-update", methods=["GET", "POST"])
def entry_update():
    connection = DbConnection(table_name)

    entry_id = request.args.get("id")

    if entry_id:
        BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_UPDATE_DATA, subject=str(entry_id))

        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)

    else:
        template_html = STR_TEMPLATE.replace("{template_string}", "NOK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)


@app.route("/entry-reset", methods=["GET", "POST"])
def entry_reset():
    connection = DbConnection(table_name)

    entry_id = request.args.get("id")

    if entry_id:
        BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_RESET_DATA, subject=str(entry_id))

        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)

    else:
        template_html = STR_TEMPLATE.replace("{template_string}", "NOK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)


@app.route("/entry-vote", methods=["GET", "POST"])
def entry_vote():
    connection = DbConnection(table_name)

    entry_id = request.args.get("id")
    current_vote = 0
    votes = EntryVotes(connection=connection)

    if request.method == "POST":
        entry_vote = request.form.get("entry-vote", "")

        votes.set(entry_id=entry_id, vote=entry_vote)

        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)
    else:
        current_vote = votes.get(entry_id=entry_id)

    html_text = get_view(ENTRY_VOTE_TEMPLATE, title="Vote entry")
    return render_template_string(html_text, entry_id=entry_id, current_vote=current_vote)


@app.route("/entry-tag", methods=["GET", "POST"])
def entry_tag():
    connection = DbConnection(table_name)
    table = ReflectedTable(connection.engine, connection.connection)
    table.vacuum()

    entry_id = request.args.get("id")
    tags = EntryTags(connection=connection)

    if request.method == "POST":
        entry_tags = request.form.get("entry-tag", "")

        tags.set(entry_id=entry_id, tags=entry_tags)

        template_html = STR_TEMPLATE.replace("{template_string}", "OK")
        html_text = get_view(template_html, title="OK")
        return render_template_string(html_text)
    else:
        current_tags = tags.get(entry_id=entry_id)

    html_text = get_view(ENTRY_TAG_TEMPLATE, title="Tag entry")
    return render_template_string(html_text, entry_id=entry_id, current_tags=current_tags)


@app.route("/rss/<int:source_id>", methods=["GET", "POST"])
def rss(source_id):
    connection = DbConnection(table_name)

    source = connection.sources_table.get(id=source_id)
    entries = connection.entries_table.get_where({"source_id":source_id})

    entry_list = []
    for entry in entries:
        entry_json = entry_to_json(entry)
        entry_list.append(entry_json)

    source_json = source_to_json(source)

    rss_text = source_and_entries_to_rss(source_json, entry_list)
    return Response(rss_text, mimetype="application/rss+xml")


@app.route("/block-rules", methods=["GET", "POST"])
def block_rules():
    html_text = get_view(BLOCK_RULES_TEMPLATE, title="Block rules")
    return render_template_string(html_text)


@app.route("/block-url", methods=["GET", "POST"])
def block_url():
    connection = DbConnection(table_name)
    controller = Controller(connection)

    rules = EntryRules(connection = connection)

    if request.method == "POST":
        raw_text = request.form.get("sources", "")
        rules.add_entry_rules(raw_text)
        return redirect(url_for("index"))

    sources = []
    html_text = get_view(DEFINE_ENTRY_RULES_TEMPLATE, title="Set Block Rules")

    raw_data = ""

    return render_template_string(html_text, raw_data=raw_data)


@app.route("/define-block-rules", methods=["GET", "POST"])
def define_block_rules():
    connection = DbConnection(table_name)
    controller = Controller(connection)

    rules = EntryRules(connection = connection)

    if request.method == "POST":
        raw_text = request.form.get("sources", "")
        rules.set_entry_rules(raw_text)
        return redirect(url_for("index"))

    sources = []
    html_text = get_view(DEFINE_ENTRY_RULES_TEMPLATE, title="Set Block Rules")

    urls = rules.get_rule_urls()
    raw_data = "\n".join(urls)

    return render_template_string(html_text, raw_data=raw_data)


@app.route("/remove-all-entries")
def remove_all_entries():
    connection = DbConnection(table_name)

    connection.entries_table.truncate()
    connection.socialdata.truncate()

    html_text = get_view(OK_TEMPLATE, title="Remove all entries")
    return render_template_string(html_text)


@app.route("/remove-all-logs")
def remove_all_logs():
    connection = DbConnection(table_name)

    connection.applogging.truncate()

    html_text = get_view(OK_TEMPLATE, title="Remove all logs")
    return render_template_string(html_text)


@app.route("/remove-all-jobs")
def remove_all_jobs():
    connection = DbConnection(table_name)

    connection.backgroundjob.truncate()

    html_text = get_view(OK_TEMPLATE, title="Remove all jobs")
    return render_template_string(html_text)


@app.route("/remove-all-sources")
def remove_all_sources():
    connection = DbConnection(table_name)

    connection.sources_table.truncate()
    connection.sourceoperationaldata.truncate()

    html_text = get_view(OK_TEMPLATE, title="Remove all sources")
    return render_template_string(html_text)


@app.route("/remove-source")
def remove_source():
    connection = DbConnection(table_name)

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
    connection = DbConnection(table_name)

    entry_id = request.args.get("id")

    entry = connection.entries_table.get(id=entry_id)
    if source:
        connection.entries_table.delete_where({"id" : entry.id})

    html_text = get_view(OK_TEMPLATE, title="Remove entry")
    return render_template_string(html_text)


@app.route("/logs", methods=["GET", "POST"])
def logs():
    connection = DbConnection(table_name)

    html_text = get_view(LOGS_TEMPLATE, title="Logs")

    order_by = [
            connection.applogging.get_table().c.date.desc()
            ]

    logs = list(connection.applogging.get_where(order_by=order_by))
    len_logs = len(logs)

    return render_template_string(html_text, logs=logs, len_logs=len_logs)


@app.route("/jobs", methods=["GET", "POST"])
def jobs():
    connection = DbConnection(table_name)

    html_text = get_view(JOBS_TEMPLATE, title="Jobs")

    order_by = [
            connection.backgroundjob.get_table().c.date_created.desc()
            ]

    jobs = list(connection.backgroundjob.get_where(order_by=order_by))
    len_jobs = len(jobs)

    return render_template_string(html_text, jobs=jobs, len_jobs=len_jobs)


@app.route("/status")
def status():
    connection = DbConnection(table_name)

    system = System.get_object()

    stats_map = {}

    stats_map["Entries"] = connection.entries_table.count()
    stats_map["Sources"] = connection.sources_table.count()
    stats_map["Sources Operational Data"] = connection.sourceoperationaldata.count()
    stats_map["Entry rules"] = connection.entry_rules.count()
    stats_map["Social data"] = connection.socialdata.count()
    stats_map["AppLogging"] = connection.applogging.count()
    stats_map["ConfigurationEntry"] = connection.configurationentry.count()
    stats_map["BackgroundJobs"] = connection.backgroundjob.count()

    stats_map["System state"] = system.is_system_ok()

    html_text = get_view(STATS_TEMPLATE, title="Stats")
    return render_template_string(html_text, stats=stats_map)


@app.route("/admin")
def admin():
    connection = DbConnection(table_name)

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


@app.route("/configuration", methods=["GET", "POST"])
def configuration():
    connection = DbConnection(table_name)

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
        number_of_update_entries = request.form.get("number_of_update_entries", "")

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
        data["number_of_update_entries"] = number_of_update_entries

        connection.configurationentry.update_json_data(id=config.id, json_data=data)

        html_text = get_view(OK_TEMPLATE, title="Changes applied")
        return render_template_string(html_text)

    instance_fields = {}
    instance_fields["instance_title"] = config.instance_title
    instance_fields["instance_description"] = config.instance_description
    instance_fields["display_type"] = config.display_type
    instance_fields["remote_webtools_server_location"] = config.remote_webtools_server_location
    instance_fields["enable_social_data"] = config.enable_social_data
    instance_fields["new_entries_fetch_social_data"] = config.new_entries_fetch_social_data
    instance_fields["entry_update_fetches_social_data"] = config.entry_update_fetches_social_data
    instance_fields["number_of_update_entries"] = config.number_of_update_entries

    html_text = get_view(CONFIGURATION_TEMPLATE, title="Configuration")
    return render_template_string(html_text, configuration=instance_fields)


#### JSON

@app.route("/api/entries")
def api_entries():
    connection = DbConnection(table_name)

    pagination = PagePagination(request)
    limit = pagination.get_limit()
    offset = pagination.get_offset()

    search = request.args.get("search")
    order_by = request.args.get("order_by")

    json_entries = []
    entries = get_entries_for_request(connection, order_by, limit, offset, search)

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


@app.route("/api/stats")
def api_stats():
    connection = DbConnection(table_name)

    entries_len = connection.entries_table.count()
    sources_len = connection.sources_table.count()
    entry_rules_len = connection.entry_rules.count()

    system = System.get_object()

    stats_map = {}
    stats_map["entries_len"] = entries_len
    stats_map["sources_len"] = sources_len
    stats_map["system_state"] = system.is_system_ok()

    return jsonify(stats_map)


@app.route("/api/sources")
def api_sources():
    connection = DbConnection(table_name)

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
