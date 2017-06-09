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
#pylint: disable-msg=E0611

import program as lib_program
from numpy import linspace, arange

class Ramp(object):
    def __init__(self, system, name, comment=""):
        self.name = str(name)
        self.comment = str(comment)

        self.system = system

    def get_prg(self):
        return lib_program.Program(self.system, "")

class LinearRamp(Ramp):
    def __init__(self, system, act_name="", act_var_name=None, act_parameters=None,
                 start_t=None, stop_t=None, step_t=None,
                 start_x=None, stop_x=None, step_x=None,
                 n_points=None,
                 name="", comment=""):

        super(LinearRamp, self).__init__(system, name, comment)

        if start_t is not None:
            start_t = float(start_t)
        self.start_t = start_t
        if stop_t is not None:
            stop_t = float(stop_t)
        self.stop_t = stop_t
        if step_t is not None:
            step_t = float(step_t)
        self.step_t = step_t
        if start_x is not None:
            start_x = float(start_x)
        self.start_x = start_x
        if stop_x is not None:
            stop_x = float(stop_x)
        self.stop_x = stop_x
        if step_x is not None:
            step_x = float(step_x)
        self.step_x = step_x

        self.act_name = str(act_name)
        if act_var_name is not None:
            act_var_name = str(act_var_name)
        self.act_var_name = act_var_name
        if act_parameters is not None:
            self.act_parameters = dict(act_parameters)
        else:
            self.act_parameters = dict()

        if start_t is not None:
            start_t = int(start_t)
        self.n_points = n_points

    def get_prg(self):

        program = lib_program.Program(system=self.system, name=self.name, comment=self.comment)

        t_ramp = []
        x_ramp = []

        if None not in [self.start_t, self.stop_t, self.n_points]:
            t_ramp = linspace(self.start_t, self.stop_t, self.n_points)
            if self.act_var_name is not None and None not in [self.start_x, self.stop_x]:
                x_ramp = linspace(self.start_x, self.stop_x, self.n_points)
            else:
                x_ramp = t_ramp
        elif None not in [self.start_t, self.step_t]:
            if self.n_points is not None:
                n_points = self.n_points
            elif self.stop_t is not None and None in [self.start_x, self.step_x, self.stop_x]:
                n_points = int((self.stop_t-self.start_t)/self.step_t)
            elif None not in [self.stop_t, self.start_x, self.step_x, self.stop_x]:
                n_points = min(int((self.stop_t-self.start_t)/self.step_t),
                               int((self.stop_x-self.start_x)/self.step_x))
            else:
                n_points = 0
                print "ERROR: wrong call for \"%s\" with name \"%s\""%(str(type(self)), self.name)

            t_ramp = arange(self.start_t, self.step_t*n_points, self.step_t)
            if self.act_var_name is not None and None not in [self.start_x, self.step_x]:
                x_ramp = arange(self.start_x, self.step_x*n_points, self.step_x)
            else:
                x_ramp = t_ramp
        else:
            print "ERROR: wrong call for \"%s\" with name \"%s\""%(str(type(self)), self.name)

        for tval, xval in zip(t_ramp, x_ramp):
            act_args = self.act_parameters.items()
            if self.act_var_name is not None:
                act_args += [(self.act_var_name, xval)]
            act_args = dict(act_args)
            program.add(self.system.set_time(tval), self.act_name, **act_args)

        return program
