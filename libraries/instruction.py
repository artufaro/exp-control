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
import uuid as uuid_lib

class Instruction(object):
    def __init__(self, time, action, enable=True, parents=None, uuid=None):
        self.time = int(time)

        if not isinstance(action, (lib_action.Action, lib_program.Program)):
            print "WARNING: instruction at clock time %d does not specify a valid action"%self.time

        if parents is None:
            parents = []
        if type(parents) != list:
            parents = [parents]
        for par in parents:
            if not isinstance(par, lib_program.Program):
                print "WARNING: instruction at clock time %d does not specify a valid parent program"%self.time

        self.parents = parents
        self.action = action
        self.enable = bool(enable)
        if uuid is None:
            self.uuid = uuid_lib.uuid1()
        else:
            self.uuid = uuid

    def __lt__(self, other):
        if isinstance(other, Instruction):
            return self.time < other.time
        else:
            print "WARNING: cannot compare '%s' with '%s'"%(str(type(self)), str(type(other)))
            return None

    def __eq__(self, other):
        return isinstance(other, Instruction) and self.uuid == other.uuid

    def __ne__(self, other):
        return not self.__eq__(other)


class FpgaInstruction(Instruction):
    def __init__(self, time_delta=0, curr_instr=None, action=None):
        time_delta = int(time_delta)
        if curr_instr is not None and action is None:
            if not isinstance(curr_instr, Instruction):
                print "WARNING: wrong call to fpga instruction at clock time %d ('%s' given instead of '%s')"%(time_delta, str(type(curr_instr)), str(Instruction))
            else:
                action = curr_instr.action
        elif curr_instr is None and action is not None:
            if not isinstance(action, lib_action.Action):
                print "WARNING: wrong call to fpga instruction at clock time %d ('%s' given instead of '%s')"%(time_delta, str(type(action)), str(lib_action.Action))
        else:
            print "WARNING: call to fpga instruction at clock time %d is not implemented"%time_delta

        super(FpgaInstruction, self).__init__(time=time_delta,
                                              action=action,
                                              enable=True)

        if isinstance(action, lib_action.Action):
            self.data = action.do_action()
