__author__ = 'wintere'

import sys
import csv
import os
import urllib2
import argparse
import shutil
import re





#modified from ubiq+ity arg parser
parser = argparse.ArgumentParser(description='TCP file distribution')
parser.add_argument('input_path', help='path to corpus to copy relative to the location of this script')
parser.add_argument('output_path', help='path to destination relative to the location of this script')
parser.add_argument('--move_nonTCP', help='enable this option to copy non TCP files (ones with no recognizable ID)', action='store_true')

args = parser.parse_args()

# this link is tied to a specific github commit, so it may become dated at some point
url = "https://raw.githubusercontent.com/textcreationpartnership/Texts/738a553aa6102261bdae52267919da2a1b66fef9/TCP.csv"
response = urllib2.urlopen(url)

eebo_ph2_files = set()
# with open('tcp.csv', 'rb') as tcp_directory:
file = csv.reader(response, delimiter=',', quotechar='"')


# get eebo phase two files name
for row in file:
    if (row[4] != '') and ("Restricted" in row[4]):
        eebo_ph2_files.add(row[0])

restricted = [] # names of restricted files

print "Checking files against restricted list..."

tcp = r'(K\d\d\d\d\d\d.\d\d\d)|((A|B|N|K)\d\d\d\d\d)'
re.compile(tcp)
for dirpath, subdirs, files in os.walk(args.input_path):
    for file in files:
        dest_path = os.path.join(args.output_path, file)
        orig_path = os.path.join(dirpath, file)
        m = re.search(tcp, file)
        if m:
            id = m.group(0)
            if id in eebo_ph2_files:
                restricted.append(file)
            else:
                # copy legal files
                shutil.copy2(orig_path,dest_path)
        else:
            if args.move_nonTCP:
                shutil.copy2(orig_path,dest_path)


with open('tcp_restricted_b.txt', 'wb') as f:
    f.write("TCP_FILE_DISTRIBUTION.PY\nInput path: %s \nOutput path: %s \nRestricted (uncopied) files: \n" % (args. input_path, args.output_path))
    for i in restricted:
        f.write(i + '\n')

if len(restricted) != 0:
    print "Some files were not copied due to copyright restrictions on EEBO Phase 2. " \
          "Their filenames were written to tcp_restricted.txt.",

else:
    print ("All files were copied over.")
