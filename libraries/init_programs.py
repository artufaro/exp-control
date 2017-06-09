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

import libraries.program as lib_program
import os, imp

def program_list_init(action_list):

    programs_path = os.path.join("data", "programs")
    for (dirpath, dirnames, filenames) in os.walk(programs_path):
        for fname in filenames:
            fstart, fext = os.path.splitext(fname)
            if fext == ".py" and fstart != "__init__":
                module = imp.load_source(fstart, os.path.join(dirpath, fname))
                categories = dirpath.replace(programs_path, "", 1).split("/")
                categories = tuple(cat for cat in categories if cat)

                if "prg_comment" in vars(module):
                    prg_comment = module.prg_comment
                else:
                    prg_comment = ""

                if "commands" in vars(module):
                    commands = module.commands
                else:
                    commands = None

                action_list.add(fstart, lib_program.Program,
                                handler=module.program, categories=categories,
                                comment=prg_comment, commands=commands)
