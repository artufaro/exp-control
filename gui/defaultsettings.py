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

import json, os

class DefaultProgSettings(object):

    def __init__(self, fname=os.path.join("data", ".program.conf")):
        self.config_fname = str(fname)
        self.last_prg = None
        self.last_evap_ramp = None

    def save_settings(self):
        try:
            with open(self.config_fname, "wb") as fid:
                json.dump(vars(self), fid)
        except IOError:
            print "ERROR: error while writing settings into file '" + self.config_fname + "'"

    def load_settings(self):
        try:
            with open(self.config_fname, "rb") as fid:
                var = json.load(fid)
            for key, val in var.items():
                setattr(self, key, val)
        except IOError:
            print "WARNING: no config file '" + self.config_fname + "' found"
