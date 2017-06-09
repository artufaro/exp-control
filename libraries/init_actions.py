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

def action_list_init(action_list):

    acts_path = "data/actions"
    for (dirpath, dirnames, filenames) in os.walk(acts_path):
        for fname in filenames:
            fstart, fext = os.path.splitext(fname)
            if fext == ".py" and fstart != "__init__":
                module = imp.load_source(fstart, os.path.join(dirpath, fname))
                module.action_list_init(action_list)

"""
EXAMPLES for an arbitrary .py file in folder data/boards
see action module for details


import libraries.action as lib_action
import libraries.ramp as lib_ramp

def action_list_init(act_lst):

    #SIMPLE ACTION
    act_lst.add("BREAKPOINT",                   #action name, arbitrary but unique in the list
                lib_action.BreakpointAction,    #action type
                categories=["FPGA"],            #arbitrary action categories used to organize the list of actions
                comment="arbitrary comment")    #description of the action
                #categories are a list of string with the first string the root category

    #DDS ACTION
    act_lst.add("ACTION NAME",                      #action name
                lib_action.DdsAction,               #action type
                board="BOARD NAME",                 #name of the target boards
                parameters=dict(channel=1),         #parameters are action arguments internally fixed, that cannot be changed by user
                                                    #a dictionary with the action arguments as keys and relative values
                variables=dict(amplitude=0),        #parameters are action arguments that must be spcified by user
                                                    #format is the same of parameters (can be exchanged), the keys values represent the default values
                var_formats=dict(amplitude="%d"),   #arbitrary string format for the variables, how will be printed to the user
                categories=["actions", "dds"],      #action categories
                comment="arbitrary comment")        #description of the action

    #DDS ACTION (multiple variables)
    act_lst.add("ACTION NAME",
                lib_action.DdsAction,
                board="BOARD NAME",
                parameters=dict(channel=1),
                variables=dict(amplitude=0, frequency=0),   #if implemented, actions can have multiple varibles
                var_formats=dict(amplitude="%d", frequency="%.2f"),
                categories=["actions", "dds"],
                comment="arbitrary comment")

    #ANALOG ACTION
    act_lst.add("ACTION NAME",
                lib_action.AnalogAction,
                board="BOARD NAME",
                parameters=dict(),
                variables=dict(value=0),
                var_formats=dict(value="%.4f"),
                categories=["actions", "analog"],
                comment="arbitrary comment")

    #TTL ACTION (single, fixed)
    act_lst.add("ACTION NAME",
                lib_action.DigitalAction,
                board="BOARD NAME",
                parameters=dict(channel=[1], status=[True]),    #the parameters are a list of channels and a list of relative values
                                                                #True for ON, False for OFF
                categories=["actions", "TTL"],
                comment="arbitrary comment")

    #TTL ACTION (multiple, fixed)
    act_lst.add("ACTION NAME",
                lib_action.DigitalAction,
                board="BOARD NAME",
                parameters=dict(channel=range(1,17),    #for actions on multiple channels use the python list
                                status=[True]*16),      #eg, this initializes all 16 channels to ON)
                categories=["actions", "TTL"],
                comment="arbitrary comment")

    #TTL ACTION (multiple, variable)
    act_lst.add("ACTION NAME",
                lib_action.DigitalAction,
                board="BOARD NAME",
                parameters=dict(channel=[10,11]),
                variables=dict(status=[True,True]),     #also TTL can have user variables
                categories=["actions", "TTL"],
                comment="arbitrary comment")

    #RAMP
    act_lst.add("RAMP NAME",
                lib_ramp.LinearRamp,
                parameters=dict(act_name="ACTION NAME", act_var_name="amplitude"),  #ramps act on the varible act_var_name for action act_name
                variables=dict(start_x=0, stop_x=0, start_t=0, stop_t=0, n_points=0),
                var_formats=dict(start_x="%.3f", stop_x="%.3f", start_t="%.4f", stop_t="%.4f", n_points="%d"),
                categories=["ramps"],
                comment="arbitrary comment")
"""
