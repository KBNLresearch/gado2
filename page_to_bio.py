#!/usr/bin/env python3

#
# page2bio.py
#
# Transforms page XML files from PRImA to .bio format used for training BERT-NER.
#
# https://github.com/PRImA-Research-Lab/PAGE-XML
# https://en.wikipedia.org/wiki/Inside%E2%80%93outside%E2%80%93beginning_(tagging)
#
# License: See LICENSE.txt.
#
# Willem Jan Faber (2021)
#


import os
import re

from lxml import etree
from pprint import pprint
from pathlib import Path

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
    ]
)


BASEDIR = './'

lookup = {'person': ['B-per', 'I-per'],
          'title_honours': ['B-per', 'I-per'],
          'place': ['B-loc', 'I-loc'],
          'organization': ['B-org', 'I-org'],
          'Austronesian': ['B-misc', 'I-misc'],
          'date': ['B-date', 'I-date'],
          'miscellaneous': ['B-misc', 'I-misc'],
          'denomination' : ['B-misc', 'I-misc'],
          'reference': ['B-misc', 'I-misc'],
          }



all_files = []

logging.info('Working from directory: %s' % Path().absolute())

for f in os.listdir(BASEDIR):
    if os.path.isdir(BASEDIR + os.sep + f + os.sep):
        for fn in os.listdir(BASEDIR + os.sep + f + os.sep):
            path = BASEDIR + os.sep + f + os.sep + fn
            if os.path.isdir(path + os.sep + 'page'):
                for ff in os.listdir(path + os.sep + 'page'):
                    all_files.append(path + os.sep + 'page' + os.sep + ff)

logging.info('Total nr of page files: %i' % len(all_files))

quit = False

for f in all_files:
    with open(f, 'rb') as fh:
        data = etree.fromstring(fh.read())

    wanted_tags = []
    prev_tag = ''
    for item in data.iter():
        if str(item.tag).endswith('TextLine'):
            # First we gather all the tag's that are used,
            # to later match them with the text-blocks.

            wanted_tags = []
            hint = str(item.attrib.get('custom')).strip()
            hi = re.sub('readingOrder {index:\d+;}', '', hint).strip()

            for i in hi.split(';} '):
                if not i.strip():
                    continue

                tag_info = i
                tag = tag_info.split(' ')[0]
                if tag in ['textStyle', 'structure']:
                    continue

                offset = int(tag_info.split('offset:')[1].split(';')[0])
                length = int(tag_info.split('length:')[1].split(';')[0])

                if tag == 'title_honours':
                    tag = 'person'
                if tag == 'Austronesian':
                    tag = 'person'


                logging.info('file: %s\ttag: %s\toffset: %i\tlen: %i', f, tag, offset, length)
                wanted_tags.append([tag, offset, length])


        txt_org = []

        continue_next = False

        if str(item.tag).endswith('Unicode'):
            if not item.text:
                continue

            # The '¬' sing indicates that a word continues on next line.
            for part in item.text.split():
                if part.strip():
                    if part.strip().endswith('¬'):
                        continue_next = True
                        txt_org.append(part.strip()[:-1])
                    else:
                        if not continue_next:
                            txt_org.append(part.strip())
                        else:
                            txt_org[-1] += part.strip()
                            continue_next = False

        if not wanted_tags:
            if txt_org:
                for p in txt_org:
                    prev_tag = 'O'
            continue

        if not txt_org:
            continue

        for wanted in wanted_tags:
            wanted_txt = item.text[wanted[1]: wanted[1] + wanted[2]]
            tag = wanted[0]
            done = False
            txt_tagged = []

            for word in txt_org:
                txt_tagged.append('O')

            for part in wanted_txt.split():
                for i, word in enumerate(txt_org):
                    part = "".join(l for l in part if l.isalpha()
                                   or l.isdigit()).strip()
                    word = "".join(l for l in word if l.isalpha()
                                   or l.isdigit()).strip()

                    if word == part:
                        txt_tagged[i] = tag
                        done = True
                        break

                if not done:
                    for i, word in enumerate(txt_org):
                        part = "".join(
                            l for l in part if l.isalpha() or l.isdigit()).strip()
                        word = "".join(
                            l for l in word if l.isalpha() or l.isdigit()).strip()

                        if word.find(part) > -1:
                            done = True
                            txt_tagged[i] = tag
                            break
            wanted_tags = []
        notag = 0

        for i, word in enumerate(txt_org):
            if txt_tagged[i] in lookup:
                j = 0
                if txt_tagged[i] == prev_tag:
                    j = 1
                print(word, lookup[txt_tagged[i]][j])
                #quit = True
                notag = 0
            else:
                # Skip all untagged parts.
                if notag < 20:
                    print(word, txt_tagged[i])
                    #quit = True
                notag += 1
            prev_tag = txt_tagged[i]
    if quit:
        break
