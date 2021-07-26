#!/usr/bin/env python3

import os
import json
import syntok.segmenter as segmenter

from flask import Flask, request, make_response
from flask_cors import CORS
from bert import Ner

app = Flask(__name__)
CORS(app)

model = Ner("out_base")

BASEPATH = '/root/data/'

papers = {}

lookup = {'I-per': 'person',
          'B-per:': 'person',
          'I-loc': 'location',
          'B-loc': 'location',
          'B-misc': 'other',
          'I-misc': 'other'}

for f in os.listdir(BASEPATH):
    if os.path.isdir(BASEPATH + f):
        for paper in os.listdir(BASEPATH + f):
            papers[paper] = BASEPATH + f


def parse_document(document):
    output = []
    for paragraph in segmenter.process(document.replace('\n', ' ')):
        sentences = []
        for sentence in paragraph:
            txt = ''
            for token in sentence:
                txt += token.value + ' '

            for paragraph in segmenter.process(txt):
                txt = ''
                for sentence in paragraph:
                    for token in sentence:
                        if (token.value == '-' or token.value == '¬'):
                            if token.value == '-':
                                txt += '-'
                            elif token.value == '¬':
                                txt = txt.strip()
                                reparse = True
                        else:
                            txt += token.value + ' '


                tags = []
                txt_tags = []
                for item in model.predict(txt):
                    tags.append(item.get('tag'))
                    txt_tags.append(item.get('word'))
                sentences.append((txt_tags, tags))
        output.append(sentences)
    return(output)



@app.route("/predict/", methods=['GET'])
def predict():
    text = request.args.get('text')
    to_parse = set()
    if text in papers:
        for f in os.listdir(papers[text] + os.sep + text):
            if os.path.isdir(papers[text] + os.sep + text + os.sep + f):
                for l in os.listdir(papers[text] + os.sep + text + os.sep + f + os.sep + 'txt'):
                    to_parse.add(papers[text] + os.sep + text +
                                 os.sep + f + os.sep + 'txt' + os.sep + l)

        out = {}
        for f in to_parse:
            with open(f, 'r') as fh:
                text = fh.read()
                out[f] = parse_document(text)
        response = make_response(json.dumps(out))
        response.headers['content-type'] = 'application/json'
        return response
    return ('')


if __name__ == '__main__':
    app.run('0.0.0.0', port=8000)
