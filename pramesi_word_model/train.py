#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ******************************************************************************
# Argon Design Ltd. Project P9000 Argon
#
# Module : pramesi_word_model
# Author : Steve Barlow
# $Id: train.py 14812 2017-01-26 13:52:59Z sjb $
# ******************************************************************************

# Code from https://github.com/ppramesi/RoboTrumpDNN trumpbot.py
# Major adaptions by SJB

"""Example script to generate text from Theresa May's spoken
contributions in parliament.

At least 20 epochs are required before the generated text
starts sounding coherent.

It is recommended to run this script on GPU, as recurrent
networks are quite computationally intensive.

If you try this script on new data, make sure your corpus
has at least ~100k characters. ~1M is better.
"""

from __future__ import print_function
from keras.models import Model, load_model
from keras.layers import Input, Dense, Activation, Dropout, TimeDistributed, ELU, LSTM, BatchNormalization, merge
from keras.optimizers import RMSprop
import json
import pickle
import gensim as gs
import numpy as np
import os
import sys

vmodel = gs.models.Word2Vec.load('may2vec')

# Load text
filename = 'input.json'
with open(filename, 'rt') as f:
    contributions = json.load(f)
text = ' '.join(contributions)

# !!! Shorten text for faster training - break at space
text = text[:50000].rpartition(' ')[0]

def prepare_text(text):
    # Helper function to take input text and prepare it into tokenised words to be used with model
    text = text.lower()
    # Separate punctuation so it becomes separate tokens
    text = text.replace('.', ' . ')
    text = text.replace('!', ' ! ')
    text = text.replace('?', ' ? ')
    text = text.replace(',', ' , ')
    text = text.replace(u'\u201c', u' \u201c ') # Left double quote '“'
    text = text.replace(u'\u201d', u' \u201d ') # Right double quote '”'
    parsedWords = text.split()
    return parsedWords

print('Vectorisation...')
parsedWords = prepare_text(text)
wordCoding = {}
codedWord = {}
codeNum = 0
for word in parsedWords:
    if not word in wordCoding:
        wordCoding[word] = codeNum
        codedWord[codeNum] = word
        codeNum += 1
print('Corpus length in words:', len(parsedWords))
print('Distinct words:', len(wordCoding))

codeTables = (wordCoding, codedWord)
with open('codetables.pickle', 'wb') as f:
    pickle.dump(codeTables, f)

input_dim = len(vmodel['.']) # Length of word vector - nominally 300
lstm_hdim = 500
dense_dim = 1500

sd_len = 12

sd_size = len(parsedWords) // sd_len

batch_size = 256

i_D = []
x_D = []
y_D = []

def one_hot(index):
    retVal = np.zeros((len(wordCoding)), dtype=np.bool)
    retVal[index] = 1
    return retVal

for idx in range(sd_size-1):
    for iidx in range(sd_len):
        input_words = parsedWords[idx * sd_len + iidx:(idx + 1) * sd_len + iidx]
        output_word = parsedWords[(idx + 1) * sd_len + iidx]
        i_D.append([wordCoding[w] for w in input_words])
        x_D.append([vmodel[w] for w in input_words])
        y_D.append(one_hot(wordCoding[output_word]))

i_D = np.asarray(i_D)
x_D = np.asarray(x_D)
y_D = np.asarray(y_D)

print('x_D shape:', str((x_D.shape)))
print('y_D shape:', str((y_D.shape)))

# Build the model: 2 stacked LSTMs

print('Build model...')
input = Input(shape=(sd_len, input_dim))
tdd1 = Dense(lstm_hdim)(input)
bn1 = BatchNormalization()(tdd1)

lstm1_left = LSTM(lstm_hdim, return_sequences=True)(bn1)
bn2_left = BatchNormalization()(lstm1_left)

lstm1_right = LSTM(lstm_hdim, return_sequences=True, go_backwards=True)(bn1)
bn2_right = BatchNormalization()(lstm1_right)

lstm3_left = LSTM(lstm_hdim, return_sequences=False)(bn2_left)
lstm3_right = LSTM(lstm_hdim, return_sequences=False, go_backwards=True)(bn2_right)

lstm4_left = LSTM(lstm_hdim, return_sequences=False)(lstm3_left)
lstm4_right = LSTM(lstm_hdim, return_sequences=False, go_backwards=True)(lstm3_right)

merge1 = merge([lstm4_left, lstm4_right], mode='concat')
bn4 = BatchNormalization()(merge1)
dropout1 = Dropout(0.2)(bn4)

dense1 = Dense(dense_dim)(dropout1)
denseelu1 = ELU()(dense1)
dropout2 = Dropout(0.2)(denseelu1)

dense2 = Dense(len(wordCoding))(dropout2)
output = Activation('softmax')(dense2)

model = Model(input=input, output=output)
model.summary()

optimiser = RMSprop(lr=0.0001)
model.compile(optimiser, loss='categorical_crossentropy')

# Train the model, output generated text after each iteration

def sample(a, temperature=1.0):
    # Helper function to sample an index from a probability array
    if temperature == 0.0:
        return np.argmax(a)
    np.random.random() # Make sure RNG initialised consistently
    a = np.clip(a, 1E-20, 1.0) # Make sure we don't have any zeros
    a = np.exp(np.log(a) / temperature)
    a = a / np.sum(a)
    a = a * 0.999999 # Added to fix sum(pvals[:-1]) > 1.0 error
    return np.argmax(np.random.multinomial(1, a, 1))

def get_sentence(wcodedVec):
    result = ''
    for i,wcode in enumerate(wcodedVec):
        word = codedWord[wcode]
        if i != 0 and word not in ['.', '!', '?', ',', u'\u201d']:
            result += ' '
        result += word
    return result

# Load weights from existing model if there is one
if os.path.isfile('trained_model.h5'):
    temp_model = load_model('trained_model.h5')
    temp_model.save_weights('tb-weights')
    model.load_weights('tb-weights')
    os.remove('tb-weights')

for iteration in range(0, 50):
    print()
    print('-' * 50)
    model.fit(x_D, y_D, batch_size=batch_size, nb_epoch=10)
    print('Saving trained model')
    model.save('trained_model.h5')

    preds = model.predict(x_D[:5000], verbose=0)
    train_accuracy = np.mean(np.equal(np.argmax(y_D[:5000], axis=-1), np.argmax(preds[:5000], axis=-1)))
    print('Training accuracy =', train_accuracy)

    # !!! Save model snapshots in case training falls off
    model.save('trained_model_{0:02d}_{1:.4f}.h5'.format(iteration, train_accuracy))

    seedSrc = i_D
    seed_index = np.random.randint(0, len(seedSrc) - 1)

    print()
    for diversity in [0.0, 0.25, 0.5]:
        print('----- diversity:', diversity)

        sentence = seedSrc[seed_index]
        strSentence = get_sentence(sentence)
        print('----- Generating with seed: "' + strSentence + '"')

        for iteration in range(100):
            vecsentence = []
            for wcode in sentence:
                vecsentence.append(vmodel[codedWord[wcode]])
            vecsentence = np.reshape(vecsentence, (1, sd_len, input_dim))
            preds = model.predict(vecsentence, verbose=0)[0]
            next_wcode = sample(preds, diversity)
            next_word = codedWord[next_wcode]
            
            sentence = np.append(sentence[1:], next_wcode)
            if iteration != 0 and next_word not in ['.', '!', '?', ',', u'\u201d']:
                sys.stdout.write(' ')
            sys.stdout.write(next_word)
            sys.stdout.flush()
        print()
