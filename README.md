This a fork of: https://github.com/kyzhouhzau/BERT-NER

It contains some local modifications to run it on the Surf-Sara research cloud,

the data/train.txt is a combination of Conll-2003 and input from various Indonesian / Dutch newspapers.

Also a pre-trained model exists in ./out_base/, this can be used with api.py to start a NER-server on localhost:8080.

The transformer used to make trainng-files from (Prima) page-xml is also included (page_to_bio.py).
