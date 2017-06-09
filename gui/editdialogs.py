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

from gui.constants import GREEN, BLUE, PRG_NAME
import gui.programwidget

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore

class ProgramEditDialog(QtGui.QDialog, object):

    def __init__(self, prg_name, par_table,
                 ramp_vars=None, extended_view=None, parent=None, system=None):
        super(ProgramEditDialog, self).__init__(parent)
        layout = QtGui.QVBoxLayout(self)
        self.system = system

        edit_wdg = gui.programwidget.ProgramEditWidget(prg_name=prg_name,
                                                       par_table=par_table,
                                                       ramp_vars=ramp_vars,
                                                       extended_view=extended_view,
                                                       parent=self,
                                                       system=self.system)
        self.table = edit_wdg.table
        self.par_table = par_table

        layout.addWidget(edit_wdg)

        sublayout = QtGui.QHBoxLayout()
        save_button = QtGui.QPushButton("Save")
        save_button.setStyleSheet("color: %s"%GREEN)
        save_button.setToolTip("save current program")
        if extended_view is not None and extended_view:
            save_button.setEnabled(False)
        sublayout.addWidget(save_button)
        save_as_button = QtGui.QPushButton("Save as")
        save_as_button.setStyleSheet("color: %s"%GREEN)
        save_as_button.setToolTip("save current program with a new name")
        sublayout.addWidget(save_as_button)
        save_button.setDefault(True)
        cancel_button = QtGui.QPushButton("Cancel")
        cancel_button.setToolTip("close and do nothing")
        sublayout.addWidget(cancel_button)

        layout.addLayout(sublayout)

        save_button.clicked.connect(self.on_save)
        save_as_button.clicked.connect(partial(self.on_save, save_as=True))
        cancel_button.clicked.connect(self.reject)

        edit_wdg.table.program_opened.connect(edit_wdg.set_title)
        edit_wdg.set_title(self.table.prg_name, self.table.prg_comment)

        self.setWindowTitle(PRG_NAME + " Dialog")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.resize(1000, 600)
        self.accepted.connect(self.on_accepted)
        self.rejected.connect(self.on_rejected)

    def on_save(self, evt=None, save_as=False):
        if self.table.prg_name is None or save_as:
            self.table.save_prg_as(dialog=self)
        else:
            self.table.save_prg()
            self.accept()

    def on_accepted(self):
        if self.par_table is not None:
            self.par_table.set_data()

    def on_rejected(self, evt=None):
        self.table.clear_prg_from_memory()
        if self.par_table is not None:
            self.par_table.set_data()


class LineEditDialog(QtGui.QDialog, object):

    direct_run = QtCore.pyqtSignal(dict)

    def __init__(self, prg_action, par_table, parent=None, system=None):
        super(LineEditDialog, self).__init__(parent)

        self.system = system

        self.prg_action = prg_action
        self.relative_view = par_table.relative_view

        layout0 = QtGui.QVBoxLayout(self)

        tab_widget = QtGui.QTabWidget(self)
        layout0.addWidget(tab_widget)

        tab1 = QtGui.QWidget()
        tab2 = QtGui.QWidget()
        tab3 = QtGui.QWidget()
        layout1 = QtGui.QVBoxLayout(tab1)
        layout2 = QtGui.QVBoxLayout(tab2)
        layout3 = QtGui.QVBoxLayout(tab3)
        tab_widget.addTab(tab1, "variables")
        tab_widget.addTab(tab2, "functions")
        tab_widget.addTab(tab3, "details")

        self.funct_enable_check = QtGui.QCheckBox()
        self.funct_enable_check.setChecked(not self.prg_action["funct_enable"])
        self.ufuncts_texts = []
        for ufunct, ufunct_val in sorted(self.prg_action["functions"].items(),
                                         key=lambda func: func[0] if func[0]!="time" else 0):
            label = QtGui.QLabel(ufunct+" (x)")
            edit = QtGui.QLineEdit(ufunct_val)
            self.ufuncts_texts.append((label, edit, ufunct))

        self.uvars_texts = []
        for uvar, uvar_val in sorted(self.prg_action["vars"].items()):
            label = QtGui.QLabel(uvar)
            if uvar in self.prg_action["var_formats"]:
                fmt = self.prg_action["var_formats"][uvar]
            else:
                fmt = "%s"
            edit = QtGui.QLineEdit(fmt%uvar_val)
            self.uvars_texts.append((label, edit, uvar))

        upars_texts = []
        for upar, upar_val in sorted([("comment", self.prg_action["comment"]),
                                      ("board", self.prg_action["board"])] + \
                                      self.prg_action["pars"].items()):
            if upar_val != "":
                label = QtGui.QLabel(upar)
                edit = QtGui.QLineEdit(str(upar_val))
                edit.setEnabled(False)
                edit.setToolTip(str(upar_val))
                upars_texts.append((label, edit, upar))

        if self.relative_view:
            self.time_text = QtGui.QLineEdit(self.system.time_formats["time_rel"]%\
                                                 self.system.get_time(self.prg_action["time_rel"]))
            self.time_text.setToolTip("time relative to the action selected in the table")
            time_label = QtGui.QLabel("time (rel)")
        else:
            self.time_text = QtGui.QLineEdit(self.system.time_formats["time"]%\
                                                 self.system.get_time(self.prg_action["time"]))
            time_label = QtGui.QLabel("time (abs)")

        self.enable_check = QtGui.QCheckBox()
        self.enable_check.setChecked(not self.prg_action["enable"])

        vars_layout = QtGui.QGridLayout()
        for uvar_n, uvar in enumerate([(time_label, self.time_text, None)] +\
                                       self.uvars_texts +\
                                       [(QtGui.QLabel("disabled"), self.enable_check, None)]):
            vars_layout.addWidget(uvar[0], uvar_n, 0, 1, 1)
            vars_layout.addWidget(uvar[1], uvar_n, 1, 1, 2)
        layout1.addLayout(vars_layout)

        functs_layout = QtGui.QGridLayout()
        for ufunct_n, ufunct in enumerate(self.ufuncts_texts):
            functs_layout.addWidget(ufunct[0], ufunct_n, 0, 1, 1)
            functs_layout.addWidget(ufunct[1], ufunct_n, 1, 1, 2)
        functs_layout.addWidget(QtGui.QLabel("disabled f"), ufunct_n+1, 0, 1, 1)
        functs_layout.addWidget(self.funct_enable_check, ufunct_n+1, 1, 1, 2)
        layout2.addLayout(functs_layout)

        pars_layout = QtGui.QGridLayout()
        for upar_n, upar in enumerate(upars_texts):
            pars_layout.addWidget(upar[0], upar_n, 0, 1, 1)
            pars_layout.addWidget(upar[1], upar_n, 1, 1, 2)
        layout3.addLayout(pars_layout)

        ok_button = QtGui.QPushButton("Insert")
        ok_button.setStyleSheet("color: %s"%GREEN)
        ok_button.setToolTip("add the action to the current program")
        layout0.addWidget(ok_button)
        ok_button.setDefault(True)
        cancel_button = QtGui.QPushButton("Cancel")
        cancel_button.setToolTip("close and do nothing")
        layout0.addWidget(cancel_button)
        direct_run_button = QtGui.QPushButton("Direct Run")
        direct_run_button.setStyleSheet("color: %s"%BLUE)
        direct_run_button.setToolTip("run this action directly on the FPGA")
        layout0.addWidget(direct_run_button)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        direct_run_button.clicked.connect(self.on_direct_run)

        self.setWindowTitle(self.prg_action["name"])
        self.time_text.setFocus()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.resize(250, 200)

    def on_direct_run(self, evt=None):
        self.direct_run.emit(self.get_action())

    def get_action(self):
        uvars = dict()
        for row in self.uvars_texts:
            uvars[row[2]] = str(row[1].text())
        ufuncts = dict()
        for row in self.ufuncts_texts:
            ufuncts[row[2]] = str(row[1].text())

        if self.relative_view:
            time_type = "time_rel"
        else:
            time_type = "time"

        try:
            fmt_str = self.system.time_formats[time_type]
            fmt = self.system.parser.fmt_to_type(fmt_str)
            time = self.system.set_time(fmt(self.time_text.text()))
        except ValueError:
            time = self.prg_action[time_type]
            print "ERROR: times in the table can be only numbers, %f will be used"%time

        self.prg_action[time_type] = time
        self.prg_action["enable"] = not bool(self.enable_check.isChecked())
        self.prg_action["funct_enable"] = not bool(self.funct_enable_check.isChecked())

        try:
            for var_n in self.prg_action["vars"]:
                if var_n in self.prg_action["var_formats"]:
                    fmt_str = self.prg_action["var_formats"][var_n]
                    fmt = self.system.parser.fmt_to_type(fmt_str)
                else:
                    fmt = str
                uvars[var_n] = fmt(uvars[var_n])
        except ValueError:
            uvars = self.prg_action["vars"]
            print "ERROR: variables given in a wrong format"
        self.prg_action["vars"] = uvars
        self.prg_action["functions"] = ufuncts

        return self.prg_action
