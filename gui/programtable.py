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

from functools import partial
import re

import gui.editdialogs
import gui.opensavedialogs

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui


class ProgramTable(QtGui.QTableWidget, object):

    program_opened = QtCore.pyqtSignal(object, object)
    program_sent = QtCore.pyqtSignal(bool)
    actions_updated = QtCore.pyqtSignal()
    dialogs_changed = QtCore.pyqtSignal(int)
    fpgas_updated = QtCore.pyqtSignal(list)

    def __init__(self, prg_name=None, par_table=None,
                 relative_view=False, extended_view=False, hide_disabled=False,
                 parent=None, ramp_vars=None, system=None):

        self.system = system

        self.prg_name = prg_name
        self.prg_comment = None
        self.cmd_str = ("", "")

        self.count_dialogs = 0

        self.extended_view = extended_view
        self.relative_view = relative_view
        self.hide_disabled = hide_disabled

        self.col_keys = ["time", "enable", "name", "vars", "is_subprg", "parents"]
        self.col_names = dict([("time", "time"),
                               ("name", "action name"),
                               ("vars", "variables"),
                               ("enable", "dis"),
                               ("is_subprg", "sub"),
                               ("parents", "parent programs")])

        cols = len(self.col_keys)
        rows = 0
        super(ProgramTable, self).__init__(rows, cols, parent=parent)

        self.cellDoubleClicked.connect(self.on_cell_doubleclick)
        self.cellChanged.connect(self.on_cell_changed)

        self.setColumnWidth(self.col_keys.index("time"), 95)
        self.setColumnWidth(self.col_keys.index("name"), 215)
        self.setColumnWidth(self.col_keys.index("vars"), 100)
        self.setColumnWidth(self.col_keys.index("enable"), 30)
        self.setColumnWidth(self.col_keys.index("is_subprg"), 30)
        self.setColumnWidth(self.col_keys.index("parents"), 200)
        self.verticalHeader().setFixedWidth(50)

        if par_table is not None:
            self.subprg = par_table.subprg
            self.actions_updated.connect(par_table.actions_updated.emit)
        else:
            self.subprg = dict()

        self.ramp_vars = ramp_vars

        self.set_data(prg_name, ramp_vars=ramp_vars)

    def clear_prg_from_memory(self, prg_name=None):
        if prg_name is None:
            prg_name = self.prg_name
        if self.subprg.has_key(prg_name):
            del self.subprg[prg_name]
            print "clearing program '%s'"%prg_name

    def prg_list(self):
        if self.subprg.has_key(self.prg_name):
            return self.subprg[self.prg_name]
        else:
            if self.prg_name is not None:
                print "ERROR: program '%s' not found in the internal database"%self.prg_name
            return []

    def categories(self):
        itm = self.system.action_list.get_dict(self.prg_name)
        if itm is not None:
            return itm["categories"]
        else:
            if self.prg_name is not None:
                print "ERROR: program '%s' not found in the internal database"%self.prg_name
            return []

    def add_dialog(self):
        self.count_dialogs += 1
        self.dialogs_changed.emit(self.count_dialogs)

    def remove_dialog(self):
        self.count_dialogs -= 1
        self.dialogs_changed.emit(self.count_dialogs)

    def set_data(self, prg_name=None, new_prg=False, ramp_vars=None):
        #set the program data if given
        if prg_name is not None or new_prg:
            self.prg_name = prg_name
            if ramp_vars == None:
                ramp_vars = dict()
            self.ramp_vars = ramp_vars
            if self.system.action_list.get_dict(prg_name) is not None:
                self.prg_comment = self.system.action_list.get_dict(prg_name)["comment"]
            else:
                self.prg_comment = None

        if self.subprg.has_key(self.prg_name):
            prg_list = self.subprg[self.prg_name]
        else:
            if self.system.action_list.is_program(self.prg_name):
                prg_list, self.cmd_str = self.system.parser.read_program_file(self.prg_name)
            elif self.system.action_list.is_ramp(self.prg_name):
                prg_list = self.system.parser.get_ramp_acts(self.prg_name, **self.ramp_vars)
            else:
                prg_list = []
                if  self.prg_name is not None:
                    print "WARNING: program '%s' not found, creating an empty program"%self.prg_name
                    self.open_prg(prg_name=None)
                    return

            self.subprg[self.prg_name] = prg_list

        #build the table row list
        self.subprg[self.prg_name] = self.set_time()
        table_lines = self.get_all(lst=self.prg_list(),
                                   time=self.system.set_time(0.0),
                                   enable=True,
                                   enable_parent=True)
        table_lines = self.set_time(table_lines)

        #prevents events while building table
        self.blockSignals(True)

        #redo the table if line number is changed
        if self.rowCount() != len(table_lines):
            self.clear()
            self.setRowCount(len(table_lines))

        for n_key, key in enumerate(self.col_keys):
            for n_row, row in enumerate(table_lines):
                cell = row[key]

                if key == "enable":
                    checkbox = QtGui.QCheckBox()
                    checkbox.setChecked(not cell)
                    checkbox.stateChanged.connect(partial(self.on_cell_changed, n_row, n_key))
                    checkbox.setToolTip("disable action")
                    self.setCellWidget(n_row, n_key, checkbox)
                elif key == "is_subprg":
                    if cell:
                        button = QtGui.QPushButton("s")
                        button.clicked.connect(partial(self.on_open_subprg, row=n_row))
                        button.setToolTip("edit subprogram")
                        self.setCellWidget(n_row, n_key, button)
                    else:
                        self.setCellWidget(n_row, n_key, QtGui.QWidget())
                else:
                    if key == "vars":
                        cell_list = sorted(cell.items())

                        cell = []
                        for uvar in cell_list:
                            v_item = ""
                            v_key = uvar[0]
                            v_value = uvar[1]
                            if v_key in row["var_formats"]:
                                fmt = row["var_formats"][v_key]
                            else:
                                fmt = "%s"
                            if len(cell_list) > 1:
                                v_item += "%s="%v_key
                            v_item += fmt%v_value
                            cell.append(v_item)
                        cell = ", ".join(cell)

                    if key == "parents":
                        if self.prg_name in cell:
                            cell.remove(self.prg_name)
                        cell = " > ".join(cell)

                    if key == "time":
                        if self.relative_view:
                            cell = self.system.time_formats["time_rel"]%\
                                            self.system.get_time(row["time_rel"])
                        else:
                            cell = self.system.time_formats["time"]%\
                                            self.system.get_time(row["time"])

                    new_item = QtGui.QTableWidgetItem(str(cell))
                    new_item.setToolTip(str(cell))

                    if key in ["time", "vars"]:
                        new_item.setTextAlignment(QtCore.Qt.AlignRight)
                    if key in ["name", "parents"] or self.extended_view \
                                        or (key == "vars" and len(cell) == 0):
                        new_item.setFlags(new_item.flags()&~QtCore.Qt.ItemIsEditable)
                    if self.extended_view:
                        new_item.setFlags(new_item.flags()&~QtCore.Qt.ItemIsEnabled)

                    if self.extended_view and not row["enable_parent"]:
                        new_item.setBackground(QtCore.Qt.lightGray)
                        font = QtGui.QFont()
                        font.setItalic(True)
                        new_item.setFont(font)

                    is_f = False
                    for kk in row["functions"].keys():
                        if re.match("^\s*x?$", row["functions"][kk]) is None:
                            is_f = True
                    if is_f and row["funct_enable"]:
                        font = QtGui.QFont()
                        font.setBold(True)
                        new_item.setFont(font)

                    self.setItem(n_row, n_key, new_item)

        self.setHorizontalHeaderLabels([self.col_names[col] for col in self.col_keys])

        self.blockSignals(False)
        self.verticalHeader().setDefaultSectionSize(24)

    #function that returns all subroutines actions
    def get_all(self, lst, time, enable, enable_parent, extended=None, parents=None):
        if extended is None:
            extended = self.extended_view
        if parents is None:
            parents = [self.prg_name]

        #actions to be returned
        all_items = []
        if lst is not None:
            for itm in lst:
                itm = itm.copy()
                itm["time"] = itm["time"] + time
                itm["enable_parent"] = enable_parent and enable
                itm["parents"] = parents

                if extended and itm["is_subprg"]:
                    if not self.subprg.has_key(itm["name"]) \
                            and self.system.action_list.is_program(itm["name"]):
                        self.subprg[itm["name"]], _ = self.system.parser.read_program_file(itm["name"])
                    elif self.system.action_list.is_ramp(itm["name"]):
                        self.subprg[itm["name"]] = \
                                self.system.parser.get_ramp_acts(itm["name"], **itm["vars"])
                    if itm["name"] not in parents:
                        itm["parents"] = itm["parents"] + [itm["name"]]
                        items = self.get_all(lst=self.subprg[itm["name"]],
                                             time=itm["time"],
                                             enable=itm["enable"],
                                             enable_parent=itm["enable_parent"],
                                             parents=itm["parents"])
                    else:
                        print "ERROR: infinite recursion for subprogram '%s'"%itm["name"]
                        items = []
                else:
                    items = [itm]

                if not(self.hide_disabled and not itm["enable"] and extended) and items is not None:
                    all_items += items

                if items is None:
                    return []

        return all_items

    def set_time(self, prg_list=None):
        if prg_list is None:
            prg_list = self.prg_list()

        prg_list = sorted(prg_list, key=lambda x: x["time"])
        if self.relative_view:
            for item_n, _ in enumerate(prg_list):
                if item_n > 0:
                    time = prg_list[item_n]["time"] - prg_list[item_n-1]["time"]
                    prg_list[item_n]["time_rel"] = time
                else:
                    prg_list[item_n]["time_rel"] = prg_list[item_n]["time"]
        return prg_list

    def on_cell_changed(self, row, col, evt=None):
        if not self.extended_view:
            item = self.item(row, col)
            widget = self.cellWidget(row, col)
            col_name = self.col_keys[col]

            set_value = True
            if item is not None:
                value = str(self.item(row, col).text())

                if col_name == "time":
                    if self.relative_view:
                        col_name = "time_rel"
                    try:
                        fmt_str = self.system.time_formats[col_name]
                        fmt = self.system.parser.fmt_to_type(fmt_str)
                        value = self.system.set_time(fmt(value))
                    except ValueError:
                        print "ERROR: wrong time input format in table"
                        set_value = False

                elif col_name == "vars":
                    new_vars = [val for val in value.split(",")]
                    old_vars = self.prg_list()[row]["vars"]
                    value = dict()
                    if len(new_vars) == len(old_vars):
                        for new_v in new_vars:
                            uvar = [v.strip() for v in new_v.split("=")]
                            if len(uvar) == 1 and len(old_vars) == 1:
                                key = old_vars.keys()[0]
                                var_value = uvar[0]
                            elif old_vars.has_key(uvar[0]):
                                key = uvar[0]
                                var_value = uvar[1]
                            else:
                                print "ERROR: wrong variable input name in table"
                                set_value = False

                            if key in self.prg_list()[row]["var_formats"]:
                                fmt_str = self.prg_list()[row]["var_formats"][key]
                                fmt = self.system.parser.fmt_to_type(fmt_str)
                            else:
                                fmt = str
                            try:
                                value[key] = fmt(var_value)
                            except ValueError:
                                print "ERROR: wrong variable input format in table"
                                set_value = False
                    else:
                        print "ERROR: wrong variable input format in table"
                        set_value = False

            elif widget is not None and col_name == "enable":
                value = not bool(widget.isChecked())
            else:
                print "ERROR: internal error while reading table cells"
                set_value = False

            if set_value:
                self.prg_list()[row][col_name] = value

        self.sync_relative_time()
        self.set_data()

    def on_cell_doubleclick(self, row, col):
        if not self.extended_view and self.col_keys[col] == "name":
            win = gui.editdialogs.LineEditDialog(prg_action=self.prg_list()[row],
                                                 par_table=self,
                                                 parent=self, system=self.system)

            self.add_dialog()

            def on_accepted(row, win):
                if not self.extended_view:
                    self.prg_list()[row] = win.get_action()
                    self.sync_relative_time()
                    self.set_data()
                self.remove_dialog()

            def on_rejected():
                self.remove_dialog()
                self.set_data()

            win.direct_run.connect(self.on_direct_run)
            win.accepted.connect(partial(on_accepted, row=row, win=win))
            win.rejected.connect(on_rejected)
            win.show()

    def on_open_subprg(self, evt=None, row=None):
        if not self.extended_view:
            if row is not None:
                if self.prg_list()[row]["is_subprg"]:
                    self.add_dialog()
                    if self.system.action_list.is_ramp(self.prg_list()[row]["name"]):
                        extended_view = True
                    else:
                        extended_view = None
                    win = gui.editdialogs.ProgramEditDialog(prg_name=self.prg_list()[row]["name"],
                                                            par_table=self,
                                                            ramp_vars=self.prg_list()[row]["vars"],
                                                            extended_view=extended_view,
                                                            parent=self,
                                                            system=self.system)
                    win.accepted.connect(self.remove_dialog)
                    win.rejected.connect(self.remove_dialog)
                    win.show()

    def sync_relative_time(self):
        if self.relative_view and not self.extended_view:
            time = 0
            for item_n, item in enumerate(self.prg_list()):
                if item["time_rel"] < 0:
                    old_time = time
                time += item["time_rel"]
                self.prg_list()[item_n]["time"] = time
                if item["time_rel"] < 0 and item_n > 0:
                    time = old_time


    def get_selected_rows(self):
        selection = self.selectedIndexes()
        sel_rows = set(sel.row() for sel in selection)
        return list(sel_rows)

    def add_line(self, action):
        if not self.extended_view:
            row = row = len(self.prg_list())
            if self.relative_view:
                rows = self.get_selected_rows()
                if len(rows) == 1:
                    row = rows[0] + 1
                elif len(rows) != 0:
                    print "ERROR: select one line in relative mode insertion"
                    return

            self.prg_list().insert(row, action)

            self.sync_relative_time()
            self.set_data()

    def delete_selected_lines(self, evt=None):
        if not self.extended_view:
            sel_rows = self.get_selected_rows()

            for row in sorted(sel_rows, reverse=True):
                self.prg_list().pop(row)

            self.sync_relative_time()
            self.set_data()

    def comment_selected_lines(self, evt=None, comment=False, uncomment=False, toggle=False):
        if not self.extended_view:
            sel_rows = self.get_selected_rows()

            if comment and not uncomment and not toggle:
                state = False
            elif not comment and uncomment and not toggle:
                state = True
            elif not comment and not uncomment and toggle:
                state = None
            else:
                print "ERROR: internal error in line comments"
                return

            for row in sel_rows:
                if state is not None:
                    self.prg_list()[row]["enable"] = state
                else:
                    self.prg_list()[row]["enable"] = not self.prg_list()[row]["enable"]

            self.sync_relative_time()
            self.set_data()

    def open_prg(self, evt=None, prg_name=None, ask_name=False):
        if ask_name:
            win = gui.opensavedialogs.ProgramOpenDialog(parent=self, system=self.system)

            def on_accepted(win):
                prg_name = win.prg_name
                if prg_name is None or prg_name in self.system.action_list.tot_list():
                    self.open_prg(prg_name=prg_name)
                else:
                    print "ERROR: program '%s' not found in the database"%prg_name

            win.accepted.connect(partial(on_accepted, win=win))
            win.show()
        else:
            if prg_name is not None:
                print "opening program '%s'"%prg_name
            else:
                print "opening a new program"
            self.clear_prg_from_memory()
            self.set_data(prg_name=prg_name, new_prg=prg_name is None)
            self.program_opened.emit(self.prg_name, self.prg_comment)

    def update_fpgas(self, evt=None, init=True):
        if init:
            self.system.init_fpgas()
        status = self.system.get_fpga_status()
        self.fpgas_updated.emit(status)
        return status

    def check_prg(self):
        prg_name = "__temp_check"
        self.save_prg(prg_name=prg_name, categories=[], prg_list=self.prg_list())
        self.system.set_program(prg_name)
        self.system.check_instructions()

    def send_prg(self, evt=None, prg_name=None, save_before=False):
        result = False
        if save_before and self.prg_name is not None:
            self.save_prg()
        elif self.prg_name is None:
            self.save_prg(prg_name="__new_program", categories=[], prg_list=self.prg_list())

#        status = self.update_fpgas(init=False)
#        tot_state = True
#        for state in status:
#            tot_state = tot_state and not state.running
#        if not tot_state:
#            reply = QtGui.QMessageBox.question(self, 'FPGA warning',
#                                               "Another program is running on one or more FPGAs,\nare you sure to launch a new one?",
#                                               QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
#                                               QtGui.QMessageBox.No)
#            tot_state = reply == QtGui.QMessageBox.Yes
#
#        if tot_state:
        if prg_name is None:
            if self.prg_name is not None:
                prg_name = self.prg_name
            else:
                prg_name = "__new_program"

        self.system.set_program(prg_name)
        result = self.system.send_program_and_run()
        self.program_sent.emit(result)
        return result

    def on_direct_run(self, action=None):
        if action is not None:
            print "direct run for action '%s'"%action["name"]
            action["time"] = self.system.set_time(0.0)
            if action["is_subprg"]:
                acts = self.get_all(lst=[action],
                                    time=self.system.set_time(0.0),
                                    enable=True,
                                    enable_parent=True,
                                    extended=True)
                for act in acts:
                    act["time"] -= acts[0]["time"]
            else:
                acts = [action]

        self.save_prg(prg_name="__temp_direct_run", prg_list=acts, categories=[])
        self.send_prg(prg_name="__temp_direct_run")

    def save_prg_as(self, evt=None, dialog=None):
        win = gui.opensavedialogs.ProgramSaveDialog(prg_name=self.prg_name,
                                                    categories=self.categories(),
                                                    parent=self, system=self.system)

        def on_accepted(win, dialog):
            prg_name = win.prg_name
            categories = win.categories
            confirm = True
            if self.system.action_list.tot_list().has_key(prg_name):
                old_categories = self.system.action_list.get_dict(prg_name)["categories"]
                if categories == old_categories:
                    msg = "An action named '%s' is already saved in '%s', are you shure to overwrite it?"%\
                           (prg_name,
                            "/".join(categories))
                else:
                    msg = "An action named '%s' is already saved in '%s', are you shure to save it in '%s'? This may cause severe conflicts"%\
                           (prg_name,
                            "/".join(old_categories),
                            "/".join(categories))
                reply = QtGui.QMessageBox.question(self, 'Action conflict',
                                                   msg,
                                                   QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                   QtGui.QMessageBox.No)
                confirm = reply == QtGui.QMessageBox.Yes

            if confirm:
                prg_list = self.prg_list()
                self.clear_prg_from_memory()
                self.subprg[prg_name] = prg_list
                self.save_prg(prg_name=prg_name, categories=categories,
                              prg_list=prg_list, prg_comment=self.prg_comment,
                              cmd_str=self.cmd_str)
                self.open_prg(prg_name=prg_name)

                if dialog is not None:
                    dialog.accept()

        win.accepted.connect(partial(on_accepted,
                                     win=win,
                                     dialog=dialog))
        win.show()

    def save_prg(self, evt=None, prg_name=None, categories=None, prg_list=None, prg_comment=None, cmd_str=None):
        if prg_name is None:
            if self.prg_name is None:
                self.save_prg_as()
            else:
                self.save_prg(prg_name=self.prg_name,
                              categories=self.categories(),
                              prg_list=self.prg_list(),
                              prg_comment=self.prg_comment,
                              cmd_str=self.cmd_str)
        elif prg_list is None or categories is None:
            print "ERROR: internal error while calling save function"
        else:
            print "saving program '%s'"%prg_name
            self.system.parser.write_program_file(prg_name, categories, prg_list, prg_comment, cmd_str)
            self.actions_updated.emit()

    def set_comment(self, comment):
        self.prg_comment = comment
        self.program_opened.emit(self.prg_name, self.prg_comment)
