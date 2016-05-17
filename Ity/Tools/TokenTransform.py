__author__ = 'wintere-admin'

import abc
from Ity import BaseClass

import string
import csv
import codecs
import os
import pandas as pd

def end_reason(token):
    if token[0].isalpha():
        return 'c'
    elif (token[0] == u'\n') or (token[0] == '\n'):
        i = 0
        r = ''
        while i < (len(token)):
            r = r + 'n'
            i = i + 1
        return r
    elif token[0] in string.punctuation:
        return 'c'
    else:
        #s for whitespace
        return 's'

def transform(tokens, csv_path):
    rows = []
    c = 0
    for i in range(len(tokens)):

        #token number, token, token start index, end reason
        t = tokens[i][0][0]
        if (t not in string.whitespace) and (t[0] != '\n'):
            row = []
            row.append(c)
            row.append(t)
            row.append(tokens[i][1])
            if i < len(tokens) - 1:
                row.append(end_reason(tokens[i + 1][0][0]))
            else:
                row.append('e') #last token end reason is always EOF
            rows.append(row)
            c = c + 1
    with open(csv_path, 'wb') as g:
        awriter = csv.writer(g, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        awriter.writerow(['Token #', 'Token', 'Start Index', 'End Reason'])
        for row in rows:
            awriter.writerow(row)

def transformToFrame(tokens):
    rows = []
    for i in range(len(tokens)):
        # token number, token, token start index, end reason
        displayWord = tokens[i][0][0]
        token = displayWord.lower()
        if (token not in string.whitespace) and (token[0] != '\n'):
            row = []
            row.append(displayWord)
            row.append(token)
            row.append(tokens[i][1])
            if i < len(tokens) - 1:
                row.append(end_reason(tokens[i + 1][0][0]))
            else:
                row.append('e')  # last token end reason is always EOF
            rows.append(row)
    frame = pd.DataFrame(rows)
    frame.columns = ['display word', 'token','start index', 'end reason']
    return frame

def tagFrameMerge(frame, result):
    tagFrame = []
    for i in range(len(result['tag_maps'])):
        pos_start =  result['tag_maps'][i].get('pos_start')
        pos_end = result['tag_maps'][i].get('pos_end')
        tag = result['tag_maps'][i].get('rules')[0][0]
        if tag == '!UNTAGGED':
            tag = ''
        elif tag == '!UNRECOGNIZED':
            tag = 'UNRECOGNIZED'
        #columns = index, tag, position in tag
        tagFrame.append([pos_start, tag, 0])
        if pos_start != pos_end:
            #get all intermediate rows
            b = frame[(frame['start index'] > pos_start) & (frame['start index'] <= pos_end)]
            pos_in_tag = 1
            for index, row in b.iterrows():
                int_index = int(row['start index'])
                tagFrame.append([int_index,tag,pos_in_tag])
                pos_in_tag += 1
    tFrame = pd.DataFrame(tagFrame)
    tFrame.columns = ['start index', 'tag', 'position in tag']
    mergedFrame = frame.merge(tFrame, how='inner', on='start index')
    del mergedFrame['start index']
    return mergedFrame