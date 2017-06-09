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
import gui.editdialogs

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore

class ActionsTree(QtGui.QTreeWidget, object):

    def __init__(self, only_prg=False, parent=None, system=None):
        super(ActionsTree, self).__init__(parent)

        self.system = system

        self.actions = []
        self.only_prg = only_prg
        self.update_actions(force_init=True)

        self.setHeaderHidden(True)
        self.expandsOnDoubleClick()
        self.setIndentation(16)
        self.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.header().setStretchLastSection(False)

    def update_actions(self, force_init=False, force_new_tree=False,
                       filter_on=False, filter_text=""):
        if force_init:
            self.system.init_actions()

        new_actions = [act for act in self.system.parser.get_actions_dict(only_prg=self.only_prg)]
        if new_actions != self.actions or force_new_tree or filter_on:
            self.actions = new_actions
            self.clear()
            self.addTopLevelItems(self.parse_dict(self.actions, filter_text))
            if filter_text != "":
                self.expandAll()
            else:
                self.collapseAll()

    def get_selected_cat(self):
        name = [str(itm.text(0)) for itm in self.selectedItems() if itm.childCount() != 0]
        if len(name) == 1:
            return name[0]
        else:
            return None

    def get_selected_name(self):
        sel_name = [str(itm.text(0)) for itm in self.selectedItems() if itm.childCount() == 0]
        if len(sel_name) == 1:
            sel_name = sel_name[0]
            act = self.system.action_list.get_dict(sel_name)
            if act is not None:
                return act["name"]
            else:
                return None
        elif len(sel_name) > 1:
            print "WARNING: select one action"
            return None

    def parse_dict(self, actions, text=""):
        items = dict()
        text = str(text)
        for act in actions:
            if text.lower() in act.lower() and not act.startswith("__"):
                curr_dict = items
                for cat in self.system.action_list.get_dict(act)["categories"]:
                    if not curr_dict.has_key(cat):
                        curr_dict[cat] = dict()
                    curr_dict = curr_dict[cat]
                curr_dict[act] = None

        def add_items(curr_item):
            new_items = []
            ordering = lambda _ac: "0"+_ac.lower() \
                                   if curr_item[_ac] is not None \
                                   else "1"+_ac.lower()
            new_keys = sorted(curr_item, key=ordering)
            for act in new_keys:
                item = QtGui.QTreeWidgetItem()
                item.setText(0, act)
                item.setToolTip(0, act)
                new_items.append(item)
                if curr_item[act] is not None:
                    item.addChildren(add_items(curr_item[act]))
            return new_items

        return add_items(items)


class ActionsTreeWidget(QtGui.QWidget, object):

    direct_run = QtCore.pyqtSignal(dict)

    def __init__(self, table, parent=None, system=None):
        super(ActionsTreeWidget, self).__init__(parent)

        self.system = system
        self.table = table
        self.tree = ActionsTree(only_prg=False, parent=self, system=self.system)
        layout = QtGui.QVBoxLayout()

        update_button = QtGui.QPushButton("Update actions")
        update_button.setToolTip("update the action list")
        update_button.clicked.connect(partial(self.on_update_actions, force_init=True,
                                              force_new_tree=True))
        layout.addWidget(update_button)

        board_button = QtGui.QPushButton("Reload boards")
        board_button.setToolTip("update and reload the board and action list")
        board_button.clicked.connect(self.on_reload_boards)
        layout.addWidget(board_button)

        create_button = QtGui.QPushButton("Create sub")
        create_button.setToolTip("create a new program")
        create_button.clicked.connect(self.on_create_action)
        layout.addWidget(create_button)

        self.delete_button = QtGui.QPushButton("Delete sub")
        self.delete_button.setToolTip("delete the selected program")
        self.delete_button.clicked.connect(self.on_delete_action)
        self.delete_button.setStyleSheet("QPushButton:enabled{color: %s}"%RED)
        self.delete_button.setEnabled(False)
        layout.addWidget(self.delete_button)

        self.edit_button = QtGui.QPushButton("Edit sub")
        self.edit_button.setToolTip("edit the selected program")
        self.edit_button.clicked.connect(self.on_edit_prg)
        self.edit_button.setEnabled(False)
        layout.addWidget(self.edit_button)

        self.find_text = QtGui.QLineEdit()
        self.find_text.textChanged.connect(self.on_find_event)
        self.find_text.setPlaceholderText("search...")
        self.find_text.setToolTip("filter actions by name")
        layout.addWidget(self.find_text)

        layout.addWidget(self.tree)
        self.setLayout(layout)

        self.tree.doubleClicked.connect(self.on_add_action)

        self.tree.itemSelectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self):
        prg_action = self.tree.get_selected_name()
        if prg_action is not None and self.system.action_list.is_program(prg_action):
            self.edit_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)

    def on_find_event(self, text):
        self.tree.update_actions(force_init=False, force_new_tree=False,
                                 filter_on=True, filter_text=str(text))

    def on_update_actions(self, evt=None, force_init=True, force_new_tree=False):
        self.tree.update_actions(force_init=force_init,
                                 force_new_tree=force_new_tree,
                                 filter_text=str(self.find_text.text()))

    def on_reload_boards(self, evt=None):
        reply = QtGui.QMessageBox.question(self, 'Reload boards',
                                           "Are you sure to reload the board and action list, and to loose the internal boards initialization?",
                                           QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                           QtGui.QMessageBox.No)
        reply = reply == QtGui.QMessageBox.Yes
        if reply:
            self.system.init_boards()
            self.on_update_actions(force_init=True, force_new_tree=True)

    def on_delete_action(self, evt=None):
        prg_action = self.tree.get_selected_name()
        if prg_action == self.table.prg_name:
            QtGui.QMessageBox.about(self, "Error", "Cannot delete the currently opened program")
        elif self.system.action_list.is_program(prg_action):
            reply = QtGui.QMessageBox.question(self, 'Delete program',
                                               "Are you sure to delete program '%s'?"%prg_action,
                                               QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                               QtGui.QMessageBox.No)
            reply = reply == QtGui.QMessageBox.Yes
            if reply:
                self.system.parser.delete_program_file(prg_action)
                self.table.clear_prg_from_memory(prg_action)
                self.table.actions_updated.emit()

    def on_add_action(self, evt=None):
        prg_action = self.system.action_list.get_dict(self.tree.get_selected_name())

        if prg_action is not None:
            prg_action["time"] = self.system.set_time(0.0)
            prg_action["time_rel"] = self.system.set_time(0.0)
            prg_action["enable"] = True

            if not self.table.extended_view:
                win = gui.editdialogs.LineEditDialog(prg_action=prg_action,
                                                     par_table=self.table,
                                                     parent=self,
                                                     system=self.system)

                self.table.add_dialog()

                def on_accepted(win):
                    self.table.add_line(win.get_action())
                    self.table.remove_dialog()

                def on_rejected():
                    self.table.remove_dialog()

                win.accepted.connect(partial(on_accepted, win))
                win.rejected.connect(on_rejected)
                win.direct_run.connect(self.direct_run.emit)
                win.show()

    def on_edit_prg(self, evt=None):
        prg_action = self.tree.get_selected_name()
        if self.system.action_list.is_program(prg_action):
            if prg_action == self.table.prg_name:
                QtGui.QMessageBox.about(self, "Error", "Cannot open the currently opened program")
            else:
                self.table.add_dialog()
                win = gui.editdialogs.ProgramEditDialog(prg_name=prg_action,
                                                        par_table=self.table,
                                                        parent=self,
                                                        system=self.system)

                win.accepted.connect(self.table.remove_dialog)
                win.rejected.connect(self.table.remove_dialog)
                win.show()

    def on_create_action(self, evt=None):
        self.table.add_dialog()
        win = gui.editdialogs.ProgramEditDialog(prg_name=None,
                                                par_table=self.table,
                                                parent=self,
                                                system=self.system)
        win.accepted.connect(self.table.remove_dialog)
        win.rejected.connect(self.table.remove_dialog)
        win.show()
