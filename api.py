from flask import Flask, request, jsonify
from flask_cors import CORS

from bert import Ner

app = Flask(__name__)
CORS(app)

model = Ner("out_base")


@app.route("/predict/", methods=['GET'])
def predict():
    text = request.args.get('text')
    if len(text) >= 512:
        return jsonify({"result": 'too large!'})
    # try:
    out = model.predict(text)
    return jsonify({"result": out})
    # except Exception as e:
    #    print(e)
    #    return jsonify({"result":"Model Failed"})


if __name__ == "__main__":
    app.run('0.0.0.0', port=8000)
