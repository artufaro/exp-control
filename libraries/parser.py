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

PRG_FILE_VERSION = "0.5.1"

import libraries.program as lib_program

import re, os

class Parser(object):
    def __init__(self, system):
        self.system = system
        self.programs_folder = os.path.join("data", "programs")

    def delete_program_file(self, prg_name):
        if self.system.action_list.is_program(prg_name):
            categories = self.system.action_list.get_dict(prg_name)["categories"]
            path, fname = self.get_program_path(prg_name, categories)
            save_name = os.path.join(path, fname)

            if os.path.isfile(save_name):
                print "deleting program '%s'"%save_name
                os.remove(save_name)
            else:
                print "ERROR: filename '%s' not found"%save_name
            self.system.init_actions()

    def read_program_file(self, action_name):
        categories = self.system.action_list.get_dict(action_name)["categories"]
        path, fname = self.get_program_path(action_name, categories)
        fname_path = os.path.join(path, fname)
        if not os.path.isfile(fname_path):
            print "ERROR: filename '%s' not found"%fname_path
            return None
        else:
            print "reading '%s'"%fname_path

        prg_str = ""
        with open(fname_path, "r") as fid:
            prg_str = fid.read()
        prg_list = []
        cmd_str0 = ""
        cmd_str1 = ""

        lines = prg_str.splitlines()
        lines = [l for l in lines if l]

        prg_flag = False
        cmd_flag = cmd_loop_flag = False
        cmd_first_flag = False
        cmd_indent = ""

        version = None
        prg_lines = []
        cmd_lines = ([], [])
        for line in lines:
            if version is None:
                m_vers = re.match("^\s*prg_version\s*=\s*['\"](.*)['\"]$", line)
                if m_vers is not None:
                    version = m_vers.group(1).split(".")
                    current_version = PRG_FILE_VERSION.split(".")
                    valid_version = False
                    for n in range(min(len(version), len(current_version))):
                        valid_version = int(version[n]) == int(current_version[n])
                    if not valid_version:
                        print "WARNING: outdated saved program version"

            return_match = re.match("^\s*return\s+.*$", line) is not None
            prg_start_match = re.match("^\s*def\s+program.*$", line) is not None
            cmd_loop_start_match = re.match("^\s*while\s*\(\s*cmd.running\s*\)\s*:\s*$", line) is not None
            cmd_init_start_match = re.match("^\s*def\s+commands.*$", line) is not None

            if prg_start_match and not prg_flag and not cmd_flag:
                prg_flag = True
            if return_match and prg_flag and not cmd_flag:
                prg_flag = False

            if cmd_init_start_match and not prg_flag and not cmd_flag:
                cmd_flag = True
                cmd_first_flag = True
            if cmd_loop_start_match and not prg_flag and cmd_flag:
                cmd_loop_flag = True
                cmd_first_flag = True
            if return_match and not prg_flag and cmd_flag:
                cmd_loop_flag = cmd_flag = False

            if prg_flag and not prg_start_match:
                prg_lines.append(line.strip())

            if cmd_first_flag and not cmd_init_start_match \
                    and not cmd_loop_start_match and not return_match:
                cmd_first_flag = False
                cmd_indent = re.match("^(\s*)", line).group(1)

            if cmd_flag and not cmd_loop_start_match and not cmd_init_start_match:
                if cmd_loop_flag:
                    cmd_lines[1].append(re.sub(cmd_indent, "", line, count=1))
                else:
                    cmd_lines[0].append(re.sub(cmd_indent, "", line, count=1))

        for line in prg_lines:

            #check if it is a valid line with add instruction
            m0 = re.match("^\s*prg.add[(]\s*(.*)\s*[)]\s*$", line)
            if m0 is None:
                print "ERROR: skipping line '%s'"%line
            else:
                line = m0.group(1)

                #split the line into prg.add function arguments
                #(consider the first grade of parenthesis)
                par_count = spar_count = 0
                part_line = ""
                split_line = []
                for ch in line:
                    if   ch == "(": par_count += 1
                    elif ch == ")": par_count -= 1
                    elif ch == "[": spar_count += 1
                    elif ch == "]": spar_count -= 1
                    if ch == "," and par_count == 0  and spar_count == 0:
                        split_line.append(part_line.strip())
                        part_line = ""
                    else:
                        part_line += ch
                split_line.append(part_line.strip())

                #the line is now splitted into arguments
                line = split_line

                #at least time and action must be present
                if not len(line) >= 2:
                    print "ERROR: skipping line '%s'"%line
                else:
                    #parse time and action name
                    time = line[0]
                    act_name = line[1].strip("'\"")

                    #parse function add agruments
                    #default values
                    functions = []
                    variables = []
                    enable = True
                    funct_enable = True
                    if len(line) > 2:
                        #parse arguments other than time and action name
                        for lin in line[2:]:
                            #match functions arguments
                            m_fun = re.match("\s*functions\s*=\s*(.*)", lin)
                            if m_fun is None:
                                #parse if not functions, split key and value
                                ar = re.split("\s*=\s*", lin)
                                if len(ar) == 2:
                                    #if named argument
                                    if ar[0] == "enable":
                                        #if enamble arg
                                        if ar[1] == "True":
                                            enable = True
                                        elif ar[1] == "False":
                                            enable = False
                                        else:
                                            print "ERROR: enable value '%s' not valid"%ar[1]
                                    else:
                                        #otherwise variable arg
                                        variables.append(ar)
                                else:
                                    #positional variable arg
                                    variables.append(ar)
                            else:
                                #parse functions into key and lambda function
                                m0 = re.match("^dict\s*[(]\s*(.*)[)]$", m_fun.group(1))
                                if m0 is not None:
                                    for m1 in re.split("\s*,\s*", m0.group(1)):
                                        m2 = re.match("^(\S*)\s*=\s*lambda\s+x\s*:\s*(.*)\s*$", m1)
                                        m3 = re.match("^funct_enable\s*=\s*(True|False)\s*$", m1)
                                        if m3 is not None and m2 is None:
                                            if m3.group(1) == "True":
                                                funct_enable = True
                                            elif m3.group(1) == "False":
                                                funct_enable = False
                                            else:
                                                print "ERROR: function enable value '%s' not valid"%m0.group(1)
                                        elif m2 is not None and m3 is None:
                                            functions.append(m2.groups())
                                        else:
                                            print "ERROR: functions of action '%s' not well formatted"%act_name
                                else:
                                    print "ERROR: functions of action '%s' not well formatted"%act_name
                    functions = dict(functions)

                    new_line = self.system.action_list.get_dict(act_name)
                    if new_line is None:
                        print "ERROR: skipping action '%s' not found in the database"%act_name
                    else:
                        if len(new_line["vars"].keys()) != len(variables):
                            print "ERROR: variables '%s' not well formatted in action '%s'"%(str(variables), act_name)
                        else:
                            for uvar in variables:
                                if len(variables) > 1 and len(uvar) != 2:
                                    print "ERROR: wrong variables declaration in action '%s'"%act_name
                                else:
                                    if len(uvar) == 1:
                                        key = new_line["vars"].keys()[0]
                                        value = uvar[0]
                                    else:
                                        key = uvar[0]
                                        value = uvar[1]
                                    if key in new_line["var_formats"]:
                                        fmt_str = new_line["var_formats"][key]
                                        fmt = self.fmt_to_type(fmt_str)
                                    else:
                                        fmt = str
                                    if fmt is int and "." in value:
                                        value = float(value)

                                    new_line["vars"][key] = fmt(value)

                            for key in functions:
                                new_line["functions"][key] = functions[key]

                        new_line["time"] = int(time)
                        new_line["enable"] = bool(enable)
                        new_line["funct_enable"] = bool(funct_enable)

                        prg_list.append(new_line)

        for line in cmd_lines[0]:
            cmd_str0 += line+"\n"
        for line in cmd_lines[1]:
            cmd_str1 += line+"\n"

        return prg_list, (cmd_str0, cmd_str1)

    def write_program_file(self, prg_name, categories, prg_list, prg_comment, cmd_str):
        prg_str = ""

        if prg_comment is None:
            prg_comment = ""
        prg_str += "prg_comment = \"%s\"\n"%prg_comment
        prg_str += "prg_version = \"%s\"\n"%PRG_FILE_VERSION
        prg_str += "def program(prg, cmd):\n"
        for item in prg_list:
            line = "    prg.add(%d, \"%s\""%(int(item["time"]), str(item["name"]))
            if len(item["vars"]) > 0:
                var_items = []
                for var_n in item["vars"]:
                    if var_n in item["var_formats"]:
                        type_fmt = item["var_formats"][var_n]
                    else:
                        type_fmt = "%s"
                    if var_n != "action_name":
                        fmt = self.fmt_to_type(type_fmt)
                        var_items.append([var_n, type_fmt%fmt(item["vars"][var_n])])

                if len(var_items) != 1:
                    var_l = [itm[0]+"="+itm[1] for itm in var_items]
                else:
                    var_l = [var_items[0][1]]
                line += ", " + ", ".join(var_l)
            f_items = item["functions"].items()
            f_items = [it for it in f_items[:] if re.match("^\s*x?\s*$", it[1]) is None]
            if len(f_items) > 0:
                line += ", functions=dict("
                for f_it in f_items:
                    line += f_it[0] + "=lambda x: " + f_it[1] + ", "
                line = line[:-2]
                if not item["funct_enable"]:
                    line += ", funct_enable=False"
                line += ")"
            if not item["enable"]:
                line += ", enable=False"
            line += ")\n"
            prg_str += line

        prg_str += "    return prg\n"

        if cmd_str is not None:
            cmd_str_init = [l for l in cmd_str[0].splitlines() if l]
            cmd_str_loop = [l for l in cmd_str[1].splitlines() if l]
            if len(cmd_str_loop)+len(cmd_str_init) > 0:
                prg_str += "def commands(cmd):\n"
                for l in cmd_str_init:
                    prg_str += "    "+l+"\n"
                if len(cmd_str_loop) > 0:
                    prg_str += "    while(cmd.running):\n"
                    for l in cmd_str_loop:
                        prg_str += "        "+l+"\n"
                prg_str += "    return cmd\n"

        path, fname = self.get_program_path(prg_name, categories)
        fname_path = os.path.join(path, fname)

        print "writing '%s'"%fname_path
        if not os.path.exists(path):
            os.makedirs(path)
        with open(fname_path, "w") as fid:
            fid.write(prg_str)
        self.system.init_actions()

    def get_program_path(self, prg_name, categories):
        return os.path.join(self.programs_folder, *categories), prg_name+".py"

    def get_programs_dirs(self):
        if os.path.isdir(self.programs_folder):
            directs = []
            for fold, _, _ in os.walk(self.programs_folder):
                if self.programs_folder in fold:
                    directs.append(fold.replace(self.programs_folder, "", 1).strip("/"))
            return directs
        else:
            print "ERROR: '%s' folder not found"%self.programs_folder
            return

    def fmt_to_type(self, fmt):
        if "f" in fmt: typ = float
        elif "d" in fmt: typ = int
        elif "s" in fmt: typ = str
        else:
            typ = str
            print "WARNING: unrecognized format '%s'"%fmt
        return typ

    def get_actions_dict(self, only_prg=False):
        if only_prg:
            action_list = self.system.action_list.programs
        else:
            action_list = self.system.action_list.tot_list()

        act_dict = dict()
        for act_name in action_list:
            act = self.system.action_list.get_dict(act_name)
            act_dict[act_name] = act

        return act_dict

    def get_ramp_acts(self, action_name, *args, **kwargs):

        prg = lib_program.Program(self.system, "")
        prg.add(0, action_name, *args, **kwargs)
        instructions = prg.get_all_instructions(only_enabled=False)

        lst = []
        for instr in instructions:
            act_dict = self.system.action_list.get_dict(instr.action.name)
            for uv in act_dict["vars"]:
                act_dict["vars"][uv] = getattr(instr.action, uv)
            act_dict["enable"] = instr.enable
            act_dict["time"] = instr.time
            lst.append(act_dict)

        return lst
