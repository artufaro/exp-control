#!/usr/bin/python2
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 24 13:35:47 2015
@author: Simone Donadello
"""

import shutil, os

#move all user data in the "data" folder
if os.path.exists("data") and os.path.exists("programs") and os.path.exists("definitions"):
    shutil.rmtree("data")
    print "deleted data"
if os.path.exists("programs"):
    shutil.move("programs", "data/programs")
    print "moved programs"
if os.path.exists("definitions/actions"):
    shutil.move("definitions/actions", "data/actions")
    print "moved definitions/actions"
if os.path.exists("definitions/boards"):
    shutil.move("definitions/boards", "data/boards")
    print "moved definitions/boards"
if os.path.exists("definitions"):
    shutil.rmtree("definitions")
    print "deleted definitions"
if os.path.exists(".program.conf"):
    shutil.move(".program.conf", "data")
    print "moved .program.conf"
os.mknod("data/.gitkeep")
