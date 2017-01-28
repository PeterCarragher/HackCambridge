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
import re
app = Flask(__name__)
ask = Ask(app, '/')

welcome_text  = "Lets start a new story."\
                "Once upon a time, in a land far far away "

reprompt_text = "What happens next?"

goodbye_text  = "And they all lived happily ever after. The end."

names = {}

rand_names = set()

@ask.launch
def welcome():
    return question(welcome_text).reprompt(reprompt_text).simple_card('Welcome', welcome_text)

@ask.intent('CompleteSentenceIntent')
def hello(InitialWords):

    #update names with new names
    tagged_sent = pos_tag(InitialWords.split())
    [names.append(word) for word, pos in tagged_sent if pos == 'NNP' and word not in names]

    #substitute place holders into initialwords
    for name, pos in tagged_sent:
        if pos == 'NNP':
            InitialWords = re.sub(name, "person_"+str(names.index(name)), InitialWords)

    if InitialWords is None:
        InitialWords = ''
    speech_output = create_sentence(InitialWords, seed=0, diversity=0.0)
    return question(speech_output).reprompt(reprompt_text).simple_card('CompleteSentenceIntent', speech_output)

@ask.session_ended
def goodbye():
    return statement(goodbye_text).simple_card('Session Ended', goodbye_text)

if __name__ == '__main__':
    app.run(debug=False)
