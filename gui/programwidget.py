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

from gui.constants import RED
import gui.programtable
import gui.actionstree

import PySide.QtGui as QtGui

class ProgramEditWidget(QtGui.QWidget, object):

    def __init__(self, prg_name=None, par_table=None, ramp_vars=None,
                 extended_view=None, parent=None, system=None):
        super(ProgramEditWidget, self).__init__(parent)

        self.system = system
        self.table = gui.programtable.ProgramTable(prg_name=prg_name,
                                                   par_table=par_table,
                                                   ramp_vars=ramp_vars,
                                                   parent=self,
                                                   system=self.system)

        self.table.setMinimumWidth(500)

        main_layout = QtGui.QHBoxLayout()
        center_widget = QtGui.QWidget(self)
        left_widget = QtGui.QWidget(self)
        left_layout = QtGui.QVBoxLayout(left_widget)
        center_layout = QtGui.QVBoxLayout(center_widget)
        main_layout.addWidget(left_widget)
        main_layout.addWidget(center_widget)

        left_widget.setMinimumWidth(160)
        left_widget.setMaximumWidth(300)

        center_layout.addWidget(self.table)

        self.actions_tree = gui.actionstree.ActionsTreeWidget(table=self.table,
                                                              parent=self,
                                                              system=self.system)

        self.title_label = QtGui.QLabel("")
        left_layout.addWidget(self.title_label)
        self.comment_label = QtGui.QLabel("")
        left_layout.addWidget(self.comment_label)
        left_layout.addWidget(self.actions_tree)

        abs_rel_box = QtGui.QGroupBox("Time mode")
        abs_rel_box.setToolTip("view times in absolute mode, or in relative mode (relatively to the previous acions)")
        abs_rel_layout = QtGui.QHBoxLayout()
        abs_rel_box.setLayout(abs_rel_layout)
        self.relative_box = QtGui.QRadioButton("relative")
        absolute_box = QtGui.QRadioButton("absolute")
        abs_rel_layout.addWidget(self.relative_box)
        abs_rel_layout.addWidget(absolute_box)
        self.relative_box.setChecked(self.table.relative_view)
        absolute_box.setChecked(not self.table.relative_view)
        self.relative_box.toggled.connect(self.on_relative_time)
        left_layout.addWidget(abs_rel_box)

        ext_comp_box = QtGui.QGroupBox("View mode")
        ext_comp_box.setToolTip("view only direct actions (compact), or extend all subprograms actions (extended)")
        ext_comp_layout = QtGui.QGridLayout()
        ext_comp_box.setLayout(ext_comp_layout)
        self.extended_box = QtGui.QRadioButton("extended")
        compact_box = QtGui.QRadioButton("compact")
        ext_comp_layout.addWidget(self.extended_box, 0, 0, 1, 1)
        ext_comp_layout.addWidget(compact_box, 0, 1, 1, 1)
        left_layout.addWidget(ext_comp_box)

        self.hide_disabled_box = QtGui.QCheckBox("hide disabled")
        self.hide_disabled_box.setChecked(self.table.hide_disabled)
        ext_comp_layout.addWidget(self.hide_disabled_box, 1, 0, 1, 2)
        self.hide_disabled_box.stateChanged.connect(self.on_hide_disabled)
        self.hide_disabled_box.setEnabled(bool(self.extended_box.isChecked()))
        self.hide_disabled_box.setToolTip("hide the lines that have been disabled, directly or from their parent programs")
        self.actions_tree.tree.setEnabled(not bool(self.extended_box.isChecked()))

        if extended_view is not None:
            self.extended_box.setChecked(extended_view)
            compact_box.setChecked(not extended_view)
            self.on_extended_view()
            ext_comp_box.setEnabled(False)
        else:
            self.extended_box.setChecked(self.table.extended_view)
            compact_box.setChecked(not self.table.extended_view)
            self.extended_box.toggled.connect(self.on_extended_view)

        line_controls_widget = QtGui.QWidget()
        line_controls_widget.setMinimumWidth(400)
        line_controls_layout = QtGui.QHBoxLayout(line_controls_widget)

        delete_button = QtGui.QPushButton("Delete sel lines")
        delete_button.clicked.connect(self.table.delete_selected_lines)
        delete_button.setStyleSheet("color: %s"%RED)
        delete_button.setToolTip("Delete selected lines")
        line_controls_layout.addWidget(delete_button)

        comment_button = QtGui.QPushButton("Disable sel lines")
        comment_button.clicked.connect(partial(self.table.comment_selected_lines, comment=True))
        comment_button.setToolTip("Disable selected lines")
        line_controls_layout.addWidget(comment_button)
        uncomment_button = QtGui.QPushButton("Enable sel lines")
        uncomment_button.clicked.connect(partial(self.table.comment_selected_lines, uncomment=True))
        uncomment_button.setToolTip("Enable selected lines")
        line_controls_layout.addWidget(uncomment_button)
        toggle_button = QtGui.QPushButton("Toggle sel lines")
        toggle_button.clicked.connect(partial(self.table.comment_selected_lines, toggle=True))
        toggle_button.setToolTip("Invert enable/disable status of selected lines")
        line_controls_layout.addWidget(toggle_button)

        comment_button = QtGui.QPushButton("Set program comment")
        comment_button.setToolTip("set a description for the current program")
        comment_button.clicked.connect(self.on_set_comment)
        line_controls_layout.addWidget(comment_button)

        center_layout.addWidget(line_controls_widget)

        self.setLayout(main_layout)

        self.table.actions_updated.connect(self.actions_tree.on_update_actions)
        self.table.dialogs_changed.connect(self.on_dialogs_changed)
        self.actions_tree.direct_run.connect(self.table.on_direct_run)

    def on_set_comment(self, evt=None):
        comment, reply = QtGui.QInputDialog.getText(self, 'Program Comment',
                                                    'enter the program description:')
        if bool(reply):
            self.table.set_comment(str(comment))

    def set_title(self, title=None, comment=None):
        if title is not None and title != "":
            self.title_label.setText("Program: \"%s\""%title)
            self.title_label.setToolTip("current program: \"%s\""%title)
        else:
            self.title_label.setText("New program")
            self.title_label.setToolTip("new program loaded")

        if comment is not None and comment != "":
            self.comment_label.setText("%s"%comment)
            self.comment_label.setToolTip("comment: \"%s\""%comment)
        else:
            self.comment_label.setText("")
            self.comment_label.setToolTip("")

    def on_dialogs_changed(self, n_dialogs):
        if n_dialogs > 0:
            self.relative_box.setDisabled(True)
            self.extended_box.setDisabled(True)
        elif n_dialogs == 0:
            self.relative_box.setEnabled(True)
            self.extended_box.setEnabled(True)
        else:
            print "ERROR: internal dialogs error"

    def on_hide_disabled(self, evt=None):
        self.table.hide_disabled = bool(self.hide_disabled_box.isChecked())
        self.table.set_data()

    def on_extended_view(self, evt=None):
        state = bool(self.extended_box.isChecked())
        self.table.extended_view = state
        self.table.set_data()

        self.hide_disabled_box.setEnabled(state)

    def on_relative_time(self, evt=None):
        self.table.relative_view = bool(self.relative_box.isChecked())
        self.table.set_data()
