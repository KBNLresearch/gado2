What is this?
===

This a fork of: https://github.com/kamalkraj/BERT-NER

It contains some local modifications to run it on a different set of NER-classes.

The data/train.txt is a combination of Conll-2002 and input from various Indonesian / Dutch newspapers,
this is not the final set used for evaluation, more info soon..

The transformer used to make trainng-files from (Prima) page-xml is also included (pagexml_to_bio.py).
In this project we used export pagexml files from: https://transkribus.eu/.

Trained models are available here: https://huggingface.co/willemjan/


Training using page files.
===
Remove old training data and model:

``
$ rm data/train.txt # Remove old training data.
``

``
$ rm -rf out_base # Remove old trained model.
``

The page files are an output format by: https://readcoop.eu/transkribus/

Convert the page-files to the bio format using the following command:

``
$ ./pagexml_to_bio.py --page_dir <<Path to Pagefiles dir>> --output_filename data/train.txt --debug 1
``

Insert GPU and run:

``
$ ./train.sh
``

The model will be outputed in the directory 'out_base'.  

Running HTTP API.
===
The trained model can be used by running: ./api.py

This creates a listening port which can be queried like so:

``
$ curl -s 'http://localhost:8000/predict/?text=Willem jan is een liefhebber van Gado-gado.&model=nl2'
``

```
{
  "result": [
    {
      "confidence": 0.9999511241912842,
      "tag": "B-per",
      "word": "Willem"
    },
    {
      "confidence": 0.9999241828918457,
      "tag": "I-per",
      "word": "jan"
    },
    {
      "confidence": 0.9999983310699463,
      "tag": "O",
      "word": "is"
    },
    {
      "confidence": 0.9999984502792358,
      "tag": "O",
      "word": "een"
    },
    {
      "confidence": 0.9999983310699463,
      "tag": "O",
      "word": "liefhebber"
    },
    {
      "confidence": 0.9999983310699463,
      "tag": "O",
      "word": "van"
    },
    {
      "confidence": 0.9998682737350464,
      "tag": "B-misc",
      "word": "Gado-gado"
    },
    {
      "confidence": 0.9999983310699463,
      "tag": "O",
      "word": "."
    }
  ]
}
```
