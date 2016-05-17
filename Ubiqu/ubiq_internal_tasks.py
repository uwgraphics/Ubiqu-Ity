from __future__ import absolute_import
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
import sys
import unicodecsv as csv
sys.path.append(os.path.join(
    os.path.dirname(os.path.basename(__file__)),
    ".."
))
sys.path.append(os.path.dirname(os.path.basename(__file__)))
from Ity import DATA_NAMES, DATA_EXTENSIONS
from Ity.Tokenizers import RegexTokenizer
from Ity.Tools import TokenTransform

version = 1.1


header_titles = {
    "<# Word Tokens>": "num_word_tokens",
    "<# Punctuation Tokens>": "num_punctuation_tokens",
    "<# Tokens>": "num_tokens", "<# Gap Tokens>": "gap_count"}

#primary tagging method utilized by both web and command line version of Ubiq+Ity
#access via tagCorpus.py
def tag_corpus(
        corpus_info,
        corpus_data_files,
        email = '',
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
        app_mode=False,
        current_task=None,
        logger=None,
        token_csv=False
):
    print 'Starting tag_corpus...'
    tag_corpus_start = time()
    timing = []

    if not generate_text_htmls:
        formats=ImmutableDict()
    # Validate corpus_info.
    if "path" not in corpus_info or "name" not in corpus_info or "data" not in corpus_info:
        raise ValueError("Invalid corpus_info provided.")

    # Validate parameters
    if chunk_text:
        if chunk_length is None:
            chunk_length = 2000 #default chunk size
        else:
            chunk_length = int(chunk_length)
        if chunk_offset is None:
            chunk_offset = chunk_length #default offset is chunk length
        else:
            chunk_offset = int(chunk_offset)
        if chunk_length < chunk_offset:
            raise ValueError("Invalid chunking parameters: chunk_offset must be <= chunk_length.")
    else:
        if chunk_length is not None or chunk_offset is not None:
            raise ValueError("Text chunking must be enabled to set chunk_length or chunk_offset.")

    if ngram_count is None and ngram_pun == True:
        raise ValueError("Ngrams must be enabled to set ngram punctuation count.")

    if ngram_count is None:
        ngram_count = 0

    if int(ngram_count) < 0 or int(ngram_count) > 3:
        raise ValueError("Ngram count must be between 1 and 3.")
    else:
        ngram_count = int(ngram_count)

    if name != '': #add a hyphen to match output naming scheme
        name = name + "-"

    if doc_rule and not rule_csv:
        raise ValueError("Must enable rule counting to enable per document rule information.")

    if chunk_text and rule_csv:
        raise ValueError('Rule counting and chunking cannot be performed simultaneously.')

    if chunk_text and token_csv:
            raise ValueError('Token csvs and chunking cannot be performed simultaneously.')

    # Validate blacklist params and retrieve blacklist words
    blacklist = []
    if blacklist_path is not None:
        if not os.path.exists(blacklist_path) or blacklist_path.endswith('.txt') is False:
            raise ValueError("Blacklist text file '%s' does not exist. Please supply a valid space-separated .txt file." % blacklist_path)
        else:
            try:
                f = open(blacklist_path)
                for line in f:
                    words = line.split()
                    blacklist.extend(words)
            except IOError:
                raise ValueError("Unable to open blacklist file %s. Please supply a valid space-separated .txt file." % blacklist_path)

    # Or, retrieve blacklisted words from GUI
    elif blacklist_words is not None:
        blacklist = str(blacklist_words).split()
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
        try:
            __import__("Ity.Taggers." + tag_name + "Tagger")
        except:
            raise ValueError("A Tagger module for '%s' tags does not exist." % tag_name)
    is_docuscope=True


    # Instantiate Taggers.
    start = time()
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
            is_docuscope=False
            tagger_init_args.update(
                dictionary_path=corpus_data_files["SimpleRule"]["saved"][0],
                return_untagged_tags=True,
                return_unrecognized_tags=True,
                blacklist=blacklist
            )
        else:
            tagger_init_args.update(
                return_untagged_tags=True,
                return_unrecognized_tags=True,
                return_excluded_tags=False,             # prevents display/tagging of whitespace
                return_included_tags=True,
                blacklist=blacklist,
            )
        # Instantiate this Tagger.
        # optimization: detailed tag data isn't required UNLESS we generate HTML files or tag-level rule statistics
        if generate_text_htmls or rule_csv or token_csv:
            tagger_init_args.update(return_tag_maps=True)

        tagger_instance = tagger_module(**tagger_init_args)
        tagger_instances[tag_name] = tagger_instance
    timing.append(('Instantiate Taggers', time() - start))

    # Validate formatters.
    for format_name in formats.keys() + batch_formats.keys():
        __import__("Ity.Formatters." + format_name + "Formatter")

    # Instantiate Formatters.
    start = time()
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
    timing.append(('Instantiate Formatters', time() - start))

    # Get all the texts in this corpus...if there are any?
    if "Text" not in corpus_info["data"] or len(corpus_data_files["Text"]["saved"]) == 0:
        raise StandardError("No corpus texts to tag!")
    text_paths = corpus_data_files["Text"]["saved"]

    if app_mode:
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

    # initialize primary csv
    csv_path = getCSVPath(corpus_info, name, 'gen')
    lats = sorted(tagger_instances['Docuscope']._ds_dict.lats)
    header_keys = getHeaderKeys(lats, is_docuscope, defect_count)
    u = open(csv_path, 'wb')
    uwriter = csv.writer(u, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    uwriter.writerow(header_keys)

    #initialize rule dict
    corpus_map = dict()
    if ngram_count > 0:
        documentNgramCounts = defaultdict(int) # to count number of documents ngrams appear in
        corpusNgramCounts = defaultdict(int)

    start = time()
    tokenizer = RegexTokenizer()
    timing.append(('Tokenizer Initialization Time: ', time() - start))

    # tag each text
    tag_start = time()
    index = 0
    tokenization_time = 0
    tagging_time = 0

    # initialize unreadable files list
    bad_texts = []

    for text_path in text_paths:
        # tokenize
        start = time()
        try:
            tokens = tokenizeText(text_path, defect_count, chunk_length, chunk_offset, tokenizer)
        # skip texts that can't be tokenized
        except NotImplementedError:
            bad_texts.append(text_path)
            continue
        if token_csv:
            token_frame = TokenTransform.transformToFrame(tokens)

        tokenization_time += (time() - start)

        start = time()
        result = tagText(tagger_instance, tag_name, text_path, tokens, corpus_info, formatter_instances, chunk=chunk_text, rule_csv=rule_csv, html=generate_text_htmls, token_csv=token_csv)
        if token_csv:
            tagged_frame = TokenTransform.tagFrameMerge(token_frame, result)
            tokenCSVPath = getCSVPath(corpus_info, name, type='token_csv', docName=result['text_key'])
            tagged_frame.to_csv(tokenCSVPath, index=False, header=False, encoding='utf-8')
        tagging_time += (time() - start)

        # iterate through tokens (or sub-lists of tokens) and calculate token level statistics (if necessary)
        # then delete tokens to free up space
        if chunk_text:
            if defect_count:
                for i in range(len(result)):
                    result[i] = defectProcess(result[i], tokens[0][i])
        else:
            if defect_count:
                result = defectProcess(result, tokens)

        if chunk_text:
            tokens = tokens[1]

        if ngram_count > 0:
            ngram_tokens = ngramProcess(tokens, ngram_pun)

        # done with tokens, free up memory
        del tokens

        # write out primary csv
        if chunk_text:
            for text_dict in result:
                row = result_to_gen_row(text_dict, header_keys)
                uwriter.writerow(row)
        else:
            row = result_to_gen_row(result, header_keys)
            uwriter.writerow(row)

        # update corpus dictionaries
        if rule_csv:
            rule_map = result['rule_map']
            updateCorpusCounts(rule_map,corpus_map)
            if doc_rule:
                perDocRuleCSV(corpus_info, result['text_key'], rule_map) # generate PER document CSVs all in one method (they all need separate writers anyway)
        del result
        if ngram_count > 0:
            docCounts = ngramUpdate(ngram_tokens, documentNgramCounts, corpusNgramCounts, ngram_count, ngram_pun)
            if ngram_per_doc:
                docName = os.path.splitext(os.path.basename(text_path))[0]
                ngramCSV(documentNgramCounts=None, corpusNgramCounts=docCounts, maxN=ngram_count, corpus_info=corpus_info, name=name, docName=docName)
        if app_mode:
            if current_task.request.id is not None:
                current_task.update_state(
                    state='PROGRESS',
                    meta={'current': float(index + 1) / len(text_paths) * 100.0, 'total': 100.0}
                )
        index = index + 1

    u.close()

    timing.append(('Total Tokenization', tokenization_time))
    timing.append(('Total Tagging', tagging_time))
    text_tagging_time = time() - tag_start
    # write out corpus-wide rule CSV (if applicable)
    if rule_csv:
        ruleCSV(corpus_info, name, corpus_map)

    if ngram_count > 0:
        ngramCSV(documentNgramCounts, corpusNgramCounts, ngram_count, corpus_info, name)


    frame = inspect.currentframe()
    tc_args, _, _, tc_values = inspect.getargvalues(frame)
    buildReadme(tc_args, tc_values, timing, version, blacklist, bad_texts)

    if app_mode:
        # Update progress. (Web version)
        if current_task.request.id is not None:
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 100.0, 'total': 100.0}
            )

    print 'tag_corpus finished. Total elapsed time: %.2f seconds.' % (time() - tag_corpus_start)

    return csv_path


#builds a text readme to accompany successful jobs
def buildReadme(args, values, timing,version, blacklist=[], bad_texts=[]):
    readmeLines = []
    readmeLines.append('Application version: %s' % version)
    readmeLines.append('Name: %s' % values['corpus_info']['name'])
    readmeLines.append('processing_id: %s' % values['corpus_info']['processing_id'])
    if values['name'] != '':
        readmeLines.append('job name: %s' % values['name'][:-1])
    readmeLines.append('provenance: %s' % values['corpus_info']['provenance'])
    readmeLines.append('email: %s' % values['email'])
    readmeLines.append('')
    readmeLines.append('PARAMS:')
    readmeLines.append('generate_text_htmls: %s' % values['generate_text_htmls'])
    readmeLines.append('generate_rule_csv: %s' % values['rule_csv'])
    readmeLines.append('generate token csv representation: %s' % values['token_csv'])
    readmeLines.append('create_zip_archive: %s' % values['create_zip_archive'])
    readmeLines.append('chunked: %s' % values['chunk_text'])
    if values['chunk_text']:
        readmeLines.append('chunk length: %s tokens' % values['chunk_length'])
        readmeLines.append('chunk offset: %s tokens' % values['chunk_offset'])
    if values['ngram_count'] > 0:
        readmeLines.append('ngram count: %s tokens' % values['ngram_count'])
        readmeLines.append('ngram punctuation: %s ' % values['ngram_pun'])
    readmeLines.append('')
    readmeLines.append('PATH INFO:')
    readmeLines.append('corpus_path: %s' % values['corpus_info']['path'])
    readmeLines.append('output_path: %s' % values['corpus_info']['output_path'])
    readmeLines.append('')
    readmeLines.append('DICTIONARY INFO')
    readmeLines.append('dictionary: %s' % os.path.basename(values['tagger_instances']['Docuscope'].dictionary_path))
    readmeLines.append('')
    if blacklist != []:
        readmeLines.append('BLACKLISTED WORDS')
        readmeLines.append(str(blacklist))
        readmeLines.append('')
    readmeLines.append('TIMING INFO')
    for task, timeTaken in timing:
        readmeLines.append('%s: %.2f seconds' % (task, timeTaken))
    readmeLines.append('')
    readmeLines.append('TEXTS:')
    readmeLines.append('  saved:')
    for name in values['corpus_data_files']['Text']['saved']:
        readmeLines.append('    %s' % name)
    readmeLines.append('  skipped:')
    for name in values['corpus_data_files']['Text']['skipped']:
        readmeLines.append('    %s' % name)
    readmeLines.append('')
    if bad_texts != []:
        readmeLines.append('UNABLE TO DECODE THE FOLLOWING FILES:')
        for fp in bad_texts:
            readmeLines.append(os.path.basename(fp))
        readmeLines.append('')
    readmePath = os.path.join(values['corpus_info']['output_path'],values['corpus_info']['provenance'],'README.txt')
    with open(readmePath, 'wb') as readmeF:
        readmeF.write('\n'.join(readmeLines))


# given a text path, reads in and tokenizes the given text
# returns a list of tokens
def tokenizeText(text_path, tcp, chunk_length, chunk_offset, tokenizer):
    if not os.path.exists(text_path):
        raise ValueError("Text file '%s' does not exist." % text_path)
    text_contents = None
    text_file = None
    for encoding in ["utf-8", "ascii"]:
        try:
            text_file = codecs.open(text_path, encoding="UTF-8", errors="ignore")
            text_contents = text_file.read()
        except UnicodeDecodeError:
            pass
        finally:
            if text_file is not None:
                text_file.close()
    if text_contents is None:
        raise NotImplementedError("Could not find a valid encoding for input file %s" % text_path)

    # returns a list of tokens
    tokens = tokenizer.tokenize(text_contents)

    if tcp:
        tokens = tcp_prep(tokens)

    # if chunking is enabled, divide tokens into sublists
    if chunk_length != None:
        tokens_list = []
        vt_list = []
        i = 0
        for token in tokens: # mark non-white space tokens
            type = token[RegexTokenizer.INDEXES["TYPE"]]
            # use only word and punctuation tokens (no white space) to generate token count
            if type == RegexTokenizer.TYPES["WORD"] or type == RegexTokenizer.TYPES["PUNCTUATION"]:
                vt_list.append(i)
            i += 1
        if len(vt_list) <= chunk_length: # if there aren't enough non-white space tokens to form multiple chunks
            tokens_list = [tokens]
        else:
            i = 0
            while i < len(vt_list) and (i + chunk_length) < len(vt_list): # use non-white space tokens to divide tokens
                start = vt_list[i]
                end = vt_list[i + chunk_length]
                tokens_list.append(tokens[start:end])
                i += chunk_offset
            # add remaining tokens to list
            tokens_list.append(tokens[vt_list[i]:])
        return tokens_list, tokens

    return tokens

#tagText(tagger_instance, tag_name, text_path, tokens, corpus_info, formatter_instances, chunk=chunk_text, rule_csv=rule_csv, html=generate_text_htmls, token_csv=token_csv)
def tagText(tagger, tag_name, text_path, tokens, corpus_info, formatters, chunk=False, rule_csv=False, html=False, token_csv=False):
    result = {}
    single_tag_maps = {}
    text_name = os.path.basename(text_path)

    if not chunk:
        if rule_csv or html or token_csv:
            single_tag_data, single_tag_maps = tagger.tag(tokens)
            if rule_csv:
                result['rule_map'] = defaultdict(int)
                for i in single_tag_maps:
                    if i["rules"][0][0] not in ["!UNTAGGED", "!UNRECOGNIZED"]:
                        name = i["rules"][0][0]
                        instance = i["rules"][0][1]
                        result['rule_map'][(name,instance)] += 1
        else:
            single_tag_data = tagger.tag(tokens)
        w, p, t = 0,0,0
        for token in tokens:
            # this loop makes sure that white space tokens don't affect the total token count
            if token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["WORD"]:
                w += 1
                t += 1
            elif token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["PUNCTUATION"]:
                p += 1
                t +=1
        result.update(
            text_path=text_path,
            text_name=text_name,
            text_key=nameToKey(os.path.splitext(text_name)[0]),
            tag_dicts=single_tag_data,
            tag_maps=single_tag_maps,
            num_punctuation_tokens=p,
            num_word_tokens=w,
            num_tokens=t,
        )
        if html:
            format_outputs = _format_text_with_existing_instances(single_tag_maps, tokens, result, corpus_info, formatters)
            result["format_outputs"] = format_outputs
            try:
                result["html_name"] = os.path.basename(format_outputs["HTML"]["app"])
            except KeyError:
                pass # This is for if there is no HTMLFormatter. Super cheap hack.

        return result
    else:
        output_dict_list = []
        i = 0
        for token_sub in tokens[0]:
            if html:
                single_tag_data, single_tag_maps = tagger.tag(token_sub)
            else:
                single_tag_data = tagger.tag(token_sub)
            w, p, t= 0,0,0
            for token in token_sub:
                if token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["WORD"]:
                    w += 1
                    t += 1
                elif token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["PUNCTUATION"]:
                    p += 1
                    t +=1
            output_dict = dict(
                text_path=text_path,
                text_name=text_name,
                chunk_index=i,
                text_key=nameToKey(os.path.splitext(text_name)[0]),
                tag_dicts=single_tag_data,
                tag_maps=single_tag_maps,
                num_punctuation_tokens=p,
                num_word_tokens=w,
                num_tokens=t,
            )
            if html:
                format_outputs = _format_text_with_existing_instances(single_tag_maps, token_sub, output_dict, corpus_info, formatters, chunk='_'+str(i))
                try:
                    output_dict["html_name"] = os.path.basename(format_outputs["HTML"]["app"])
                except KeyError:
                    pass
            output_dict_list.append(output_dict)
            i += 1
        return output_dict_list

def _format_text_with_existing_instances(tag_maps, tokens, output_dict, corpus_info, formatters, chunk=''):
    format_outputs = {}
    for format_name, formatter in formatters.items():
        # Format with this formatter.
        format_output = formatter.format_paginated(
            tags=(output_dict["tag_dicts"], tag_maps),
            tokens=tokens,
            text_name=os.path.splitext(output_dict["text_name"]),
            processing_id=corpus_info["processing_id"]
        )
        format_outputs.update(
            # _save_separate_paginated_format_output(
            _save_single_paginated_format_output(
                output_dict,
                corpus_info,
                format_name,
                format_output,
                chunk
            )
        )
    return format_outputs

def _save_single_paginated_format_output(
        output_dict,
        corpus_info,
        format_name,
        format_output,
        chunk=''
):
    format_outputs = {}
    format_outputs[format_name] = {
        "app": None,
        "pages": [],
        "tags_json": None,
        "pages_json": None
    }
    text_name = output_dict["text_key"]
    page_folder_name = "".join([
        text_name,
        "_",
        "Docuscope"
    ])
    tmpRelPath = output_dict["text_path"].replace(
        corpus_info["data"]["Text"]["path"],
        ""
    )
    while tmpRelPath.startswith('/') or tmpRelPath.startswith("\\"):
        tmpRelPath = tmpRelPath[1:]
    text_relative_path = os.path.dirname(tmpRelPath)
    if chunk == '':
        format_output_root = os.path.join(
            corpus_info["output_path"],
            corpus_info["provenance"],
            # "Formats",
            format_name.lower(),
            text_relative_path
        )
    # if the output is chunked, organized each html file into its respective folder
    else:
        format_output_root = os.path.join(
            corpus_info["output_path"],
            corpus_info["provenance"],
            # "Formats",
            format_name.lower(),
            text_relative_path, page_folder_name
        )
    if not os.path.exists(format_output_root):
        os.makedirs(format_output_root)
    # Write the app file to disk.
    app_output_path = os.path.join(
        format_output_root,
        page_folder_name + chunk + ".html"
    )
    app_output_file = codecs.open(app_output_path, "w", encoding="UTF-8")
    app_output_file.write(format_output)
    app_output_file.close()
    format_outputs[format_name]["app"] = app_output_path
    return format_outputs

#writes formatted output to paginated html files
def _save_separate_paginated_format_output(
        output_dict,
        corpus_info,
        formats,
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
    return format_outputs

header_titles = {
    "<# Word Tokens>": "num_word_tokens",
    "<# Punctuation Tokens>": "num_punctuation_tokens",
    "<# Tokens>": "num_tokens", "<# Gap Tokens>": "gap_count"}


# generates frequencies of each rule in a tagged corpus
def rules_csv(tag_results, corpus_info, name=''):
    #write metadata inside csv directory
    format_output_root = os.path.join(
        corpus_info["output_path"],
        corpus_info["provenance"], 'csv'
    )
    format_output_path = os.path.join(
        format_output_root,name+
                           'rule-count-'+corpus_info["provenance"]+'.csv')
    #generate corpus level dictionary
    corpus_map = dict()
    for i in tag_results:
        rule_map = i["rule_map"]
        for k in rule_map.keys():
            try:
                corpus_map[k] += rule_map[k]
            except KeyError:
                corpus_map[k] = rule_map[k]
    with open(format_output_path, 'wb') as g:
        header = ["Lat", "Rule", "Frequency"]
        awriter = csv.writer(g, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        awriter.writerow(header)
        for key, value in sorted(corpus_map.iteritems(), key=lambda (k,v): (v,k), reverse=True):
            rule = key[1]
            if isinstance(rule, (tuple)): #pretty up tuples to print like strings
                rule = ' '.join(rule)
            row = [key[0],rule, value]
            awriter.writerow(row)

# creates a single document csv from a tag dict
def doc_rules_csv(tag_results, corpus_info):
    #make sub-dir for document data
    format_output_root = os.path.join(
        corpus_info["output_path"],
        corpus_info["provenance"], 'csv','per_document_csv'
    )
    if not os.path.exists(format_output_root):
        os.makedirs(format_output_root)
    for i in tag_results:
        rule_map = i["rule_map"]
        name = i["text_key"]
        doc_path = os.path.join(
            format_output_root,
            name + '-rule-count.csv')
        with open(doc_path, 'wb') as g:
            header = ["Lat", "Rule", "Frequency"]
            awriter = csv.writer(g, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            awriter.writerow(header)
            for key, value in sorted(rule_map.iteritems(), key=lambda (k,v): (v,k), reverse=True):
                rule = key[1]
                if isinstance(rule, (tuple)): #pretty up tuples to print like strings
                    rule = ' '.join(rule)
                row = [key[0],rule, value]
                awriter.writerow(row)

# takes a single text dict and transforms it into a row in an open csv
def result_to_gen_row(text_dict, header_keys):
    curRow = []
    tags = text_dict['tag_dicts']
    k = text_dict.keys()
    num_tokens = text_dict['num_word_tokens'] + text_dict['num_punctuation_tokens']
    for column in header_keys:
        if column in k:
            curRow.append(str(text_dict[column]))
        elif header_titles.get(column) in k:
            curRow.append(str(text_dict[header_titles.get(column)]))
        elif column == "<% Defective Word Tokens>" and text_dict['num_word_tokens'] > 0:
            curRow.append(str(text_dict["wdefect_count"]/float(text_dict['num_word_tokens']) * 100))
        elif column == "<% Illegible Punctuation Tokens>" and text_dict['num_punctuation_tokens'] > 0:
            curRow.append(str(text_dict["pdefect_count"]/float(text_dict['num_punctuation_tokens']) * 100))
        else:
            in_dict = False
            for td in tags.values():
                id = td['name']
                if column == id:
                    curRow.append(str((td['num_included_tokens']/float(num_tokens)) * 100))
                    in_dict = True
                    break
            if not in_dict:
                curRow.append('0')
    return curRow

# instantiates CSV directory if necessary and returns appropriate filepath
def getCSVPath(corpus_info, name, type, docName=None):
    format_output_root = os.path.join(
        corpus_info["output_path"],
        corpus_info["provenance"], 'csv'
    )
    ngram_output_root = os.path.join(
        corpus_info["output_path"],
        corpus_info["provenance"], 'ngram'
    )
    ngram_doc_root = os.path.join(
        corpus_info["output_path"],
        corpus_info["provenance"], 'ngram', 'perDocNgrams'
    )
    token_csv_root = os.path.join(
        corpus_info["output_path"],
        corpus_info["provenance"], 'token_csv'
    )
    if not os.path.exists(format_output_root):
        os.makedirs(format_output_root)
    if type == 'gen':
        format_output_path = os.path.join(
            format_output_root,
            name+corpus_info['provenance'] + '.csv'
        )
    elif type == 'rule':
        format_output_path = os.path.join(
            format_output_root,name+
                               'rule-count-'+corpus_info["provenance"]+'.csv')
    elif type == 'ngram':
        if not os.path.exists(ngram_output_root):
            os.makedirs(ngram_output_root)
        format_output_path = os.path.join(ngram_output_root, name+corpus_info["provenance"] + "-")
    elif type == 'doc_ngram':
        if not os.path.exists(ngram_output_root):
            os.makedirs(ngram_output_root)
        if not os.path.exists(ngram_doc_root):
            os.makedirs(ngram_doc_root)
        format_output_path = os.path.join(ngram_doc_root, name+corpus_info["provenance"] + "-" + docName + "-")
    elif type == 'token_csv':
        if not os.path.exists(token_csv_root):
            os.makedirs(token_csv_root)
        format_output_path = os.path.join(token_csv_root, name + corpus_info["provenance"] + "-" + docName + '-tokens' + '.csv')
    return format_output_path


#for a given general csv, returns an appropriate header
def getHeaderKeys(tag_list, is_docuscope, defect_count):
    if is_docuscope:
        tag_keys = ["!UNRECOGNIZED", "!UNTAGGED", "!BLACKLISTED"] # exclusive to docuscope
    else:
        tag_keys = ["!UNRECOGNIZED", "!UNTAGGED"] #custom rule dictionaries
    for tag in tag_list:
        tag_keys.append(tag)
    header_keys = [
                      "text_name",
                      "text_key",
                      "html_name",
                      "chunk_index"] + tag_keys + [
                      "<# Word Tokens>",
                      "<# Punctuation Tokens>",
                      "<# Tokens>"
                  ]
    if defect_count:
        header_keys.extend(["<% Defective Word Tokens>", "<% Illegible Punctuation Tokens>", "<# Gap Tokens>"])
    return header_keys

# for use with TCP pipeline, identifies special characters that indicate illegible letters, punctuation, and token gaps
def defectProcess(dict, tokens):
    # perform defect statistics on tcp text
    # for chunked texts, iterate through each set of tokens to calculate per-chunk statistics
    dict["wdefect_count"] = 0
    dict["pdefect_count"] = 0
    dict["gap_count"] = 0
    for token in tokens:
        if token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["WORD"] or token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["PUNCTUATION"]:
            ts = token[RegexTokenizer.INDEXES["STRS"]][0]
            # illegible letter
            if '^' in ts:
                dict["wdefect_count"] += 1
            # illegible punctuation
            if '*' in ts:
                dict["pdefect_count"] += 1
            # gap
            if ts == u'(...)':
                dict["gap_count"] += 1
    return dict

# prepares ngrams and inserts placeholder paragraph break tokens so that 2 and 3-grams do not extend over paragraph breaks (but continue over verse lines)
def ngramProcess(tokens, ngram_pun):
    token_list = []
    for token in tokens:
        if token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["WORD"] or \
                (token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["PUNCTUATION"] and ngram_pun):
            tokenString = token[RegexTokenizer.INDEXES["STRS"]][0]
            token_list.append(tokenString.lower()) #makes ngrams not case-sensitive
        elif token[RegexTokenizer.INDEXES["TYPE"]] == RegexTokenizer.TYPES["NEWLINE"]:
            tokenString = token[RegexTokenizer.INDEXES["STRS"]][0]
            if len(tokenString) > 1: #multi new-lines
                token_list.append("PB")
    return token_list

#updates per document and per corpus rule counts
def updateCorpusCounts(rule_map, corpus_map):
    for k in rule_map.keys():
        try:
            corpus_map[k] += rule_map[k]
        except KeyError:
            corpus_map[k] = rule_map[k]
    return rule_map

def perDocRuleCSV(corpus_info, text_key, rule_map):
    format_output_root = os.path.join(
        corpus_info["output_path"],
        corpus_info["provenance"], 'csv','per_document_csv'
    )
    if not os.path.exists(format_output_root):
        os.makedirs(format_output_root)
    doc_path = os.path.join(
        format_output_root,
        text_key + '-rule-count.csv')
    f = open(doc_path, 'wb')
    header = ["Lat", "Rule", "Frequency"]
    dwriter = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    dwriter.writerow(header)
    for key, value in sorted(rule_map.iteritems(), key=lambda (k,v): (v,k), reverse=True):
        rule = key[1]
        if isinstance(rule, (tuple)): #pretty up tuples to print like strings
            rule = ' '.join(rule)
        row = [key[0],rule, value]
        dwriter.writerow(row)
    f.close()

def ruleCSV(corpus_info, name, corpus_map):
    rule_path = getCSVPath(corpus_info, name, 'rule')
    header = ["Lat", "Rule", "Frequency"]
    r = open(rule_path, 'wb')
    rwriter = csv.writer(r, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    rwriter.writerow(header)
    for key, value in sorted(corpus_map.iteritems(), key=lambda (k,v): (v,k), reverse=True):
        rule = key[1]
        if isinstance(rule, (tuple)): #pretty up tuples to print like strings
            rule = ' '.join(rule)
        row = [key[0],rule, value]
        rwriter.writerow(row)
    r.close()
    return rule_path


#updates corpus-wide ngram dictionaries given a tokenized  text
def ngramUpdate(tokens, documentNgramCounts, corpusNgramCounts, ngram_count, pun):
    doc_grams = defaultdict(int)
    for maxN in range(1, ngram_count  + 1):
        queueFront = 0
        queueBack = maxN
        for i in range (1, maxN + 1):
            while queueBack <= len(tokens):
                win = tokens[queueFront:queueBack]
                if "PB" not in win or pun:
                    corpusNgramCounts[tuple(win)] += 1
                    doc_grams[tuple(win)] += 1
                queueFront = queueFront + 1
                queueBack = queueBack + 1

    for key in doc_grams.keys():
        documentNgramCounts[key] += 1
    return doc_grams

#given ngram dictionaries, writes out appropriate csvs
def ngramCSV(documentNgramCounts, corpusNgramCounts, maxN, corpus_info, name, docName=None):
    # initialize params to track file descriptors and rank
    fds = []
    writers = []
    rank = [0] * maxN
    prevCount = [sys.maxsize] * maxN

    # open and initialize ngram csvs
    if docName is None:
        for i in range(1, maxN + 1):
            path = getCSVPath(corpus_info, name, 'ngram') + str(i) + "grams.csv"
            f = open(path, 'wb')
            w = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            w.writerow(["ngram", "corpus frequency", "document frequency", "rank in corpus"])
            fds.append(f)
            writers.append(w)

    else:
        for i in range(1, maxN + 1):
            path = getCSVPath(corpus_info, name, 'doc_ngram', docName=docName) + str(i) + "grams.csv"
            f = open(path, 'wb')
            w = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            w.writerow(["ngram", "document frequency", "rank in document"])
            fds.append(f)
            writers.append(w)

    # rank and print ngrams
    cc = lambda (a1, a2), (b1, b2):cmp((b2, a1), (a2, b1))
    for key, value in sorted(corpusNgramCounts.iteritems(), cmp=cc):
        n = len(key) - 1
        if value < prevCount[n]:
            rank[n] += 1
            prevCount[n] = value
        if docName:
            row = [' '.join(key), value, rank[n]]
        else:
            row = [' '.join(key), value, documentNgramCounts[key], rank[n]]
        writers[n].writerow(row)

    for fd in fds:
        fd.close()

# groups together (...) marks into a single token for identification of gaps
def tcp_prep(tokens):
    tc = []
    i = 0
    while i < (len(tokens)):
        if tokens[i][0][0] == "(":
            if tokens[i+1][0][0] == "..." and tokens[i+2][0][0] == ")":
                new = tokens[i]
                new[0] = [u'(...)']
                new[2] = 5
                tc.append(new)
                i += 3
            else:
                tc.append(tokens[i])
                i += 1
        else:
            tc.append(tokens[i])
            i += 1
    return tc


def nameToKey(the_name):
    return filter(lambda x: x.isalnum(), the_name).lower().lstrip().rstrip()