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

#pylint: disable-msg=E1101

import action as lib_action
import program as lib_program
import board as lib_board
import system as lib_system
import ramp as lib_ramp

class ActionList(object):
    def __init__(self, system=None):
        self.actions = dict()
        self.programs = dict()
        self.ramps = dict()

        if not isinstance(system, lib_system.System):
            print "WARNING: wrong call to action list class (\"%s\" given instead of \"%s\")"%(str(type(system)), str(lib_system.System))
        self.system = system

    def tot_list(self):
        return dict(self.actions.items() + self.programs.items() + self.ramps.items())

    def get(self, action_name, *args, **kwargs):
        if action_name in self.actions.keys()+self.ramps.keys():
            return self.tot_list()[action_name]["call"](*args, **kwargs)
        elif action_name in self.programs.keys():
            cmd = self.system.cmd_thread
            return self.tot_list()[action_name]["call"]\
                    (lib_program.Program(self.system, action_name), cmd, *args, **kwargs)
        else:
            print "ERROR: action \"%s\" not found"%action_name
            return None

    def get_cmd(self, action_name):
        cmd = self.system.cmd_thread
        if action_name in self.programs.keys():
            act_cmd = self.tot_list()[action_name]["cmd"]
            if act_cmd is not None:
                return act_cmd(cmd)
            else:
                return None
        else:
            return None

    def is_program(self, action_name):
        return self.programs.has_key(action_name)

    def is_action(self, action_name):
        return self.actions.has_key(action_name)

    def is_ramp(self, action_name):
        return self.ramps.has_key(action_name)

    def get_dict(self, action_name):
        if action_name in self.tot_list().keys():
            new_dict = self.tot_list()[action_name].copy()
            del new_dict["call"]
            new_dict["vars"] = new_dict["vars"].copy()
            new_dict["pars"] = new_dict["pars"].copy()
            new_dict["functions"] = new_dict["functions"].copy()
            if new_dict["board"] is not None:
                new_dict["board"] = new_dict["board"].name
            else:
                new_dict["board"] = ""
            return new_dict
        else:
            return None

    def get_vars(self, action_name):
        return self.tot_list()[action_name]["vars"]

    def get_pars(self, action_name):
        return self.tot_list()[action_name]["pars"]

    def add(self, action_name, action,
            board=None, parameters=None, variables=None, var_formats=None,
            handler=None, categories=None, commands=None, comment=""):
        action_name = str(action_name)
        if self.actions.has_key(action_name) or self.programs.has_key(action_name):
            print "ERROR: action \"" + action_name + "\" is already defined"
            return
        else:
            if board is not None:
                board = self.system.board_list.get(board)
            if categories is None:
                categories = tuple()
            if parameters is None:
                parameters = dict()
            if type(parameters) != dict:
                parameters = dict()
                print "WARNING: wrong parameters definition for action \"%s\" (must be a dict or None)"%action_name

            if variables is None:
                variables = dict()
            if type(variables) != dict:
                variables = dict()
                print "WARNING: wrong variables definition for action \"%s\" (must be a dict or None)"%action_name

            if var_formats is None:
                var_formats = dict()

            if issubclass(action, (lib_action.Action, lib_ramp.Ramp)):

                if handler is None:
                    def new_handler(*args, **kwargs):

                        arg_dict = kwargs.items() + [("name", action_name)] + parameters.items()
                        if board is not None:
                            arg_dict += [("board", board)]
                        if len(args) == len(variables.keys()):
                            arg_dict += zip(variables.keys(), args)
                        elif len(kwargs.keys()) != len(variables.keys()):
                            print "ERROR: wrong arguments call to action \"%s\" (arguments to be given are \"%s\")"%(action_name, str(variables))

                        arg_dict = dict(arg_dict)
                        if var_formats is not None:
                            for var_form in var_formats:
                                fmt = self.system.parser.fmt_to_type(var_formats[var_form])
                                arg_dict[var_form] = fmt(arg_dict[var_form])
                        return action(self.system, **arg_dict)

                    handler = new_handler

                if issubclass(action, lib_ramp.Ramp):
                    selected_list = self.ramps
                    subprg = True
                else:
                    selected_list = self.actions
                    subprg = False

            elif issubclass(action, lib_program.Program):
                if handler is None:
                    print "ERROR: program handler for action \"%s\" must be specified"%action_name
                    return
                selected_list = self.programs
                subprg = True
            else:
                print "ERROR: trying to define action \"%s\" with an unrecognized action type (must be \"%s\" or \"%s\")"%(action_name, str(type(lib_action.Action)), str(lib_program.Program))
                return

            var_keys = variables.keys() + ["time"]
            functions = dict(zip(var_keys, ["x"]*len(var_keys)))

            selected_list[action_name] = dict()
            selected_list[action_name]["call"] = handler
            selected_list[action_name]["vars"] = variables
            selected_list[action_name]["var_formats"] = var_formats
            selected_list[action_name]["pars"] = parameters
            selected_list[action_name]["name"] = action_name
            selected_list[action_name]["board"] = board
            selected_list[action_name]["comment"] = comment
            selected_list[action_name]["time"] = None
            selected_list[action_name]["time_rel"] = None
            selected_list[action_name]["is_subprg"] = subprg
            selected_list[action_name]["enable"] = True
            selected_list[action_name]["categories"] = categories
            selected_list[action_name]["functions"] = functions
            selected_list[action_name]["funct_enable"] = True
            selected_list[action_name]["cmd"] = commands


class BoardList(object):
    def __init__(self, system=None):
        self.boards = dict()
        self.system = system

    def add(self, board_name, board, address, parameters=None, comment=""):
        if not self.boards.has_key(board_name):
            if not issubclass(board, lib_board.Board):
                print "WARNING: trying to add board \"%s\" with wrong type (\"%s\" given instead of \"%s\")"%(board_name, str(board), str(lib_board.Board))

            if parameters is None:
                parameters = dict()
            self.boards[board_name] = board(name=str(board_name),
                                            address=int(address),
                                            comment=str(comment),
                                            **parameters)
        else:
            print "ERROR: board \"%s\" is already defined"%board_name
            return

    def get(self, board_name):
        if self.boards.has_key(board_name):
            return self.boards[board_name]
        else:
            print "ERROR: board \"%s\" not found"%board_name
