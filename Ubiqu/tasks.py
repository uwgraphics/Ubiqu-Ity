# coding=utf-8
from __future__ import absolute_import


__author__ = 'kohlmannj'


import os
import codecs
from datetime import datetime
from time import time
import json
import socket
import zipfile
from werkzeug.datastructures import ImmutableDict
from werkzeug.utils import secure_filename

# Import Ity Modules
import sys
sys.path.append(os.path.join(
    os.path.dirname(os.path.basename(__file__)),
    ".."
))
sys.path.append(os.path.dirname(os.path.basename(__file__)))
from Ity import DATA_NAMES, DATA_EXTENSIONS
from Ity.Tokenizers import RegexTokenizer

# Import app configuration
from app_config import conf as app_config

# Import Celery Modules
from celery import Celery, current_task
from celery.utils.log import get_task_logger

# Instantiate Celery
celery = Celery(__name__)
celery.config_from_object("celery_config")
logger = get_task_logger(__name__)

# Have tasks indicate when they have been sent.
# From http://stackoverflow.com/a/10089358
from celery.signals import task_sent

# Mail imports
from email.mime.text import MIMEText
import smtplib


def email_alert(email, failed=False):
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
        status_link = '%s/tag_corpus/%s' % (ubiquity_url, corpus_name)
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


def email_failure(task):
    def on_failure(exc, task_id, args, kwargs, einfo):
        try:
            email = kwargs.pop('email')
            if email is not None:
                email_alert(email, failed=True)
        except KeyError:
            pass

    task.on_failure = on_failure
    return task


def update_sent_state(sender=None, id=None, **kwargs):
    # the task may not exist if sent using `send_task` which
    # sends tasks by name, so fall back to the default result backend
    # if that is the case.
    task = celery.tasks.get(sender)
    backend = task.backend if task else celery.backend
    backend.store_result(id, None, "SENT")
task_sent.connect(update_sent_state)


# Sentry Integration
if "SENTRY_DSN" in celery.conf:
    from raven import Client
    from raven.contrib.celery import register_signal
    client = Client(
        dsn=celery.conf["SENTRY_DSN"]
    )
    register_signal(client)


default_tag_corpus_options = {
    "filename_match": "*.txt",
    "taggers": {
        "DocuscopeTagger": None  # ,
        # "SimpleRuleTagger": {
        #     "rules_path":
    },
    "write_to_disk": True
}


# Custom header titles for the CSV output.
# CHANGED
custom_header_key_titles = {
    "Docuscope.!UNTAGGED": "<# Docuscope Untagged Tokens>",
    "Docuscope.!NORULE": "<# Docuscope No-Rules Tokens>",
    "Docuscope.!EXCLUDED": "<# Docuscope Excluded Tokens>",
    "num_word_tokens": "<# Word Tokens>",
    "num_punctuation_tokens": "<# Punctuation Tokens>",
    "num_included_tokens": "<# Included Tokens (Incl. by Tokenizer)>",
    "num_excluded_tokens": "<# Excluded Tokens (Excl. by Tokenizer)>",
    "num_tokens": "<# Tokens>",
    "num_tag_maps": "<# Tag Maps>"
}


def module_exists(module_name):
    """From http://stackoverflow.com/a/5847944"""
    try:
        __import__(module_name)
    except ImportError:
        return False
    else:
        return True


def _tag_corpus_options_valid(options):
    """
    A helper function to validate the contents of an options dict passed to
    tag_corpus().
    :param options: The dict of options to pass to tag_corpus().
    :return: True if the options dict is well-formed; False if not.
    """
    return (
        ("filename_match" in options and options["filename_match"] is not None) and
        ("taggers" in options and type(options["taggers"]) is dict) and
        "write_to_disk" in options
    )


def _tag_text_options_valid(options):
    return (
        "text_path" in options and
        options["text_path"] is not None and
        "model_path" in options and
        options["model_path"] is not None and
        "taggers" in options and
        type(options["taggers"]) is dict
    )


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
        # Skip blank filenames
        if filename == "":
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
    if delete_zip_archive:
        os.remove(zip_archive_path)
    return written_files


@celery.task
def save_corpus(corpus_name, data_uploads):
    corpus_date = datetime.now().strftime("%Y-%m-%d-%X").replace(":", "-")
    corpus_path = os.path.join(celery.conf["OUTPUT_ROOT"], corpus_date)
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
@celery.task
def tag_corpus(
    corpus_info,
    corpus_data_files,
    email,
    tags=ImmutableDict(Docuscope={"return_included_tags": True}),
    formats=ImmutableDict(HTML=None),
    batch_formats=ImmutableDict(CSV=None),
    write_to_disk=True,
    create_zip_archive=False
):
    # Validate corpus_info.
    if "path" not in corpus_info or "name" not in corpus_info or "data" not in corpus_info:
        raise ValueError("Invalid corpus_info provided.")

    # Add an id to the corpus_info dict.
    corpus_info["processing_id"] = "".join([
        corpus_info["name"],
        "_",
        "-".join(tags.keys()),
        "_",
        "-".join(formats.keys()),
        "_",
        socket.gethostname(),
        "_",
        str(int(time()))
    ])
    # Validate Taggers.
    tagger_instances = {}
    formatter_instances = {}
    if len(tags) > 1:
        raise ValueError("Tagging texts with multiple taggers isn't supported yet.")
    for tag_name in tags.keys():
        if not module_exists("Ity.Taggers." + tag_name + "Tagger"):
            raise ValueError("A Tagger module for '%s' tags does not exist." % tag_name)
    # Instantiate Taggers.
    for tag_name, tag_args in tags.items():
        if tag_name in tagger_instances:
            raise NotImplementedError("Tagging multiple times with the same tagger is not yet supported.")
        tagger_name = tag_name + "Tagger"
        tagger_module = getattr(__import__("Ity.Taggers", fromlist=tagger_name), tagger_name)
        # Add some additional instantiation arguments for specific taggers.
        # TODO: Clean up Taggers' init() arguments.
        if tag_args is None:
            tagger_init_args = {}
        else:
            tagger_init_args = tag_args
        # custom rules file
        if tag_name == "Docuscope" and (
            "SimpleRule" in corpus_data_files and
            "saved" in corpus_data_files["SimpleRule"] and
            len(corpus_data_files["SimpleRule"]["saved"]) > 0
        ):
            tagger_init_args.update(
                dictionary_path=corpus_data_files["SimpleRule"]["saved"][0]
            )
        # Instantiate this Tagger.
        tagger_instance = tagger_module(**tagger_init_args)
        tagger_instances[tag_name] = tagger_instance
    # Validate formatters.
    for format_name in formats.keys() + batch_formats.keys():
        if not module_exists("Ity.Formatters." + format_name + "Formatter"):
            raise ValueError("A Formatter module for '%s' format does not exist." % format_name)
    # Instantiate Formatters.
    for format_name, format_args in formats.items():
        if format_name in formatter_instances:
            raise NotImplementedError("Formatting multiple times with the same formatter is not yet supported.")
        formatter_name = format_name + "Formatter"
        formatter_module = getattr(__import__("Ity.Formatters", fromlist=formatter_name), formatter_name)
        # Add some additional instantiation arguments for specific formatters.
        # TODO: Clean up Taggers' init() arguments.
        if format_args is None:
            formatter_init_args = {}
        else:
            formatter_init_args = format_args
        # Instantiate this Formatter.
        formatter_instance = formatter_module(**formatter_init_args)
        formatter_instances[format_name] = formatter_instance

    # Get all the texts in this corpus...if there are any?
    if "Text" not in corpus_info["data"] or len(corpus_data_files["Text"]["saved"]) == 0:
        raise StandardError("No corpus texts to tag!")
    text_paths = corpus_data_files["Text"]["saved"]

    # Logging
    logger.info("Email: %s; Corpus: %s; # Texts: %u." % (
        email,
        corpus_info["name"],
        len(corpus_data_files["Text"]["saved"])
    ))

    # Update progress.
    if current_task.request.id is not None:
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0.0, 'total': 100.0, "model_path": corpus_info["name"]}
        )

    # Prepare the arguments for each tag_text() call.
    tag_text_args = [
        dict(
            text_path=text_path,
            corpus_info=corpus_info,
            corpus_data_files=corpus_data_files,
            taggers=tagger_instances,
            formatters=formatter_instances,
            write_to_disk=write_to_disk
        ) for text_path in text_paths
    ]
    # Synchonrously tag and format all the texts.
    tag_results = []
    for index, tag_text_arg in enumerate(tag_text_args):
        tag_results.append(
            _tag_text_with_existing_instances(**tag_text_arg)
        )
        # Update progress.
        if current_task.request.id is not None:
            current_task.update_state(
                state='PROGRESS',
                meta={'current': float(index + 1) / len(tag_text_args) * 100.0, 'total': 100.0}
            )
    csv_path = format_corpus(
        text_results=tag_results,
        corpus_info=corpus_info,
        write_to_disk=write_to_disk
    )
    zip_archive_path = None
    if create_zip_archive:
        zip_archive_path = archive_corpus_output(
            corpus_info=corpus_info
        )
    # Update progress.
    if current_task.request.id is not None:
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100.0, 'total': 100.0}
        )
    # Email if successful.
    if email is not None:
        email_alert(email, failed=False)
    return corpus_info["name"], csv_path, zip_archive_path


def _tag_text_with_existing_instances(text_path, corpus_info, corpus_data_files, taggers, formatters=None, write_to_disk=False):
    # Open the text file and get its contents.
    if not os.path.exists(text_path):
        raise ValueError("Text file '%s' does not exist." % text_path)
    text_name = os.path.basename(text_path)
    # Try to decode the file with multiple encodings
    text_file = None
    text_contents = None
    for encoding in ["UTF-8", "ISO-8859-1", "CP1252"]:
        try:
            text_file = codecs.open(text_path, encoding=encoding)
            text_contents = text_file.read()
            break
        except UnicodeDecodeError:
            pass
        finally:
            if text_file is not None:
                text_file.close()
    if text_contents is None:
        raise NotImplementedError("Could not find a valid encoding for input file %s" % text_path) 

    # Tokenize.
    tokenizer = RegexTokenizer()
    tokens = tokenizer.tokenize(text_contents)

    # Import and instantiate the taggers.
    tag_dicts = {}
    tag_maps = {}
    # TODO: Parallelize?
    for tag_name, tagger in taggers.items():
        if tag_name in tag_dicts or tag_name in tag_maps:
            raise NotImplementedError("Tagging multiple times with the same tagger is not yet supported.")
        # Tag with this tagger.
        single_tag_data, single_tag_maps = tagger.tag(tokens)
        tag_dicts[tag_name] = single_tag_data
        tag_maps[tag_name] = single_tag_maps

    # Return the text name, list of tag dicts, and some token counts.
    output_dict = dict(
        text_path=text_path,
        text_name=text_name,
        text_key=nameToKey(os.path.splitext(text_name)[0]),
        corpus_name=corpus_info["name"],
        text_contents=text_contents,
        # tokens=tokens,
        tag_dicts=tag_dicts,
        # tags=tags,
        num_tokens=len(tokens),
        num_word_tokens=len([
            token for token in tokens
            if token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["WORD"]
        ]),
        num_punctuation_tokens=len([
            token for token in tokens
            if token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["PUNCTUATION"]
        ]),
        num_included_tokens=len([
            token for token in tokens
            if token[RegexTokenizer.INDEXES["TYPE"]] not in tokenizer.excluded_token_types
        ]),
        num_excluded_tokens=len([
            token for token in tokens
            if token[RegexTokenizer.INDEXES["TYPE"]] in tokenizer.excluded_token_types
        ])
    )
    if formatters is not None:
        format_outputs = _format_text_with_existing_instances(tag_maps, tokens, output_dict, corpus_info, formatters, write_to_disk=write_to_disk)
        output_dict["format_outputs"] = format_outputs
        output_dict["html_name"] = os.path.basename(format_outputs["HTML"]["app"])
    # del output_dict["tags"]
    return output_dict


@celery.task
def tag_text(text_path, corpus_info, corpus_data_files, tags, formats=None, write_to_disk=False):
    # Open the text file and get its contents.
    if not os.path.exists(text_path):
        raise ValueError("Text file '%s' does not exist." % text_path)
    text_name = os.path.basename(text_path)
    text_file = codecs.open(text_path, encoding="UTF-8")
    text_contents = text_file.read()
    text_file.close()

    # Tokenize.
    tokenizer = RegexTokenizer()
    tokens = tokenizer.tokenize(text_contents)

    # Import and instantiate the taggers.
    tag_dicts = {}
    tag_maps = {}
    # TODO: Parallelize?
    for tag_name, tag_args in tags.items():
        if tag_name in tag_dicts or tag_name in tag_maps:
            raise NotImplementedError("Tagging multiple times with the same tagger is not yet supported.")
        tagger_name = tag_name + "Tagger"
        tagger_module = getattr(__import__("Ity.Taggers", fromlist=tagger_name), tagger_name)
        # Add some additional instantiation arguments for specific taggers.
        # TODO: Clean up Taggers' init() arguments.
        if tag_args is None:
            tagger_init_args = {}
        else:
            tagger_init_args = tag_args
        # Optionally use the rules file that was uploaded with the
        if tag_name == "SimpleRule" and (
            "SimpleRule" in corpus_data_files and
            "saved" in corpus_data_files["SimpleRule"]
            and len(corpus_data_files["SimpleRule"]["saved"]) > 0
        ):
            if "rules_filename" not in tagger_init_args:
                if len(corpus_data_files["SimpleRule"]["saved"]) > 1:
                    raise NotImplementedError("Multiple rules files for SimpleRuleTagger is not yet supported.")
                tagger_init_args.update(
                    rules_filename=corpus_data_files["SimpleRule"]["saved"][0]
                )
            # Otherwise, SimpleRuleTagger will use the default rules file it knows the path to internally.
        elif tag_name == "TopicModel":
            tagger_init_args.update(
                corpus_name=corpus_info["name"]
            )
        # Instantiate this tagger.
        tagger_instance = tagger_module(**tagger_init_args)
        # Tag with this tagger.
        single_tag_data, single_tag_maps = tagger_instance.tag(tokens)
        tag_dicts[tag_name] = single_tag_data
        tag_maps[tag_name] = single_tag_maps

    # Return the text name, list of tag dicts, and some token counts.
    output_dict = dict(
        text_path=text_path,
        text_name=text_name,
        text_key=nameToKey(os.path.splitext(text_name)[0]),
        corpus_name=corpus_info["name"],
        text_contents=text_contents,
        # tokens=tokens,
        tag_dicts=tag_dicts,
        # tags=tags,
        num_tokens=len(tokens),
        num_word_tokens=len([
            token for token in tokens
            if token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["WORD"]
        ]),
        num_punctuation_tokens=len([
            token for token in tokens
            if token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["PUNCTUATION"]
        ]),
        num_included_tokens=len([
            token for token in tokens
            if token[RegexTokenizer.INDEXES["TYPE"]] not in tokenizer.excluded_token_types
        ]),
        num_excluded_tokens=len([
            token for token in tokens
            if token[RegexTokenizer.INDEXES["TYPE"]] in tokenizer.excluded_token_types
        ])
    )
    if formats is not None:
        format_outputs = format_text(tag_maps, tokens, output_dict, corpus_info, formats, write_to_disk=write_to_disk)
        output_dict["format_outputs"] = format_outputs
        output_dict["html_name"] = os.path.basename(format_outputs["HTML"]["app"])
    # del output_dict["tags"]
    return output_dict


def _format_text_with_existing_instances(tag_maps, tokens, output_dict, corpus_info, formatters, write_to_disk=True):
    format_outputs = {}
    for format_name, formatter in formatters.items():
        # Format with this formatter.
        if len(output_dict["tag_dicts"].keys()) > 1:
            raise NotImplementedError("Formatting with multiple taggers is not yet supported.")
        format_output = formatter.format_paginated(
            tags=(output_dict["tag_dicts"].values()[0], tag_maps.values()[0]),
            tokens=tokens,
            text_name=os.path.splitext(output_dict["text_name"])[0],
            processing_id=corpus_info["processing_id"]
        )
        format_outputs.update(
            # _save_separate_paginated_format_output(
            _save_single_paginated_format_output(
                output_dict,
                corpus_info,
                write_to_disk,
                format_name,
                format_output
            )
        )
    return format_outputs


@celery.task
def format_text(tag_maps, tokens, output_dict, corpus_info, formats, write_to_disk=True):
    format_outputs = {}
    for format_name, format_args in formats.items():
        if format_name in format_outputs:
            raise NotImplementedError("Formatting multiple times with the same formatter is not yet supported.")
        formatter_name = format_name + "Formatter"
        formatter_module = getattr(__import__("Ity.Formatters", fromlist=formatter_name), formatter_name)
        # Add some additional instantiation arguments for specific formatters.
        # TODO: Clean up Taggers' init() arguments.
        if format_args is None:
            formatter_init_args = {}
        else:
            formatter_init_args = format_args
        # Instantiate this formatter.
        formatter_instance = formatter_module(**formatter_init_args)
        # Format with this formatter.
        if len(output_dict["tag_dicts"].keys()) > 1:
            raise NotImplementedError("Formatting with multiple taggers is not yet supported.")
        format_output = formatter_instance.format_paginated(
            tags=(output_dict["tag_dicts"].values()[0], tag_maps.values()[0]),
            tokens=tokens,
            s=output_dict["text_contents"],
            partial=False,
            text_name=os.path.splitext(output_dict["text_name"])[0],
            single_file=True,
            processing_id=corpus_info["processing_id"]
        )
        format_outputs.update(
            # _save_separate_paginated_format_output(
            _save_single_paginated_format_output(
                output_dict,
                corpus_info,
                write_to_disk,
                format_name,
                format_output
            )
        )
    return format_outputs


def _save_single_paginated_format_output(
    output_dict,
    corpus_info,
    write_to_disk,
    format_name,
    format_output
):
    format_outputs = {}
    format_outputs[format_name] = {
        "app": None,
        "pages": [],
        "tags_json": None,
        "pages_json": None
    }
    text_name = os.path.splitext(output_dict["text_name"])[0]
    simplified_text_name = nameToKey(text_name)
    if write_to_disk:
        page_folder_name = "".join([
            # simplified_text_name,
            text_name,
            "_",
            "-".join(output_dict["tag_dicts"].keys())
        ])
        text_relative_path = os.path.dirname(
            output_dict["text_path"].replace(
                corpus_info["data"]["Text"]["path"] + "/",
                ""
            )
        )
        format_output_root = os.path.join(
            corpus_info["output_path"],
            corpus_info["provenance"],
            # "Formats",
            format_name,
            text_relative_path
        )
        if not os.path.exists(format_output_root):
            os.makedirs(format_output_root)
        # Write the app file to disk.
        app_output_path = os.path.join(
            format_output_root,
            page_folder_name + ".html"
        )
        app_output_file = codecs.open(app_output_path, "w", encoding="UTF-8")
        app_output_file.write(format_output)
        app_output_file.close()
        format_outputs[format_name]["app"] = app_output_path
    return format_outputs


def _save_separate_paginated_format_output(
    output_dict,
    corpus_info,
    formats,
    write_to_disk,
    format_name,
    format_args,
    format_output
):
    format_outputs = {}
    format_outputs[format_name] = {
        "app": None,
        "pages": [],
        "tags_json": None,
        "pages_json": None
    }
    text_name = os.path.splitext(output_dict["text_name"])[0]
    simplified_text_name = nameToKey(text_name)
    if write_to_disk:
        page_folder_name = "".join([
            # simplified_text_name,
            text_name,
            "_",
            "-".join(output_dict["tag_dicts"].keys())
        ])
        format_output_root = os.path.join(
            corpus_info["output_path"],
            corpus_info["provenance"],
            # "Formats",
            format_name,
            page_folder_name
        )
        if not os.path.exists(format_output_root):
            os.makedirs(format_output_root)
        # Write the app file to disk.
        app_output_path = os.path.join(
            format_output_root,
            "index.html"
        )
        app_output_file = codecs.open(app_output_path, "w", encoding="UTF-8")
        app_output_file.write(format_output["app"])
        app_output_file.close()
        format_outputs[format_name]["app"] = app_output_path
        # Write the tags file to disk.
        tags_output_path = os.path.join(
            format_output_root,
            "tags.json"
        )
        tags_output_file = codecs.open(tags_output_path, "w", encoding="UTF-8")
        tags_output_file.write(json.dumps(format_output["tags"]))
        tags_output_file.close()
        format_outputs[format_name]["tags_json"] = tags_output_path
        # Write the pages to disk.
        page_output_root = os.path.join(
            format_output_root,
            "pages"
        )
        if not os.path.exists(page_output_root):
            os.makedirs(page_output_root)
        for page_index, page_output in enumerate(format_output["pages"]):
            page_filename = "".join([
                str(page_index),
                "_",
                # simplified_text_name,
                text_name,
                "_",
                "-".join(output_dict["tag_dicts"].keys()),
                ".html"
            ])
            page_output_path = os.path.join(
                page_output_root,
                page_filename
            )
            page_output_file = codecs.open(page_output_path, "w", encoding="UTF-8")
            page_output_file.write(page_output)
            page_output_file.close()
            format_outputs[format_name]["pages"].append(page_output_path)
        # Write pages.json to disk.
        pages_json_output_path = os.path.join(
            format_output_root,
            "pages.json"
        )
        pages_json_output_file = codecs.open(pages_json_output_path, "w", encoding="UTF-8")
        pages_json_output_file.write(json.dumps([
            os.path.join("pages", os.path.basename(page_path))
            for page_path in format_outputs[format_name]["pages"]
        ]))
        pages_json_output_file.close()
        format_outputs[format_name]["pages_json"] = pages_json_output_path
    else:
        format_outputs[format_name] = format_output
    return format_outputs


@celery.task
def format_corpus(text_results, corpus_info, write_to_disk=True):
    format_name = "CSV"
    # TODO: Incorporate this into a much simpler CSVFormatter.
    logger.info("Formatting output for %u texts" % len(text_results))
    # Figure out which tags are in all the texts, and sort that list alphabetically.
    taggers_set = set()
    tag_keys_set = set()
    for text_dict in text_results:
        for tag_name, tags in text_dict["tag_dicts"].items():
            for tag_key in tags.keys():
                tag_short_name = tags[tag_key]['name']
                taggers_set.add(tag_name)
                tag_keys_set.add(
                    # Later - print period-delimited namespaced tag keys
                    ".".join([tag_name, tag_short_name])
                    # tag_key
                )
    tag_keys = sorted(tag_keys_set)
    # The keys from either the text_dict or the text_dict's tags key to use for
    # the CSV output (and its headers), in order.
    header_keys = [
      "text_name",
      "text_key",
      "html_name",
      "model_path"
    ] + tag_keys + [
        "num_included_tokens",
        "num_excluded_tokens",
        "num_tokens"
    ]
    output = ""
    # Print the headers.
    for header_index, header_key in enumerate(header_keys):
        if header_key in custom_header_key_titles:
            output += custom_header_key_titles[header_key]
        else:
            output += header_key
        if header_index < len(header_keys) - 1:
            output += ","
        else:
            output += "\n"
    # Print a header for the CSV-like output.
    for text_index, text_dict in enumerate(text_results):
        row_output = []
        for header_key in header_keys:
            # For counts that should not be percentages.
            if header_key in text_dict.keys() and header_key != "tags":
                row_output.append(str(text_dict[header_key]))
            # For counts that *should* be percentages.
            elif header_key in tag_keys:
                split_header_key = header_key.split(".")
                try:
                    text_tags = text_dict["tag_dicts"][split_header_key[0]]
                    current_tag = text_tags[[t for t in text_tags if text_tags[t]['name'] == split_header_key[1]][0]]
                    assert(current_tag["num_tags"] > 0)

                    # By default, display as a percentage.
                    value = current_tag["num_included_tokens"]
                    # Display as an integer if this header key is one of the custom titles.
                    if header_key not in custom_header_key_titles:
                        #value = text_dict["tag_dicts"][split_header_key[0]][split_header_key[1]]["num_included_tokens"]
                        value *= (100.0 / text_dict["num_included_tokens"])

                    row_output.append(str(value))
                except (IndexError, KeyError, AssertionError) as e:
                    row_output.append(str(0.0))
            # elif header_key in text_dict["tags"].keys():
            #     row_output.append(str(text_dict["tags"][header_key]["num_tag_maps"]))
            elif header_key in tag_keys:
                    row_output.append(str(0.0))
            else:
                row_output.append(str(0))
        output += ",".join(row_output) + "\n"
    if write_to_disk:
        format_output_root = os.path.join(
            corpus_info["output_path"],
            corpus_info["provenance"],
            # "Formats",
            format_name
        )
        if not os.path.exists(format_output_root):
            os.makedirs(format_output_root)
        format_filename = "".join([
            corpus_info["provenance"],
            ".csv"
        ])
        print format_filename
        if not os.path.exists(format_output_root):
            os.makedirs(format_output_root)
        format_output_path = os.path.join(
            format_output_root,
            format_filename
        )
        corpus_output_file = codecs.open(format_output_path, "w", encoding="UTF-8")
        corpus_output_file.write(output)
        corpus_output_file.close()
        # Return the path to the file on-disk.
        return format_output_path
    else:
        # Pass along the full output.
        return output


@celery.task
def archive_corpus_output(corpus_info):
    zip_archive_root = os.path.join(
        corpus_info["output_path"],
        "..",
        "Archives"
    )
    if not os.path.exists(zip_archive_root):
        os.makedirs(zip_archive_root)
    zip_archive_filename = "".join([
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
                arcname=os.path.join(relative_root_path, the_file)
            )
    zip_archive_file.close()
    return zip_archive_path


def nameToKey(the_name):
    return filter(lambda x: x.isalnum(), the_name).lower().lstrip().rstrip()

if __name__ == "__main__":
    celery.start()
