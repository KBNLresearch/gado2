#!/usr/bin/env python3

from flask import Flask, request, jsonify
from flask_cors import CORS

from bert import Ner

app = Flask(__name__)
CORS(app)


models = {"nl1": Ner("models/nl1"),
          "nl2": Ner("models/nl2"),
          "indo1": Ner("models/indo1"),
          "indo2": Ner("models/indo2"),
          "spa2": Ner("models/spa2"),
          "en2": Ner("models/en2")}



@app.route("/predict/", methods=['GET'])
def predict():
    text = request.args.get('text')
    model = request.args.get('model')
    if len(text) >= 512:
        return jsonify({"result": 'too large!'})
    if model in models:
        model = models.get(model)
    else:
        model = models.get('nl1')

    # try:
    out = model.predict(text)
    text_parsed = ""

    result = []
    
    ne = ""
    p_tag = ''
    lookup_type = ''
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
