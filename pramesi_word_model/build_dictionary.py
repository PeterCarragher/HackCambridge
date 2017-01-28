#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ******************************************************************************
# Argon Design Ltd. Project P9000 Argon
#
# Module : pramesi_word_model
# Author : Steve Barlow
# $Id: build_dictionary.py 14770 2017-01-22 15:24:42Z sjb $
# ******************************************************************************

# Code from https://github.com/ppramesi/RoboTrumpDNN build_dictionary.py
# Major adaptions by SJB

import json
import gensim as gs

# For details of Gensim word2vec see:
# https://radimrehurek.com/gensim/models/word2vec.html 

# Load text and covert to lowercase
filename = 'input.json'
with open(filename, 'rt') as f:
    contributions = json.load(f)
text = ' '.join(contributions)

# Divide into sentences and separate punctuation so it becomes separate tokens
# Other special characters stay as part of words
text = text.lower()
text = text.replace('.', ' . <sentence-sep>')
text = text.replace('!', ' ! <sentence-sep>')
text = text.replace('?', ' ? <sentence-sep>')
text = text.replace(',', ' , ')
text = text.replace(u'\u201c', u' \u201c ') # Left double quote '“'
text = text.replace(u'\u201d', u' \u201d ') # Right double quote '”'

sentences = text.split('<sentence-sep>')
non_empty_sentences = filter(len, sentences)
parsedWords = [words.split() for words in non_empty_sentences]

mayModel = gs.models.Word2Vec(parsedWords, size=300, min_count=1, iter=10, window=8, sg=1, hs=0, negative=5)

mayModel.save('may2vec')
