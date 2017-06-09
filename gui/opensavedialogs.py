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

from gui.constants import GREEN
import gui.actionstree

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui


class ProgramOpenDialog(QtGui.QDialog, object):

    def __init__(self, parent=None, system=None):
        super(ProgramOpenDialog, self).__init__(parent)
        self.system = system

        self.tree = gui.actionstree.ActionsTree(only_prg=True, parent=self, system=self.system)
        self.prg_name = None

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        sublayout = QtGui.QHBoxLayout()

        find_text = QtGui.QLineEdit()
        find_text.setPlaceholderText("search...")
        find_text.setToolTip("filter programs by name")
        find_text.textChanged.connect(self.on_filter_actions)

        layout.addWidget(find_text)
        layout.addWidget(self.tree)
        layout.addLayout(sublayout)

        ok_button = QtGui.QPushButton("Open")
        ok_button.setToolTip("open the selected program")
        cancel_button = QtGui.QPushButton("Cancel")
        cancel_button.setToolTip("close and do nothing")
        empty_button = QtGui.QPushButton("New program")
        empty_button.setToolTip("open a new empty program")

        sublayout.addWidget(ok_button)
        sublayout.addWidget(empty_button)
        layout.addWidget(cancel_button)

        empty_button.clicked.connect(partial(self.on_accept, empty=True))
        ok_button.clicked.connect(partial(self.on_accept, empty=False))
        cancel_button.clicked.connect(self.reject)
        self.tree.doubleClicked.connect(partial(self.on_accept, empty=False))

        self.setWindowTitle("Select a program to open")
        find_text.setFocus()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.resize(300, 400)

    def on_filter_actions(self, text):
        self.tree.update_actions(force_init=False, force_new_tree=False,
                                 filter_on=True, filter_text=str(text))

    def on_accept(self, evt=None, empty=False):
        if empty:
            self.prg_name = None
            self.accept()
        else:
            self.prg_name = self.tree.get_selected_name()
            if self.prg_name is not None:
                self.accept()
            elif self.tree.get_selected_cat() is None:
                print "WARNING: select one name and one category"


class ProgramSaveDialog(QtGui.QDialog, object):

    def __init__(self, prg_name, categories, parent=None, system=None):
        super(ProgramSaveDialog, self).__init__(parent)

        self.prg_name = None
        self.categories = None

        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        self.prg_name_text = QtGui.QLineEdit()
        if prg_name is not None:
            self.prg_name_text.setText(prg_name)

        self.cat_list = QtGui.QListWidget(self)
        for categ in system.parser.get_programs_dirs():
            self.cat_list.addItem(QtGui.QListWidgetItem(categ))
        sel_index = 0
        curr_cat = "/".join(categories)
        if curr_cat in system.parser.get_programs_dirs():
            sel_index = system.parser.get_programs_dirs().index(curr_cat)
        self.cat_list.setCurrentRow(sel_index)

        layout.addWidget(QtGui.QLabel("category"), 0, 0, 1, 1)
        layout.addWidget(QtGui.QLabel("name"), 2, 0, 1, 1)
        layout.addWidget(self.prg_name_text, 2, 1, 1, 1)

        ok_button = QtGui.QPushButton("Save")
        ok_button.setStyleSheet("color: %s"%GREEN)
        ok_button.setToolTip("save the program with given name in the selected category")
        cancel_button = QtGui.QPushButton("Cancel")
        cancel_button.setToolTip("close and do nothing")

        layout.addWidget(ok_button, 3, 0, 1, 2)
        layout.addWidget(cancel_button, 4, 0, 1, 2)
        layout.addWidget(self.cat_list, 0, 1, 1, 2)

        ok_button.clicked.connect(self.on_accept)
        cancel_button.clicked.connect(self.reject)

        self.setWindowTitle("Select where to save the program")
        self.setFocus()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.resize(250, 200)

    def on_accept(self, evt=None):
        self.prg_name = str(self.prg_name_text.text())
        sel_items = self.cat_list.selectedItems()
        if len(sel_items) > 0:
            self.categories = tuple(str(sel_items[0].text()).split("/"))

        if self.prg_name is not None and self.categories is not None and len(self.prg_name) > 0:
            self.accept()
        else:
            print "WARNING: give one name and select one category"
