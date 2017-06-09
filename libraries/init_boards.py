#!/usr/bin/python2
# -*- coding: utf-8 -*-

# Copyright (C) 2015-2016  Simone Donadello
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, imp

def board_list_init(board_list):

    boards_path = "data/boards"
    for (dirpath, dirnames, filenames) in os.walk(boards_path):
        for fname in filenames:
            fstart, fext = os.path.splitext(fname)
            if fext == ".py" and fstart != "__init__":
                module = imp.load_source(fstart, os.path.join(dirpath, fname))
                module.board_list_init(board_list)

"""
EXAMPLES for an arbitrary .py file in folder data/boards
see board module for details


import libraries.board as lib_board

def board_list_init(board_lst):

    #DDS BOARD
    board_lst.add("BOARD NAME",             #BOARD NAME is arbitrary but must be unique in the list (eg DDS32)
                  lib_board.DdsBoard,       #board type
                  address=33,               #hardware address
                  parameters=dict(amp_to_lut={1: lambda x: x, 2: lambda x: x,
                                  freq_to_lut={1: lambda x: x, 2: lambda x: x),
                  comment="arbitrary board description")
                  #Parameters for DDS boards are composed of a dictionary with two elements:
                  #the encoders for DDS amplitude converted into LUT number (amp_to_lut),
                  #and encoders for for DDS frequency converted into LUT number (freq_to_lut).
                  #Each group of encoders is a dictionary, with the numbers of the DDS channels as keys,
                  #and lambda functions mapping the relative values to LUT numbers.
                  #Be careful with divisions in python.

    #TTL BOARD
    board_lst.add("BOARD NAME",
                  lib_board.DigitalBoard,
                  address=33,
                  comment="arbitrary board description")

    #ANALOG BOARD
    board_lst.add("BOARD NAME",
                  lib_board.AnalogBoard,
                  address=33,
                  parameters=dict(ang_to_dig={1: lambda x: x}),
                  comment="arbitrary board description")
                  #Parameters for Analog boards are similar to the DDS boards
                  #with a key ang_to_dig mapping the input values to the DAC range.
"""
