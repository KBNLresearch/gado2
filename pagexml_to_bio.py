#!/usr/bin/env python3

"""
pagexml_to_bio
pagexml2bio

Reformats page.xml output from https://transkribus.eu/lite/ to .bio format,
used as input for training NER engines. This enables adding custom tags to your dataset.
The static variable LOOKUP is used to reformat the tags to the output format.

For more info:
    ./pagexml2bio --help
"""

__author__ = "Willem Jan Faber."
__copyright__ = "Copyright 2021, KB"
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Willem Jan Faber"
__email__ = "willemjan.faber@kb.nl"
__status__ = "Production"

import argparse
import os
import sys

import nltk

from lxml import etree
from pprint import pprint

from page_example import page_example

DEBUG = False

NS_TL = ".//{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextLine"
NS_UC = ".//{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Unicode"

WANTED_TAGS = ["date", "denomination", "organization", "person", "place"]

LOOKUP = {
    "person": ["B-per", "I-per"],
    "title_honours": ["B-per", "I-per"],
    "place": ["B-loc", "I-loc"],
    "organization": ["B-org", "I-org"],
    "Austronesian": ["B-misc", "I-misc"],
    "date": ["B-date", "I-date"],
    "miscellaneous": ["B-misc", "I-misc"],
    "denomination": ["B-misc", "I-misc"],
    "reference": ["B-misc", "I-misc"],
}


def get_tags(tag_info: str) -> list:
    """
    >>> a = []
    >>> a.append('readingOrder {index:0;')
    >>> a.append('structure {type:header')
    >>> a.append('organization {offset:8; length:10;')
    >>> a.append('person {offset:31; length:14;firstname:Karel; lastname:Hartsinck;')
    >>> a.append('date {offset:54; length:12;year:0; day:0; month:0;}')
    >>> get_tags(a)
    [['organization', [8, 18]], ['person', [31, 45]], ['date', [54, 66]]]
    """
    global WANTED_TAGS

    tags = []
    for tag in tag_info:
        tagname = tag.split(" ")[0]
        pos = []
        if tagname in WANTED_TAGS:
            tags.append([tagname])
            for item in tag.split(":"):
                for p in item.split(";"):
                    if p.isalnum() and len(pos) < 1:
                        pos.append(int(p))
                    elif p.isalnum() and len(pos) < 2:
                        pos.append(pos[0] + int(p))

            tags[-1].append(pos)
    return tags


def to_bio(tags: list, text: str, old_tags: list, old_text: str, combine: bool) -> list:
    """
    >>> tags = []
    >>> tags.append(['person', [0, 12]])
    >>> text ='W:Hartsinck.'
    >>> to_bio(tags, text, old_tags=[], old_text='', combine=False)
    [(False, [['W', 'person'], [':', 'person'], ['Hartsinck', 'person'], ['.', 'person']], 'W:Hartsinck.', [['person', [0, 12]]])]
    >>> old_text = 'E.E. hier gecomen en gecommitteert waren omme denselven daartoe opent¬'
    >>> text = 'lijck te installeren ende de Chinese ingesetenen deswegen publijcque kennisse'
    >>> old_tags = [['organization', [0, 4]]]
    >>> tags = [['denomination', [29, 48]]]
    >>> to_bio(tags, text, old_tags, old_text, combine=True)[0][1]
    [['E.E.', 'organization'], ['hier', 'O'], ['gecomen', 'O'], ['en', 'O'], ['gecommitteert', 'O'], ['waren', 'O'], ['omme', 'O'], ['denselven', 'O'], ['daartoe', 'O'], ['opentlijck', 'O'], ['te', 'O'], ['installeren', 'O'], ['ende', 'O'], ['de', 'O'], ['Chinese', 'denomination'], ['ingesetenen', 'denomination'], ['deswegen', 'O'], ['publijcque', 'O'], ['kennisse', 'O']]
    """

    text_tokens = nltk.tokenize.word_tokenize(
        text, language="dutch", preserve_line=True
    )

    res_tokens = [[token, "O"] for token in text_tokens]

    if combine:
        if tags:
            for tag in tags:
                tag[1][0] += len(old_text) - 1
                tag[1][1] += len(old_text) - 1
        if old_tags:
            tags = old_tags + tags
        text = old_text[:-1] + text
        text_tokens = nltk.tokenize.word_tokenize(
            text, language="dutch", preserve_line=True
        )
        res_tokens = [[token, "O"] for token in text_tokens]

    combine = False

    for token in res_tokens:
        if token[0].endswith("¬"):
            combine = True

    for tag in tags:
        tag_str = text[tag[1][0]:tag[1][1]]
        tag_tokens = nltk.tokenize.word_tokenize(
            tag_str + " ", language="dutch", preserve_line=True
        )

        found = False

        for pos in range(0, len(text_tokens)):
            txt_match = text_tokens[pos:pos + len(tag_tokens)]
            if txt_match == tag_tokens:
                found = True
                break

        if not found:
            tag_tokens = tag_str.split()

            for pos in range(0, len(text_tokens)):
                txt_match = text_tokens[pos:pos + len(tag_tokens)]
                if txt_match == tag_tokens:
                    found = True
                    break
        if found:
            for word_num, word in enumerate(res_tokens):
                if word_num in range(pos, pos + len(tag_tokens)):
                    res_tokens[word_num][1] = tag[0]
    return [(combine, res_tokens, text, tags)]


def parse_page_file(
    data: etree._Element,
    fname: str,
    stats: dict = {
        "known_tokens": set(),
        "sentence_count": 0,
        "tokens": 0,
        "tokens_with_tag": 0,
        "tokens_without_tag": 0,
        "files": [],
    },
) -> tuple:
    """
    >>> data = etree.fromstring(page_example.encode('utf-8'))
    >>> sorted(parse_page_file(data, '_builtin_page_example')[1].get('known_tokens'))
    ['organization', 'person', 'place']
    >>> a=[i for i,j in parse_page_file(data, '_builtin_page_example')[0][0]]
    >>> " ".join(a)
    "Pyrotechnia of konst i n't vuurwercken Geschreven op 't Schip 't Huijs Ter Loo door mijn Daniel Galschut van Koppenhaggen"
    """
    combine = False
    prev_tags = []
    prev_text = ""
    output = []
    output_lines = []

    nr_of_tokens = 0
    nr_of_tokens_without_tag = 0
    nr_of_tokens_with_tag = 0
    nr_of_newlines = 0

    stats["files"].append(fname)

    sent = ""

    for line in zip(data.findall(NS_TL), data.findall(NS_UC)):
        tags = line[0].attrib.get("custom").split("} ")
        tags = get_tags(tags)
        text = line[1].text

        if not text:
            continue

        sent += text + " "

        for (i, j, prev_text, prev_tags) in to_bio(
            tags, text, prev_tags, prev_text, combine
        ):
            if i:
                combine = True
            else:
                for i in j:
                    nr_of_tokens += 1
                    if i[0] == "." and i[1] == "O":
                        output.append((i[0], i[1]))
                        output_lines.append(output)
                        nr_of_newlines += 1
                        output = []
                    else:
                        output.append((i[0], i[1]))
                        if i[1] == "O":
                            nr_of_tokens_without_tag += 1
                        else:
                            nr_of_tokens_with_tag += 1
                            if not i[1] in stats["known_tokens"]:
                                stats["known_tokens"].add(i[1])
                combine = False

    if output not in output_lines:
        output_lines.append(output)

    stats["sentence_count"] += nr_of_newlines
    stats["tokens"] += nr_of_tokens
    stats["tokens_without_tag"] += nr_of_tokens_without_tag
    stats["tokens_with_tag"] += nr_of_tokens_with_tag

    return (output_lines, stats)


def main(dirname: str, outfilename: str = "output.bio"):
    if not os.path.isdir(dirname):
        print(f"Error: {sys.argv[-1]} is not a directory, aborting.")
        sys.exit(-1)

    if os.path.isfile(outfilename):
        print(f"Remove {outfilename}? y/n")
        response = input()

        if response == "y":
            os.unlink(outfilename)

    stats = {}

    for f in os.listdir(dirname):
        if not f.endswith(".xml"):
            continue

        fname = dirname + os.sep + f
        if DEBUG:
            print(f"Parsing {fname}")

        with open(fname, "rb") as fh:
            data = etree.parse(fh)

        if stats:
            output, stats = parse_page_file(data, fname, stats)
        else:
            output, stats = parse_page_file(data, fname)

        stats["sentence_count"] += 1

        with open(outfilename, "a") as fh:
            for i in range(len(output)):
                prev_tag = ""
                ent = 0
                for j, k in output[i]:
                    if not k == "O":
                        ent += 1
                if ent:
                    for j, k in output[i]:
                        if k in LOOKUP:
                            if prev_tag == k:
                                fh.write(f"{j} {LOOKUP.get(k)[1]}\n")
                            else:
                                fh.write(f"{j} {LOOKUP.get(k)[0]}\n")
                        else:
                            fh.write(f"{j} {k}\n")
                        prev_tag = k

                    fh.write("\n")

        if DEBUG:
            pprint(stats)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--page_dir",
        default=None,
        type=str,
        required=False,
        help="The input data dir. Should contain the page.xml files. (https://readcoop.eu/transkribus/docu/rest-api/)",
    )
    parser.add_argument(
        "--debug", default=False, type=int, required=False, help="Debug level."
    )
    parser.add_argument(
        "--output_filename",
        default="output.bio",
        type=str,
        required=False,
        help="The output filename where the converted page files will be written as bio file.",
    )
    parser.add_argument(
        "--test_code",
        required=False,
        action="store_true",
        help="Test the python code, can be used with -v.",
    )

    parser.add_argument(
        "-v", required=False, action="store_true", help="Can be used with --test_code."
    )

    args = parser.parse_args()

    if args.debug:
        DEBUG = args.debug

    if args.test_code:
        import doctest

        doctest.testmod()
    elif args.page_dir:
        if args.output_filename:
            main(args.page_dir, args.output_filename)
        else:
            main(args.page_dir)
    else:
        parser.print_help()
