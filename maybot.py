#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ******************************************************************************
# Argon Design Ltd. Project P9000 Argon
# (c) Copyright 2017 Argon Design Ltd. All rights reserved.
#
# Module : maybot
# Author : Steve Barlow
# $Id: maybot.py 14794 2017-01-24 22:23:41Z sjb $
# ******************************************************************************

"""Skill for Amazon Alexa that completes sentences in the style of Theresa May.

Maybot is a skill for Amazon Alexa that completes sentences in the style of
Theresa May's parliamentary spoken contributions scraped from Hansard from given
starting words. This code forms a web server which responds to JSON service
requests from Alexa and returns a JSON response with the text to be spoken.
"""

from __future__ import print_function
from flask import Flask, render_template
from flask_ask import Ask, question, statement
from pramesi_word_model.create_sentence import create_sentence
from nltk.tag import pos_tag
from nltk.corpus import names
import re
import random
app = Flask(__name__)
ask = Ask(app, '/')

welcome_text  = "Lets start a new story. Once upon a time, in a land far far away "

reprompt_text = "What happens next?"

goodbye_text  = "And they all lived happily ever after. The end."

userNames = []

rand_names = [name.lower() for name in names.words("male.txt")] + [name.lower() for name in names.words("female.txt")]
rand_names.append("andreea")
random.shuffle(rand_names)

lastOutput = welcome_text

def findnth(haystack, needle, n):
    parts= haystack.split(needle, n+1)
    if len(parts)<=n+1:
        return -1
    return len(haystack)-len(parts[-1])-len(needle)

@ask.launch
def welcome():
    return question(welcome_text).reprompt(reprompt_text).simple_card('Welcome', welcome_text)

@ask.intent('CompleteSentenceIntent')
def hello(InitialWords):
    global lastOutput

    if InitialWords is None:
        if len(lastOutput) > 12:
            InitialWords = lastOutput.split()[-12:]
            speech_output = create_sentence(InitialWords, seed=0, diversity=0.0)
            lastOutput = speech_output
            return question(speech_output).reprompt(reprompt_text).simple_card('CompleteSentenceIntent', speech_output)

    print("heard: " + InitialWords)

    # update names with new names
    tagged_sent = pos_tag(InitialWords.split())
    [userNames.append(word) for word, pos in tagged_sent if pos == 'NNP' and word not in userNames]

    #substitute place holders into initialwords
    for name, pos in tagged_sent:
        if pos == 'NNP':
            InitialWords = re.sub(name, "person_"+str(userNames.index(name)), InitialWords)

    space = " "

    #add 12-givenWords from lastOutput to InitialWords
    if len(InitialWords.split())<12:
        lastList = lastOutput.split()
        numWordsNeeded = 12 - len(InitialWords.split())
        listNeeded = lastList[-numWordsNeeded:]
        InitialWords = space.join(listNeeded) + " " + InitialWords
    else:
        InitialWords = InitialWords[-12:]

    print("sending: " + InitialWords)

    speech_output = create_sentence("forget " + InitialWords, seed=0, diversity=0.0)

    print("recieved: "+speech_output)

    #find last word from input to remove input from output
    lastInitialWord = InitialWords.split()[-1]
    lastIter = speech_output.find(lastInitialWord)

    #if last word of input found, remove all input from output
    if lastIter > 0:
        speech_output = speech_output[lastIter+len(lastInitialWord)+1:]

    print("wo last input: "+speech_output)

    #find fullstop
    fullstops = speech_output.find(".")
    numWordsToFullStop = -1
    if fullstops > 0:
        numWordsToFullStop = len((speech_output[:fullstops]).split())

    maxLen = 20

    #if fullstop found, remove everything after
    if numWordsToFullStop > 0 and numWordsToFullStop < 5:
        #continue to second full stop
        secondStop = findnth(speech_output, ".", 2)
        numWordsToSecondStop = -1
        if secondStop > 0:
            numWordsToSecondStop = len((speech_output[:secondStop]).split())
        if numWordsToSecondStop > 0 and numWordsToSecondStop < 20:
            speech_output = speech_output[:secondStop]
    elif numWordsToFullStop < maxLen:
        speech_output = speech_output[:fullstops]

    print("fullstop: "+speech_output)


    if len(speech_output) > maxLen: # set limit output to 20 words
        speech_output = space.join(speech_output.split()[:maxLen])

    print("capped: "+speech_output)

    #substitute names back into speech_output
    iters = map(int, re.findall("person_(\d+)", speech_output))
    for iter in iters:
        name = ""
        if iter<len(userNames):
            name = userNames[iter]
        else:
            name = rand_names[iter-len(userNames)]

        speech_output = re.sub("person_"+str(iter), name, speech_output)

    #save last output for next iteration
    lastOutput = speech_output

    print("saying: " + speech_output)

    return question(speech_output).reprompt(reprompt_text).simple_card('CompleteSentenceIntent', speech_output)

@ask.session_ended
def goodbye():
    return statement(goodbye_text).simple_card('Session Ended', goodbye_text)

if __name__ == '__main__':
    app.run(debug=False)
