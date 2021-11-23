#!/usr/bin/env bash

wget https://www.clips.uantwerpen.be/conll2002/ner/data/ned.train
wget https://www.clips.uantwerpen.be/conll2002/ner/data/ned.testa
wget https://www.clips.uantwerpen.be/conll2002/ner/data/ned.testb

recode l1..u8 ned.train
recode l1..u8 ned.testa
recode l1..u8 ned.testb

./convert.py ned.train > train.txt
./convert.py ned.testa >> test.txt
./convert.py ned.testb > valid.txt
