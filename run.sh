#!/bin/bash
# ******************************************************************************
# Argon Design Ltd. Project P9000 Argon
# (c) Copyright 2017 Argon Design Ltd. All rights reserved.
#
# Module : maybot
# Author : Steve Barlow
# $Id: run.sh 14714 2017-01-17 17:11:13Z sjb $
# ******************************************************************************

# run.sh - Start local server

# Opens two terminal windows - one for web server and one for ngrok
gnome-terminal -x ./maybot.py
gnome-terminal -x ./ngrok http 5000
