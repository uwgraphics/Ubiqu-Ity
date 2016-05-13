# coding=utf-8
from __future__ import absolute_import

import os
import sys
sys.path.append(os.path.join(
    os.path.dirname(os.path.basename(__file__)),
    ".."
))
sys.path.append(os.path.dirname(os.path.basename(__file__)))

from flask import Flask, url_for, render_template, redirect, request, jsonify, send_file
from Support.flask_util_js.flask_util_js import FlaskUtilJs
import hashlib
import json
import time
import tasks
from werkzeug.datastructures import ImmutableDict

from raven.contrib.flask import Sentry

#########################
#### Flask App Setup ####
#########################

app = Flask(__name__)
# Add the SENTRY_DSN value from Celery config into this Flask app's config.
if "SENTRY_DSN" in tasks.celery_app.conf:
    app.config["SENTRY_DSN"] = tasks.celery_app.conf["SENTRY_DSN"]

# Load the configuration object.
app.config.from_object("Ubiqu.flask_config")
# app.config.from_pyfile(__name__ + '.cfg', silent=True)

# Determine if we should execute Celery tasks asynchronously (or not) by trying to connect to the Celery worker server.
# app.config["ASYNC"] = len(tasks.celery_app.control.ping(timeout=0.15)) > 0
# Update the Celery instance's configuration.
# tasks.celery_app.conf["ASYNC"] = app.config["ASYNC"]

# Load some sweet Jinja2 extensions
app.jinja_options = dict(
    extensions=[
        'jinja2.ext.do',
        'jinja2.ext.autoescape'
    ]
)

# For flask_util.url_for() in JavaScript: https://github.com/dantezhu/flask_util_js
fujs = FlaskUtilJs(app)

# Sentry with the Ubiqu+Ity URI
sentry = Sentry(app)


################
#### Routes ####
################


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/tag_corpus/", methods=["GET"])
def tag_corpus_no_tid():
    return redirect(url_for("index"))


@app.route("/upload", methods=["POST"])
def upload():
    """
    If there's some problem with the upload, we return early with the JSON status output.
    If the upload concludes successfully, we write the status information to disk and return a redirect to the upload_get route.
    :return:
    """
    # No Celery? Uh, we're not ready for that yet.
    if not app.config["CELERY"]:
        raise NotImplementedError("Right now we need Celery to even function!")
    # Make a unique corpus name for this upload.
    upload_hash = hashlib.sha1()
    upload_hash.update(str(time.time()))
    arbitrary_corpus_name = upload_hash.hexdigest()[:10]
    # Save the corpus synchronously.
    # This is *not* a Celery task call; we want to avoid transferring all the
    # upload data across the network to the Celery worker server.
    corpus_info, corpus_data_files = tasks.save_corpus(
        corpus_name=arbitrary_corpus_name,
        data_uploads=request.files
    )
    if "email_address" not in request.form:
        raise ValueError("No email address provided!")
    email_address = request.form["email_address"]
    docuscope_dictionary = request.form["docuscope_dictionary"]
    if "generate_ngram_csv" in request.form:
        ngram_count = int(request.form["ngram_count"])
        ngram_punc = "ngram_pun" in request.form
    else:
        ngram_count=0
        ngram_punc=False
    generate_text_htmls = "generate_text_htmls" in request.form
    chunk_text = "chunk_text" in request.form
    if "chunk_text" in request.form:
        if "chunk_length" in request.form and request.form["chunk_length"] != '':
            chunk_length = request.form["chunk_length"]
        else:
            chunk_length = None
        if "chunk_offset" in request.form and request.form["chunk_offset"] != '':
            chunk_offset = request.form["chunk_offset"]
        else:
            chunk_offset = None
    # wipes values if chunk parameters were entered but then chunk_text was unchecked
    else:
        chunk_length = None
        chunk_offset = None
    name = str(request.form["custom"])
    # get blacklisted words as string, if any
    blacklist_words = ''
    if "enable_blacklist" in request.form:
        if "blacklist_words" in request.form:
            blacklist_words = request.form["blacklist_words"]

    rule_csv = ("generate_rule" in request.form)
    defect_count = ("defect_stats" in request.form)
    token_csv = ("token_csv" in request.form)
    doc_rule = False
    if rule_csv:
        doc_rule = ("doc_rule" in request.form)
    # If we're running with Celery, make an asynchronous call to the task.
    # Then redirect to tag_corpus_status with the tid=[the Celery task ID].
    if app.config["CELERY"]:
        # Hand the uploaded data off to a Celery task.
        result = tasks.tag_corpus.delay(
            corpus_info=corpus_info,
            corpus_data_files=corpus_data_files,
            email=email_address,
            create_zip_archive=True,
            tags=ImmutableDict(Docuscope={"return_included_tags": True, "return_excluded_tags": False, "dictionary_path":docuscope_dictionary}),
            ngram_count=ngram_count,
            ngram_pun=ngram_punc,
            generate_text_htmls=generate_text_htmls,
            chunk_text=chunk_text,
            chunk_length=chunk_length,
            chunk_offset=chunk_offset,
            blacklist_words=blacklist_words,
            rule_csv=rule_csv,
            doc_rule=doc_rule,
            name=name,
            defect_count=defect_count,
            token_csv=token_csv
        )
        if name == '':
            name = '~' #placeholder to keep url structure
        # The jQuery AJAX form plugin expects a JSON return value rather than a redirect.
        if "javascript_enabled" in request.form and request.form["javascript_enabled"] == "true":
            return jsonify(dict(redirect=url_for(
                "tag_corpus_index",
                tid=result.id,
                name=name
            )))
        else:
            return redirect(url_for(
                "tag_corpus_index",
                tid=result.id,
                name=name
            ))
    # No Celery? Uh, we're not ready for that yet.
    else:
        raise NotImplementedError("Right now we need Celery to even function!")


@app.route("/tag_corpus/<tid>/<name>", methods=["GET"])
def tag_corpus_index(tid, name):
    message = json.loads(tag_corpus_status(tid, name).data)
    return render_template(
        "tag_corpus_index.html",
        message=message,
        tid=tid,
        refresh=15,
        name=name
    )


@app.route("/tag_corpus/<tid>/<name>/status", methods=["GET"])
def tag_corpus_status(tid, name):
    # No Celery? Uh, we're not ready for that yet.
    if not app.config["CELERY"]:
        raise NotImplementedError("Right now we need Celery to even function!")
    # Get the AsyncResult object for this task and check its state.
    result = tasks.tag_corpus.AsyncResult(tid)
    message = dict(
        state=result.state,
        name=name
    )
    # Send the progress status if we are in that state.
    if not result.ready() and result.state == "PROGRESS":
        if type(result.info) is dict:
            message.update(result.info)
        return jsonify(message)
    # Success? Send along the download URIs.
    elif result.successful():
        message.update(
            csv=url_for("tag_corpus_format", tid=tid, name=name, fmt="csv"),
            zip=url_for("tag_corpus_format", tid=tid, name=name, fmt="zip"),
        )
    return jsonify(message)


@app.route("/tag_corpus/<tid>/<name>/<fmt>")
def tag_corpus_format(tid, name, fmt):
    result = tasks.tag_corpus.AsyncResult(tid)
    if not result.ready() or not result.successful():
        return redirect(
            url_for("tag_corpus_status", tid=tid, name=name)
        )
    else:
        return_value = result.get()
        file_path = None
        if fmt == "csv":
            file_path = return_value[1]
        elif fmt == "zip":
            file_path = return_value[2]
        if file_path is None:
            return "Format '%s' not found." % fmt, 404
        else:
            return send_file(
                file_path,
                as_attachment=True,
                attachment_filename=os.path.basename(file_path)
            )


if __name__ == "__main__":
    port = 5001
    app.run(host='0.0.0.0', port=port, debug=True)
