#!/usr/bin/env python3

from flask import Flask, request, jsonify
from flask_cors import CORS

from bert import Ner

app = Flask(__name__)
CORS(app)

model = Ner("out_base")


#@app.route("/predict/", methods=['GET'])
def predict():
    text = request.args.get('text')
    if len(text) >= 512:
        return jsonify({"result": 'too large!'})
    # try:
    out = model.predict(text)
    text_parsed = ""

    result = []
    
    ne = ""
    for r in out:
        text_parsed += r.get('word') + ' '
        if r.get('tag') != 'O':
            p_tag = r.get('tag')
            ne += r.get('word') + ' '

            lookup_type = p_tag
        else:
            if p_tag != 'O':
                if not ne.strip() in [ne.get('ne') for ne in result]:
                    pos = text_parsed.find(ne.strip())
                    result.append({'ne': ne.strip(), 'type': lookup_type, 'pos' : pos})
                    p_tag = 'O'

    #from pprint import pprint
    #pprint(result)

    return jsonify({"result": out})


if __name__ == "__main__":
    app.run('0.0.0.0', port=8000)
