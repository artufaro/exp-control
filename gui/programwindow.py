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
# copyramp button
from subprocess import call

from gui.constants import RED, GREEN, BLUE
import gui.programwidget
import gui.defaultsettings
import gui.plotactions
import gui.commandwidget

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore

class ProgramEditWindow(QtGui.QMainWindow, object):

    def __init__(self, system):
        super(ProgramEditWindow, self).__init__()

        self.system = system

        self.progressbar_step_ms = 200.0
        self.progressbar_step = 0
        self.progressbar_duration = 0
        self.progressbar = QtGui.QProgressBar()

        self.iter_timer = QtCore.QTimer()
        self.iter_time = 0
        self.progressbar_timer = QtCore.QTimer()

        self.iter_flag = False
        self.iter_num = 0

        self.init_ui()

    def init_ui(self):
        main_widget = QtGui.QWidget(self)
        main_layout = QtGui.QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.settings = gui.defaultsettings.DefaultProgSettings()
        self.settings.load_settings()

        right_widget = QtGui.QWidget(self)

        self.cmd_init_edit = QtGui.QTextEdit("")
        self.cmd_loop_edit = QtGui.QTextEdit("")

        self.table_widget = gui.programwidget.ProgramEditWidget(parent=self, system=self.system)
        self.table_widget.table.program_opened.connect(self.on_program_opened)
        self.table_widget.table.program_sent.connect(self.start_progressbar_loading)
        self.table_widget.table.fpgas_updated.connect(self.on_update_fpgas)
        if self.settings.last_prg == "":
            prg_name = None
        else:
            prg_name = self.settings.last_prg
        self.table_widget.table.open_prg(prg_name=prg_name)

        right_layout = QtGui.QGridLayout(right_widget)

        right_widget.setMinimumWidth(160)
        right_widget.setMaximumWidth(350)

        main_layout.addWidget(self.table_widget)
        main_layout.addWidget(right_widget)

        open_button = QtGui.QPushButton("Open prg")
        open_button.setToolTip("open a program")
        open_button.clicked.connect(partial(self.table_widget.table.open_prg, ask_name=True))
        right_layout.addWidget(open_button, 0, 0, 1, 1)

        open_new_button = QtGui.QPushButton("New prg")
        open_new_button.setToolTip("open a new program")
        open_new_button.clicked.connect(partial(self.table_widget.table.open_prg, prg_name=None))
        right_layout.addWidget(open_new_button, 0, 1, 1, 1)

        save_button = QtGui.QPushButton("Save prg")
        save_button.setToolTip("save current program")
        save_button.clicked.connect(self.table_widget.table.save_prg)
        save_button.setStyleSheet("color: %s"%GREEN)
        right_layout.addWidget(save_button, 1, 0, 1, 1)

        save_as_button = QtGui.QPushButton("Save prg as")
        save_as_button.setToolTip("save current program with a new name")
        save_as_button.clicked.connect(self.table_widget.table.save_prg_as)
        save_as_button.setStyleSheet("color: %s"%GREEN)
        right_layout.addWidget(save_as_button, 1, 1, 1, 1)

        self.save_before_send_check = QtGui.QCheckBox("save before send")
        self.save_before_send_check.setToolTip("save current program before sending it to FPGAs")
        self.save_before_send_check.setChecked(True)
        right_layout.addWidget(self.save_before_send_check, 2, 0, 1, 2)

        send_button = QtGui.QPushButton("Send program")
        send_button.setToolTip("send current program to the FPGAs")
        send_button.clicked.connect(self.on_program_sent)
        send_button.setStyleSheet("color: %s"%BLUE)
        right_layout.addWidget(send_button, 3, 0, 1, 2)

        plot_button = QtGui.QPushButton("Plot acts")
        plot_button.setToolTip("graphical representation for the program actions")
        plot_button.clicked.connect(self.on_plot_actions)
        right_layout.addWidget(plot_button, 4, 0, 1, 1)

        plot_button = QtGui.QPushButton("Check prg")
        plot_button.setToolTip("perform a validity check for the program actions")
        plot_button.clicked.connect(self.on_check_program)
        right_layout.addWidget(plot_button, 4, 1, 1, 1)

        update_fpga_button = QtGui.QPushButton("Reload FPGAs")
        update_fpga_button.setToolTip("initialize the FPGA list")
        update_fpga_button.clicked.connect(partial(self.table_widget.table.update_fpgas, init=True))
        right_layout.addWidget(update_fpga_button, 5, 0, 1, 1)

        check_fpga_button = QtGui.QPushButton("Check FPGAs")
        check_fpga_button.setToolTip("check the state of the FPGA list")
        check_fpga_button.clicked.connect(partial(self.table_widget.table.update_fpgas, init=False))
        right_layout.addWidget(check_fpga_button, 5, 1, 1, 1)

		# copyramp button:
        # added button
        # connected to on_copyramp defined at line 279
        # moved iter_cmd_tabwidget from 6 to 7
        copyramp_button = QtGui.QPushButton("Copy Evaporation ramp")
        copyramp_button.setToolTip("copies and translates the ramp from the little computer")
        copyramp_button.clicked.connect(self.on_copyramp)
        copyramp_button.setStyleSheet("color: %s"%RED)
        right_layout.addWidget(copyramp_button, 6, 0, 1, 2)


        #iterations/commands tab
        iter_cmd_tabwidget = QtGui.QTabWidget(self)
        cmd_widget = gui.commandwidget.CommandWidget(init_edit=self.cmd_init_edit,
                                                     loop_edit=self.cmd_loop_edit)
        
        #commands tab connections
        cmd_widget.start_cmd_button.clicked.connect(self.on_start_cmd)
        cmd_widget.stop_cmd_button.clicked.connect(self.on_stop_cmd)
        self.cmd_loop_edit.textChanged.connect(self.on_cmd_changed)
        self.cmd_init_edit.textChanged.connect(self.on_cmd_changed)
        
        
        iter_widget = QtGui.QWidget()
        iter_layout = QtGui.QVBoxLayout(iter_widget)
        iter_cmd_tabwidget.addTab(iter_widget, "Iterations")
        iter_cmd_tabwidget.addTab(cmd_widget, "Commands")

        right_layout.addWidget(iter_cmd_tabwidget, 7, 0, 1, 2)


        #iterations parameters group
        self.iter_par_groupbox = QtGui.QGroupBox("Iter program")
        iter_par_layout = QtGui.QGridLayout(self.iter_par_groupbox)

        #current program iterating label
        self.iter_prg_label = QtGui.QLabel("")
        self.iter_prg_label.setToolTip("")

        #label of the remaining iterations
        self.iter_current_label = QtGui.QLabel("")

        #setter of the number of iters
        self.iter_num_text = QtGui.QSpinBox()
        self.iter_num_text.setMaximum(999)
        self.iter_num_text.setMinimum(-1)
        self.iter_num = 0
        self.iter_num_text.setValue(self.iter_num)
        self.iter_num_text.setToolTip("number of times that the program will be repeated, use -1 for infinite loop")

        #repeat when the program finish with and additional time (button + value)
        self.iter_cont_time_text = QtGui.QLineEdit("100.0")
        self.iter_cont_time_text.setToolTip("safety time (in ms) between the end of the previous program and the new iteration")
        self.iter_cont_button = QtGui.QRadioButton("continuously")
        self.iter_cont_button.setToolTip("repeat the same program after the end of the previous iteration")
        self.iter_cont_button.setChecked(True)

        #repeat the program at a fixed time (button + value)
        self.iter_fixed_time_text = QtGui.QLineEdit("60000.0")
        self.iter_fixed_time_text.setToolTip("time (in ms) between each iteration")
        self.iter_fixed_button = QtGui.QRadioButton("fixed time")
        self.iter_fixed_button.setToolTip("repeat the same program after a fixed time")

        #set iter parameters layout
        iter_par_layout.addWidget(self.iter_prg_label, 0, 0, 1, 2)
        iter_par_layout.addWidget(QtGui.QLabel("iterations #"), 1, 0, 1, 1)
        iter_par_layout.addWidget(self.iter_num_text, 1, 1, 1, 1)
        iter_par_layout.addWidget(self.iter_cont_button, 2, 0, 1, 1)
        iter_par_layout.addWidget(self.iter_cont_time_text, 2, 1, 1, 1)
        iter_par_layout.addWidget(self.iter_fixed_button, 3, 0, 1, 1)
        iter_par_layout.addWidget(self.iter_fixed_time_text, 3, 1, 1, 1)
        iter_par_layout.addWidget(self.iter_current_label, 4, 0, 1, 2)

        #iter start/stop
        self.iter_start_button = QtGui.QPushButton("Start/Stop")
        self.iter_start_button.setToolTip("begin or interrupt to repeat a program with the given parameters")
        self.iter_start_button.setCheckable(True)
        self.iter_start_button.clicked.connect(self.on_start_stop_iter)
        self.stop_iter_buttons()

        #set iterations layout
        iter_layout.addWidget(self.iter_par_groupbox)
        iter_layout.addWidget(self.iter_start_button)
        iter_layout.addStretch()


        statusbar = self.statusBar()

        self.progressbar.setToolTip("progress of the currently running program and remaining seconds")
        statusbar.addPermanentWidget(self.progressbar, 3)
        self.progressbar.setMinimum(0)
        self.progressbar.setMaximum(100)
        self.progressbar.setValue(0)

        self.fpga_count_label = QtGui.QLabel("")

        self.fpga_status_label = QtGui.QWidget()
        self.fpga_count_label.setMinimumWidth(70)
        self.fpga_status_label.setMinimumWidth(350)
        statusbar.addPermanentWidget(self.fpga_count_label, 1)
        statusbar.addPermanentWidget(self.fpga_status_label, 3)

        fpga_layout = QtGui.QHBoxLayout(self.fpga_status_label)
        self.fpga_status_labels = []
        for _ in range(5):
            labl = QtGui.QLabel(self)
            self.fpga_status_labels.append(labl)
            fpga_layout.addWidget(labl)

        self.set_progressbar_value(0)
        self.table_widget.table.update_fpgas(init=False)

    def on_copyramp(self):
        #call('rsync -v bec@10.194.33.62:~/RampGenerator/"Evaporation\ Ramp.sub" ./test/Evaporation\ Ramp.sub',
        #     shell=True)
        #call('python ./test/labview_converter_evapramp_data.py', shell=True)
		call('sh ./copyramp/copyramp.sh', shell=True)

    def on_cmd_changed(self):
        self.table_widget.table.cmd_str = (str(self.cmd_init_edit.toPlainText()),
                                           str(self.cmd_loop_edit.toPlainText()))

    def on_start_stop_iter(self):
        self.iter_flag = bool(self.iter_start_button.isChecked())
        repeat_after_complete = bool(self.iter_cont_button.isChecked())
        repeat_at = bool(self.iter_fixed_button.isChecked())
        repeat_after_complete_time = float(self.iter_cont_time_text.text())
        repeat_at_time = float(self.iter_fixed_time_text.text())
        self.iter_num = int(self.iter_num_text.value())
        if self.iter_flag:
            self.on_iter_take_prg()
            self.iter_start_button.setStyleSheet("color: %s"%RED)
            self.iter_par_groupbox.setEnabled(False)
            self.on_iter()

            if self.iter_flag:
                if repeat_after_complete:
                    prg_time = self.system.get_time(self.system.get_program_time())
                    self.iter_time = int(prg_time + repeat_after_complete_time)
                elif repeat_at:
                    self.iter_time = int(repeat_at_time)
                else:
                    self.iter_time = 0

                self.iter_timer = QtCore.QTimer()
                self.iter_timer.timeout.connect(self.on_iter)
                self.iter_timer.start(self.iter_time)
        else:
            self.stop_iter_buttons()

    def on_iter(self):
        if self.iter_flag:

            if self.iter_num != 0:
                if self.iter_num > 0:
                    self.iter_num -= 1
                    self.iter_current_label.setText("%d iterations remaining"%self.iter_num)
                elif self.iter_num < 0:
                    self.iter_current_label.setText("infinite iterations")

                self.iter_timer.stop()
                result = self.table_widget.table.send_prg(prg_name="__temp_iter")
                if result:
                    self.iter_timer = QtCore.QTimer()
                    self.iter_timer.timeout.connect(self.on_iter)
                    self.iter_timer.start(self.iter_time)
                else:
                    self.iter_flag = False
                    self.stop_iter_buttons()
            else:
                self.iter_flag = False
                self.stop_iter_buttons()
                self.iter_timer.stop()

    def stop_iter_buttons(self):
        self.iter_start_button.setChecked(False)
        self.iter_start_button.setStyleSheet("color: %s"%BLUE)
        self.iter_par_groupbox.setEnabled(True)
        self.iter_current_label.setText("")

    def on_iter_take_prg(self):
        if bool(self.save_before_send_check.isChecked()):
            self.table_widget.table.save_prg(prg_name="__temp_iter",
                                             prg_list=self.table_widget.table.prg_list(),
                                             categories=[], cmd_str=("",""))
            self.iter_prg_label.setText("\"%s\""%self.table_widget.table.prg_name)
            self.iter_prg_label.setToolTip("the program that will be repeated is a snapshot of \"%s\""%self.table_widget.table.prg_name)

    def on_program_sent(self, evt=None):
        self.table_widget.table.send_prg(save_before=bool(self.save_before_send_check.isChecked()))

    def on_start_cmd(self, evt=None):
        if not self.system.sys_commands_running():
            if bool(self.save_before_send_check.isChecked()):
                self.table_widget.table.save_prg()
            self.system.set_program(self.table_widget.table.prg_name)
            self.system.run_sys_commands()

    def on_stop_cmd(self, evt=None):
        if self.system.sys_commands_running():
            self.system.stop_sys_commands()

    def on_update_fpgas(self, status):
        state_text = "FPGAs connected:%1d"%len(status)
        state_details_tip = ""

        for f_num, f_lab in enumerate(self.fpga_status_labels):
            if f_num < len(status):
                state = status[f_num]
                if state.running:
                    running = "run"
                    f_lab.setStyleSheet("color: %s"%RED)
                else:
                    running = "ready"
                    f_lab.setStyleSheet("color: %s"%GREEN)
                f_lab.setText("FPGA%1d:%s"%(f_num, running.ljust(5)))
                state_details_tip += "FPGA%1d:\n"%f_num + str(state)

                if f_num+1 != len(status):
                    state_details_tip += "\n------\n"
            else:
                f_lab.setText("")
                f_lab.setStyleSheet("background-color: transparent")

        self.fpga_count_label.setText(state_text)
        self.fpga_count_label.setToolTip(state_details_tip)

    def on_plot_actions(self):
        win = gui.plotactions.PlotActionsDialog(table=self.table_widget.table,
                                                parent=self)
        win.show()

    def on_check_program(self):
        self.table_widget.table.check_prg()

    def on_program_opened(self, title, comment):
        self.table_widget.set_title(title, comment)
        self.cmd_init_edit.blockSignals(True)
        self.cmd_loop_edit.blockSignals(True)
        self.cmd_init_edit.setText(self.table_widget.table.cmd_str[0])
        self.cmd_loop_edit.setText(self.table_widget.table.cmd_str[1])
        self.cmd_init_edit.blockSignals(False)
        self.cmd_loop_edit.blockSignals(False)
        self.settings.last_prg = title

    def closeEvent(self, event):
        self.settings.save_settings()
        event.accept()

    def start_progressbar_loading(self, result):
        if result:
            self.progressbar_duration = int(self.system.get_time(self.system.get_program_time()))
            self.progressbar_step = 0
            self.progressbar_timer.stop()

            self.progressbar_timer = QtCore.QTimer()
            self.progressbar_timer.timeout.connect(self.update_progressbar)
            self.progressbar_timer.start(self.progressbar_step_ms)

        self.table_widget.table.update_fpgas(init=False)

    def set_progressbar_value(self, value, time=0):
        diff = self.progressbar_duration - time
        if diff < 0:
            diff = 0
        self.progressbar.setFormat("%d%%  (%ds)"%(value, round(diff*self.system._time_multiplier)))
        self.progressbar.setValue(value)

    def update_progressbar(self):
        if self.progressbar_duration != 0:
            value_ms = self.progressbar_step*self.progressbar_step_ms
            value = int(value_ms/self.progressbar_duration*100)
        else:
            value = value_ms = 0

        if self.progressbar_step > 2 + (self.progressbar_duration/self.progressbar_step_ms):
            self.progressbar_timer.stop()
            self.progressbar_step = value = 0
            self.table_widget.table.update_fpgas(init=False)
        else:
            self.progressbar_step += 1

        if value >= 100:
            value = 100

        self.set_progressbar_value(value, value_ms)
