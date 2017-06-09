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
import instruction as lib_instructions
import ramp as lib_ramp
from copy import copy

class Program(object):
    def __init__(self, system, name, comment=""):
        self.name = str(name)
        self.instructions = dict()
        self.comment = str(comment)
        self.version = None

        self.system = system

    def add(self, time, action_str, *args, **kwargs):
        if kwargs.has_key("enable"):
            enable = bool(kwargs.pop("enable"))
        else:
            enable = True
        time = int(time)

        functions = None
        if "functions" in kwargs.keys():
            functions = kwargs["functions"].copy()
            del kwargs["functions"]
        action = self.system.action_list.get(str(action_str), *args, **kwargs)

        if functions is not None:
            if "funct_enable" in functions:
                funct_enable = functions["funct_enable"]
                del functions["funct_enable"]
            else:
                funct_enable = True
            if funct_enable:
                for f_key in functions:
                    if f_key == "time":
                        time_ms = functions[f_key](self.system.get_time(time))
                        time = self.system.set_time(time_ms)
                    else:
                        setattr(action, f_key, functions[f_key](getattr(action, f_key)))

        if isinstance(action, lib_ramp.Ramp):
            action = action.get_prg()
        if isinstance(action, (lib_action.Action, Program)):
            istr = lib_instructions.Instruction(time, action, enable=enable, parents=self)
            self.instructions[istr.uuid] = istr
        else:
            print "WARNING: trying to add at time %d of program \"%s\" an action of type \"%s\" (instead of \"%s\" or \"%s\")"%(time, self.name, str(action), str(lib_action.Action), str(Program))

    def get(self, uuid):
        if self.instructions.has_key(uuid):
            return self.instructions[uuid]
        else:
            return None

    def set_comment(self, comment):
        self.comment = str(comment)

    def set_version(self, version):
        self.version = str(version)

    def get_all_instructions(self, only_enabled=True):
        instructs = []
        for instr in self.get_instructions(only_enabled):
            if isinstance(instr.action, Program):
                for instr_sub in instr.action.get_all_instructions():
                    i0 = copy(instr_sub)
                    i0.time += instr.time
                    i0.parents = instr.parents + i0.parents
                    instructs.append(i0)
            elif isinstance(instr.action, lib_action.Action):
                i0 = copy(instr)
                instructs.append(i0)
            else:
                print "ERROR: wrong action type found for instruction at time %d of program \"%s\" (\"%s\" instead of \"%s\" or \"%s\")"%(instr.time, self.name, str(type(instr.action)), str(lib_action.Action), str(Program))
        instructs.sort()
        return instructs

    def get_instructions(self, only_enabled=True):
        instructs = []
        for instr in self.instructions.values():
            i0 = copy(instr)
            if not bool(only_enabled) or instr.enable:
                instructs.append(i0)
        instructs.sort()
        return instructs

    def _print_instructions(self, extended=False, only_enabled=True):
        if not bool(extended):
            to_print = "Program intructions:\n"
            instructs = self.get_instructions(only_enabled=only_enabled)
        else:
            to_print = "Extended program intructions:\n"
            instructs = self.get_all_instructions(only_enabled=only_enabled)

        for inst in instructs:
            to_print += "%15d"%inst.time + " " + str(inst.action.name)
            if isinstance(inst.action, lib_action.AnalogAction):
                if inst.action.value is not None:
                    to_print += " - value: " + str(inst.action.value)
            elif isinstance(inst.action, lib_action.DdsAction):
                if inst.action.frequency is not None:
                    to_print += " - freq: " + str(inst.action.frequency)
                if inst.action.amplitude is not None:
                    to_print += " - amp: " + str(inst.action.amplitude)
                if inst.action.n_lut is not None:
                    to_print += " - lut: " + str(inst.action.n_lut)
            else:
                pass

            if len(inst.action.comment) > 0:
                to_print += " (%s)"%inst.action.comment

            if not inst.enable:
                to_print += " [DISABLED]"
            if len(inst.parents) > 1:
                to_print += " (" + inst.parents[-1].name + ")"
            if inst is not instructs[-1]:
                to_print += "\n"

        print to_print
