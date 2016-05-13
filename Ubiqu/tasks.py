# coding=utf-8
from __future__ import absolute_import
__author__ = 'wintere'


import os
import codecs
from datetime import datetime
from time import time
import json
import socket
import zipfile
import inspect
from werkzeug.datastructures import ImmutableDict
from werkzeug.utils import secure_filename
from collections import defaultdict
from celery.signals import after_task_publish

import operator
import unicodecsv as csv
# Import Ity Modules

import sys
sys.path.append(os.path.join(
    os.path.dirname(os.path.basename(__file__)),
    ".."
))
sys.path.append(os.path.dirname(os.path.basename(__file__)))
from Ity import DATA_NAMES, DATA_EXTENSIONS
import ubiq_internal_tasks
from Ity.Tokenizers import RegexTokenizer
from Ity import dictionaries_root
# Import app configuration
from app_config import conf as app_config

# Import Celery Modules
from celery import Celery, current_task
from celery.utils.log import get_task_logger

# Instantiate Celery
celery_app = Celery(__name__)
celery_app.config_from_object("celery_config")
logger = get_task_logger(__name__)

# Have tasks indicate when they have been sent.
# From http://stackoverflow.com/a/10089358
from celery.signals import task_sent

# Mail imports
from email.mime.text import MIMEText
import smtplib

version = 1.1

# generic email form sent after jobs complete
def email_alert(email, failed=False, name=''):
    corpus_name = current_task.request.id
    if failed:
        subject_status = "failed"
        body = app_config.get("FAIL_TEMPLATE", None)
    else:
        subject_status = "succeeded"
        body = app_config.get("SUCCESS_TEMPLATE", None)
    mail_from_address = app_config.get("MAIL_FROM_ADDRESS", None)
    mail_server = app_config.get("MAIL_SERVER", None)
    mail_port = app_config.get("MAIL_PORT", None)
    mail_username = app_config.get("MAIL_USERNAME", None)
    mail_password = app_config.get("MAIL_PASSWORD", None)
    ubiquity_url = app_config.get("UBIQUITY_URL", None)
    if not all([
        body,
        mail_from_address,
        mail_server,
        mail_port,
        mail_username,
        mail_password,
        ubiquity_url
    ]):
        return
    # Send mail
    try:
        if name != '':
            status_link = '%s/tag_corpus/%s/%s' % (ubiquity_url, corpus_name, name[:-1])
        else:
            status_link = '%s/tag_corpus/%s/%s' % (ubiquity_url, corpus_name, '~')  #placeholder to retain url structure
        msg = MIMEText(body % (corpus_name, status_link))
        msg['Subject'] = 'Ubiqu+Ity job %s' % subject_status
        msg['To'] = email
        msg['From'] = mail_from_address
        s = smtplib.SMTP(mail_server, mail_port)
        s.starttls()
        s.login(mail_username, mail_password)
        s.sendmail(mail_username, email, msg.as_string())
    # TODO: Handle failure
    except smtplib.SMTPException:
        pass

# failure email sent if the task fails
def email_failure(task):
    def on_failure(exc, task_id, args, kwargs, einfo):
        try:
            email = kwargs.pop('email')
            if email is not None:
                email_alert(email, failed=True,name='~')
        except KeyError:
            pass

    task.on_failure = on_failure
    return task

@after_task_publish.connect
def update_sent_state(sender=None, body=None, **kwargs):
    # the task may not exist if sent using `send_task` which
    # sends tasks by name, so fall back to the default result backend
    # if that is the case.
    task = celery_app.tasks.get(sender)
    backend = task.backend if task else celery_app.backend
    backend.store_result(body['id'], None, "SENT")

# Sentry Integration
if "SENTRY_DSN" in celery_app.conf:
    from raven import Client
    from raven.contrib.celery import register_signal
    client = Client(
        dsn=celery_app.conf["SENTRY_DSN"]
    )
    register_signal(client)


default_tag_corpus_options = {
    "filename_match": "*.txt",
    "taggers": {
        "DocuscopeTagger": None  # ,
        # "SimpleRuleTagger": {
        #     "rules_path":
    },
}

def _tag_text_options_valid(options):
    return (
        "text_path" in options and
        options["text_path"] is not None and
        "model_path" in options and
        options["model_path"] is not None and
        "taggers" in options and
        type(options["taggers"]) is dict
    )

# unzips archives passed in as input to the web version
def _expand_zip_archive(zip_archive_path, delete_zip_archive=True):
    """
    Returns a list of file paths written to disk, as extracted from the specified ZIP archive.
    Removes the ZIP archive by default.
    :param zip_archive_path:
    :param delete_zip_archive:
    :return:
    """
    # http://stackoverflow.com/a/7806727
    written_files = []
    zfile = zipfile.ZipFile(zip_archive_path)
    for name in zfile.namelist():
        (dirname, filename) = os.path.split(name)
        # Skip blank filenames and MacOSX metadata files
        if filename == "" or dirname.startswith('__MACOSX'):
            continue
        # Reassign dirname to place the contents of the ZIP archive in the folder containing the archive.
        zip_archive_containing_folder = os.path.dirname(zip_archive_path)
        # Figure out the full file path of where this file is going.
        file_containing_folder = os.path.join(
            zip_archive_containing_folder,
            dirname
        )
        file_path = os.path.join(
            file_containing_folder,
            filename
        )
        if not os.path.exists(file_containing_folder):
            os.mkdir(file_containing_folder)
        # Do not overwrite existing files.
        if not os.path.exists(file_path):
            fd = open(file_path, "w")
            fd.write(zfile.read(name))
            fd.close()
            written_files.append(file_path)
    #if delete_zip_archive:
    #   os.remove(zip_archive_path)
    return written_files

#saves corpus for web version of Ubiq+Ity
@celery_app.task
def save_corpus(corpus_name, data_uploads):
    corpus_date = datetime.now().strftime("%Y-%m-%d-%X").replace(":", "-")
    corpus_path = os.path.join(celery_app.conf["OUTPUT_ROOT"], corpus_date)
    corpus_info = {
        "name": corpus_name,
        "provenance": "ubiquity-%s" % corpus_date,
        "path": corpus_path,
        # Always output in the TMP_ROOT, where we **know** we have write access.
        "output_path": os.path.join(corpus_path, "Output"),
        "data": {}
    }
    corpus_data_files = {}
    # Only deal with the data uploads we expect to have.
    for data_name in DATA_NAMES:
        if data_name in corpus_info["data"]:
            raise ValueError("Attempting to upload data of the same type twice.")
        data_files = data_uploads.getlist(data_name)
        # Skip this data type if there are no uploads for it.
        if len(data_files) == 0:
            continue
        info = {
            "name": data_name,
            "path": os.path.join(corpus_path, "Data", data_name)
        }
        saved_files = {
            "saved":   [],
            "skipped": []
        }
        # Save the uploaded metadata files.
        if not os.path.exists(info["path"]):
            os.makedirs(info["path"])
        # Go through all the uploaded data files.
        for the_file in data_files:
            new_filename = secure_filename(the_file.filename)
            new_filename_ext = os.path.splitext(new_filename)[1]
            new_file_path = os.path.join(
                info["path"],
                new_filename
            )
            # Is this file of the right type?
            if new_filename_ext in DATA_EXTENSIONS[data_name]:
                the_file.save(new_file_path)
                # Special case for CorpusText ZIP archives: we want to extract them.
                # By default, _unzip_archive() deletes the ZIP archive after extraction!
                if data_name == "Text" and new_filename_ext == ".zip":
                    # Add the paths of the files extracted from the ZIP archive.
                    saved_files["saved"].extend(
                        _expand_zip_archive(zip_archive_path=new_file_path)
                    )
                else:
                    # Add the path of this saved file.
                    saved_files["saved"].append(new_file_path)
            else:
                saved_files["skipped"].append(the_file.filename)
        corpus_info["data"][data_name] = info
        corpus_data_files[data_name] = saved_files
    return corpus_info, corpus_data_files



@email_failure
@celery_app.task
#skeleton method accessed by web version of Ubiq+Ity
def tag_corpus(
        corpus_info,
        corpus_data_files,
        email,
        tags=ImmutableDict(Docuscope={"return_included_tags": True, "return_excluded_tags": False}),
        formats=ImmutableDict(HTML=None),
        batch_formats=ImmutableDict(CSV=None),
        create_zip_archive=False,
        ngram_count=0,
        ngram_pun=False,
        ngram_per_doc=False,
        generate_text_htmls=True,
        chunk_text=False,
        chunk_length=None,
        chunk_offset=None,
        blacklist_path=None,
        blacklist_words='',
        rule_csv=False,
        doc_rule=False,
        defect_count=False,
        name='',
        token_csv=False
):
    csv_path = ubiq_internal_tasks.tag_corpus(corpus_info,
        corpus_data_files,
        email,
        tags=tags,
        formats=formats,
        batch_formats=batch_formats,
        create_zip_archive=create_zip_archive,
        ngram_count=ngram_count,
        ngram_pun=ngram_pun,
        ngram_per_doc=ngram_per_doc,
        generate_text_htmls=generate_text_htmls,
        chunk_text=chunk_text,
        chunk_length=chunk_length,
        chunk_offset=chunk_offset,
        blacklist_path=blacklist_path,
        blacklist_words=blacklist_words,
        rule_csv=rule_csv,
        doc_rule=doc_rule,
        defect_count=defect_count,
        name=name,
        token_csv=token_csv,
        app_mode=True,
        current_task = current_task,
        logger = logger)
    zip_archive_path = None
    if create_zip_archive:
        zip_archive_path = archive_corpus_output(
            corpus_info=corpus_info,name=name
        )
    # Update progress. (Web version)
    if current_task.request.id is not None:
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100.0, 'total': 100.0}
        )
    # Email if successful. (Web version)
    if email is not None:
        email_alert(email, failed=False, name=name)

    return corpus_info["name"], csv_path, zip_archive_path


@celery_app.task
#zips up job once it is completed, for use with web client
def archive_corpus_output(corpus_info, name=''):
    zip_archive_root = os.path.join(
        corpus_info["output_path"],
        "..",
        "Archives"
    )
    if not os.path.exists(zip_archive_root):
        os.makedirs(zip_archive_root)
    zip_archive_filename = "".join([name,
                                    corpus_info["provenance"],
                                    ".zip"
                                    ])
    zip_archive_path = os.path.join(
        zip_archive_root,
        zip_archive_filename
    )
    if os.path.exists(zip_archive_path):
        raise IOError("ZIP archive '%s' already exists!" % zip_archive_path)
    zip_archive_file = zipfile.ZipFile(zip_archive_path, "w", zipfile.ZIP_DEFLATED)
    archive_target_path = os.path.join(
        corpus_info["output_path"],
        corpus_info["provenance"]
    )
    for root, dirs, files in os.walk(archive_target_path):
        for the_file in files:
            relative_root_path = root.replace(corpus_info["output_path"], "")
            zip_archive_file.write(
                filename=os.path.join(root, the_file),
                arcname=os.path.join(relative_root_path,the_file)
            )
    zip_archive_file.close()
    return zip_archive_path



if __name__ == "__main__":
    celery_app.start()

