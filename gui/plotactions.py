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


from functools import partial

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui

import matplotlib
matplotlib.use("Qt4Agg")
matplotlib.rcParams['font.size'] = 9
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT


class NavigationToolbar(NavigationToolbar2QT):
    toolitems = [t for t in NavigationToolbar2QT.toolitems if \
                 t[0] in ('Home', 'Pan', 'Zoom', 'Save')]


class FigureCanvas(FigureCanvasQTAgg):
    def __init__(self, parent_axis=None, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(FigureCanvas, self).__init__(self.fig)
        self.setParent(parent)

        self.axis = self.fig.add_subplot(111, sharex=parent_axis)
        self.fig.tight_layout(pad=3)
        self.axis.ticklabel_format(useOffset=False)


class DigitalCanvas(FigureCanvas):
    def __init__(self, *args, **kwargs):
        super(DigitalCanvas, self).__init__(height=2, *args, **kwargs)
        self.axis.set_yticks([])


class AnalogCanvas(FigureCanvas):
    def __init__(self, *args, **kwargs):
        super(AnalogCanvas, self).__init__(height=6, *args, **kwargs)
        self.axis2 = self.axis.twinx()


class AvaiableActions(QtGui.QTableWidget, object):
    columns = [("name", 120),
               ("y1", 30),
               ("y2", 30),
               ("col", 40),
               ("sty", 40)]
    actions_updated = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(AvaiableActions, self).__init__(0, len(self.columns),
                                              parent=parent)
        self.acts = dict()
        self.setHorizontalHeaderLabels([col[0] for col in self.columns])

    def set_acts(self, acts):
        self.acts = acts

        self.clear()
        self.setRowCount(len(self.acts))
        self.setHorizontalHeaderLabels([col[0] for col in self.columns])
        for n_col, col in enumerate(self.columns):
            self.setColumnWidth(n_col, col[1])

        for n_row, row in enumerate(sorted(self.acts.keys())):
            itm = QtGui.QTableWidgetItem(str(row))
            itm.setFlags(itm.flags()&~QtCore.Qt.ItemIsEditable)
            itm.setToolTip(str(row))
            self.setItem(n_row, 0, itm)

            check_y1 = QtGui.QCheckBox()
            check_y2 = QtGui.QCheckBox()
            self.setCellWidget(n_row, 1, check_y1)
            check_y1.stateChanged.connect(partial(self.on_state_changed,
                                                  n_row=n_row, n_col=1))
            self.setCellWidget(n_row, 2, check_y2)
            check_y2.stateChanged.connect(partial(self.on_state_changed,
                                                  n_row=n_row, n_col=2))

            combo_col = ColorCombo()
            combo_sty = StyleCombo()
            col = self.acts[row]["plot_col"]
            combo_col.setCurrentIndex([cl[0] for cl in ColorCombo.colors].index(col))
            self.setCellWidget(n_row, 3, combo_col)
            combo_col.currentIndexChanged.connect(partial(self.on_state_changed,
                                                          n_row=n_row, n_col=3))
            sty = self.acts[row]["plot_sty"]
            combo_sty.setCurrentIndex(StyleCombo.styles.index(sty))
            self.setCellWidget(n_row, 4, combo_sty)
            combo_sty.currentIndexChanged.connect(partial(self.on_state_changed,
                                                          n_row=n_row, n_col=4))

    def on_state_changed(self, n_row, n_col):
        widget = self.cellWidget(n_row, n_col)
        item = sorted(self.acts.keys())[n_row]
        if n_col in [1, 2]:
            n_other = [2, 1][n_col-1]
            self.acts[item]["plot_y"+str(n_col)] = bool(widget.isChecked())
            if self.acts[item]["plot_y"+str(n_col)]:
                self.acts[item]["plot_y"+str(n_other)] = not bool(widget.isChecked())
                wid_other = self.cellWidget(n_row, n_other)
                wid_other.blockSignals(True)
                wid_other.setChecked(self.acts[item]["plot_y"+str(n_other)])
                wid_other.blockSignals(False)
        elif n_col == 3:
            self.acts[item]["plot_col"] = str(widget.currentText())
        elif n_col == 4:
            self.acts[item]["plot_sty"] = str(widget.currentText())
        self.actions_updated.emit()


class ColorCombo(QtGui.QComboBox):
    colors = [("r", QtCore.Qt.red),
              ("b", QtCore.Qt.blue),
              ("c", QtCore.Qt.cyan),
              ("g", QtCore.Qt.green),
              ("m", QtCore.Qt.magenta),
              ("y", QtCore.Qt.darkYellow),
              ("k", QtCore.Qt.gray)]
    def __init__(self):
        super(ColorCombo, self).__init__()

        for n_col, col in enumerate(self.colors):
            self.addItem(col[0])
            self.setItemData(n_col,
                             QtGui.QColor(col[1]),
                             QtCore.Qt.BackgroundRole)


class StyleCombo(QtGui.QComboBox):
    styles = ["-", "--", "-.", ":"]
    def __init__(self):
        super(StyleCombo, self).__init__()

        self.addItems(self.styles)


class PlotActionsDialog(QtGui.QDialog, object):
    def __init__(self, table, parent=None):
        super(PlotActionsDialog, self).__init__(parent=parent)

        self.table = table
        self.actions = []
        self.avaiable_acts = dict()

        layout = QtGui.QGridLayout()
        self.setLayout(layout)

        self.actions_table = AvaiableActions(parent=self)
        self.plot2 = DigitalCanvas(parent=self)
        self.plot1 = AnalogCanvas(parent_axis=self.plot2.axis, parent=self)
        toolbar = NavigationToolbar(self.plot1, self)

        update_button = QtGui.QPushButton("Update actions")
        update_button.clicked.connect(self.update_acts)
        self.check_legend = [QtGui.QCheckBox("legend y1"),
                             QtGui.QCheckBox("legend y2")]
        for chck in self.check_legend:
            chck.setChecked(True)
            chck.stateChanged.connect(self.plot)

        legend_widget = QtGui.QWidget()
        legend_layout = QtGui.QHBoxLayout(legend_widget)
        legend_layout.addStretch()
        legend_layout.addWidget(update_button)
        legend_layout.addWidget(self.check_legend[0])
        legend_layout.addWidget(self.check_legend[1])

        layout.addWidget(self.actions_table, 0, 0, 5, 1)
        layout.addWidget(toolbar, 0, 1)
        layout.addWidget(self.plot1, 1, 1, 3, 1)
        layout.addWidget(self.plot2, 4, 1, 1, 1)
        layout.addWidget(legend_widget, 5, 0, 1, 2)

        self.setFocus()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.resize(800, 400)
        self.setWindowState(QtCore.Qt.WindowMaximized)

        self.actions_table.actions_updated.connect(self.plot)
        self.update_acts()

    def update_acts(self):
        self.setWindowTitle("Plot actions of program \"%s\""%self.table.prg_name)
        self.actions = self.table.get_all(lst=self.table.prg_list(),
                                          time=self.table.system.set_time(0.0),
                                          enable=True,
                                          enable_parent=True,
                                          extended=True)
        acts2 = self.table.get_all(lst=self.table.prg_list(),
                                    time=self.table.system.set_time(0.0),
                                    enable=True,
                                    enable_parent=True,
                                    extended=False)
        self.actions += [act for act in acts2 if act["is_subprg"]]
        avaiable_acts = dict()
        for act in self.actions:
            name = act["name"]
            if name not in avaiable_acts:
                col = ColorCombo.colors[hash(name)%len(ColorCombo.colors)][0]
                sty = StyleCombo.styles[(hash(name)+13)%len(StyleCombo.styles)]
                if act["is_subprg"]:
                    act_time = self.table.system.get_program_time(act["name"],
                                                                  **act["vars"])
                else:
                    act_time = None
                avaiable_acts[name] = dict(plot_y1=False,
                                           plot_y2=False,
                                           plot_col=col,
                                           plot_sty=sty,
                                           delta_t=act_time)

                var = act["vars"]
                if len(var) == 1:
                    var = var.keys()[0]
                else:
                    var = None
                avaiable_acts[name]["var"] = var

        if avaiable_acts.keys() != self.avaiable_acts.keys():
            self.avaiable_acts = avaiable_acts
            self.actions_table.set_acts(self.avaiable_acts)
        self.plot()

    def plot(self):
        self.plot1.axis.cla()
        self.plot1.axis2.cla()
        self.plot2.axis.cla()
        self.plot2.axis.set_yticks([])
        self.plot1.axis.ticklabel_format(useOffset=False)
        self.plot1.axis2.ticklabel_format(useOffset=False)
        self.plot2.axis.ticklabel_format(useOffset=False)

        for act_name in sorted(self.avaiable_acts.keys()):
            act = self.avaiable_acts[act_name]
            if act["plot_y1"] or act["plot_y2"]:
                var_name = act["var"]
                x = []
                y = []
                for row in self.actions:
                    if row["name"] == act_name and row["enable"] and row["enable_parent"]:
                        x.append(self.table.system.get_time(row["time"]))
                        if var_name is not None:
                            y.append(row["vars"][var_name])
                        else:
                            y.append(None)
                if len(x) > 1:
                    x, y = (list(t) for t in zip(*sorted(zip(x, y))))

                col = act["plot_col"]
                if col == "":
                    col = "k"
                sty = act["plot_sty"]
                if sty == "":
                    sty = "-"

                if act["plot_y1"]:
                    plt_ax = self.plot1.axis
                else:
                    plt_ax = self.plot1.axis2
                if var_name is not None:
                    plt_ax.plot(x, y, col+"o", markersize=4, alpha=0.75)
                    plt_ax.step(x, y, col, linestyle=sty, where="post",
                                label=act_name, linewidth=2, alpha=0.5)
                else:
                    plt_ax.plot([], [], col+sty, label=act_name)

                self.plot2.axis.vlines(x, 0, 1, color=col, linestyles=sty,
                                       linewidth=2, alpha=0.5)
                if act["delta_t"] is not None:
                    delta_t = self.table.system.get_time(act["delta_t"])
                    for x_ in x:
                        self.plot2.axis.axvspan(x_, x_+delta_t, 0, 1,
                                                color=col, alpha=0.25)
                self.plot2.axis.set_xlim(auto=True)

        if self.check_legend[0].isChecked() \
                and len(self.plot1.axis.get_legend_handles_labels()[0]) > 0:
            self.plot1.axis.legend(loc="lower left", title="scale y1")
        if self.check_legend[1].isChecked() \
                and len(self.plot1.axis2.get_legend_handles_labels()[0]) > 0:
            self.plot1.axis2.legend(loc="lower right", title="scale y2")
        self.plot1.draw()
        self.plot2.draw()
