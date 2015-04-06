from __future__ import absolute_import

__author__ = 'kohlmannj'

import os
import sys
sys.path.append(os.path.dirname(os.path.basename(__file__)))
from time import time

from celery.result import AsyncResult
import tasks


if __name__ == "__main__":
    corpus_info, corpus_data_files = tasks.get_corpus_info(
        # corpus_path="/Users/kohlmannj/Dropbox/VEP Workspace/Apps/Serendip+Ity/Data/Corpora/Globe/"
        corpus_path="/Users/kohlmannj/Dropbox/VEP Workspace/Apps/Serendip+Ity/Data/Corpora/Globe_KingHenry/"
        # corpus_path="/Users/kohlmannj/Dropbox/VEP Workspace/Apps/Serendip+Ity/Data/Corpora/Globe_Neue"
    )
    args = {
        "corpus_info": corpus_info,
        "corpus_data_files": corpus_data_files,
        "tags": {
            "Docuscope": None
        },
        "formats": {
            "HTML": {
                "portable": True
            }
        },
        "batch_formats": {
            # "CSV": None
        },
        "write_to_disk": True,
        "create_zip_archive": True
    }
    # Determine if we should execute asynchronously.
    async = len(tasks.celery.control.ping(timeout=0.15)) > 0
    # Update the Celery instance's configuration.
    tasks.celery.conf["ASYNC"] = async

    if async:
        print "Asynchronous with Celery."
        # Get the Celery ID of the callback task which returns the final output.
        result = tasks.tag_corpus.delay(**args)
        previous_percent = 0.0
        previous_state = ""
        print "Processing..."
        while True:
            result = AsyncResult(result.id)
            if result.state in ("SUCCESS", "FAILURE"):
                break
            if (
                result.state == "PROGRESS" and
                type(result.result) is dict and
                "current" in result.result and
                type(result.result["current"]) is float and
                "total" in result.result and
                type(result.result["total"]) is float
            ):
                progress_percent = result.result["current"] / result.result["total"] * 100.0
                if previous_percent != progress_percent:
                    print "%s: %f%%" % (result.state, progress_percent)
                    previous_percent = progress_percent
            elif result.state != previous_state:
                print str(result.state)
                previous_state = result.state
        if result.state == "SUCCESS":
            print "Succeeded!"
        elif result.state == "FAILURE":
            print "Failed!"
        print result.get()
        # Get the result of the callback task.
        # callback_result = AsyncResult(callback_id)
        # Wait for the callback task to return.
        # callback_return_value = callback_result.get()
        # Print the callback return value.
        print "Finished.\n"
        # print callback_return_value
    else:
        print "Synchronous."
        print "Processing..."
        return_value = tasks.tag_corpus(**args)
        print "Finished.\n"
        print return_value
