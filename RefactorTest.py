# coding=utf-8
__author__ = 'kohlmannj'

from Ity import celery_tasks as tasks

corpus_path = "/Users/kohlmannj/Dropbox/VEP Workspace/Apps/Serendip+Ity/Data/Corpora/Globe_Rev/"

if __name__ == "__main__":
    # the_corpus = Corpus(corpus_path)
    saved_files = tasks.save_corpus(*process_corpus(path=corpus_path))
    print saved_files
