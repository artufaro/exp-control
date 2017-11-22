#!/usr/bin/python2
# -*- coding: utf-8 -*-

# Copyright (C) 2015-2017  Simone Donadello, Carmelo Mordini
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

import os
import numpy as np

import matplotlib
matplotlib.use("Qt4Agg")
import matplotlib.pyplot as plt
#from matplotlib.colors import colorConverter as conv
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT)

from PySide import QtGui, QtCore

from .ui.rampgendialog_ui import Ui_RampGenDialog

class QPushButtonIndexed(QtGui.QPushButton):
    indexSignal = QtCore.Signal(int)
    nextIndexSignal = QtCore.Signal(int)
    def __init__(self, index, *args, **kwargs):
        super(QPushButtonIndexed, self).__init__(*args, **kwargs)
        self.index = index
        self.clicked.connect(self.emit_index)
        self.clicked.connect(self.emit_next_index)

    def emit_index(self):
        self.indexSignal.emit(self.index)
    def emit_next_index(self):
        self.nextIndexSignal.emit(self.index + 1)



class RampGenDialog(QtGui.QDialog, Ui_RampGenDialog):
    def __init__(self, parent, system, *args, **kwargs):
        super(RampGenDialog, self).__init__(parent=parent, *args, **kwargs)
        self.parent = parent
        self.system = system
        self.setupUi(self)
        self.connectUi()
        self.setupPlotWidget(self.rampPlotWidget)

        self._currentRampName = self.parent.settings.last_evap_ramp
        self.rampNameLabel.setText(str(self._currentRampName))
        self.saveDir = os.path.abspath('data/evaporation')
        print(self.saveDir)

        self.headers = ['npoints', 't0', 't1', 'x0', 'x1', 'amp0', 'amp1', 'omit', 'dt', 'slope', 'Add', 'Remove']
        self.headers_row = self.headers[:8]
        self.default_row = dict(zip(self.headers_row,
                                    [100, 0., 100., 60., 50., 1000, 1000, False, ]))
        self.times = np.empty(100,)
        self.freqs = np.empty(100,)
        self.amps  = np.empty(100,)
        self.setupTable(self.table)

    @property
    def currentRampName(self):
        return self._currentRampName
    @currentRampName.setter
    def currentRampName(self, value):
        self._currentRampName = value
        self.parent.settings.last_evap_ramp = value
        self.rampNameLabel.setText(str(value))

    @property
    def fcut(self):
        return self.fcutDoubleSpinBox.value()

    @property
    def edit_slopes(self):
        return self.editSlopesCheckBox.isChecked()
    @property
    def enabled(self):
        return dict(zip(self.headers, [True,
                                      True, not self.edit_slopes,
                                      True, not self.edit_slopes,
                                      True, True, True,
                                      self.edit_slopes, self.edit_slopes,
                                      False, False]))
    @property
    def npoints(self):
        self.npointsLabel.setText(str(int(len(self.times))))
        return len(self.times)

    @property
    def tfinal(self):
        try:
            tf = self.times[-1]
        except IndexError as e:
            print(e)
            tf = np.nan
        self.tfinalLabel.setText(str(tf))
        return tf


    def insertRow(self, index, row=None):
        if row is None:
            row = self.default_row.copy()
            if index > 0:
                print(index)
                lastRow = self.readTableRow(index-1)
                row.update({'t0': lastRow['t1'],
                               't1': lastRow['t1'] + 100.0,
                               'x0': lastRow['x1'],
                               'x1': lastRow['x1'] - 10.0,})
        self.table.insertRow(index)
        self.table.blockSignals(True)
        self.writeTableRow(index, row)
        self.updateARIndices()
        self.table.blockSignals(False)
        print('Added the {:d} row'.format(index+1))


    def removeRow(self, index, force=False):
        if self.table.rowCount() == 1 and not force:
            print("You shouldn't remove the last row!\n")
            return
        self.table.removeRow(index)
        print('Removed the {:d} row'.format(index+1))
        print('There are {:d} rows left\n'.format(self.table.rowCount()))
        self.updateARIndices()
        self.updateRamps()

    def updateARIndices(self):
        add_index = self.headers.index('Add')
        rem_index = self.headers.index('Remove')
        for index in range(self.table.rowCount()):
            self.table.cellWidget(index, add_index).index = index     # i never wrote the word 'index' so many times in a row
            if index > 0:
                self.table.cellWidget(index, rem_index).index = index
        # print 'Add buttons indices:'
        # for index in range(self.table.rowCount()):
        #     print self.table.cellWidget(index, add_index).index

    def clearTable(self,):
        self.table.blockSignals(True)
        for j in range(self.table.rowCount(), 0, -1):
            self.removeRow(j-1, force=True)
        self.table.blockSignals(False)

    def write_formatted_item(self, witem, head, value=None):
        if value is None:
            print 'no writable value: skipping'
        elif head in ['omit',]:
            witem.setCheckState(QtCore.Qt.CheckState(bool(value)))
        elif head in ['npoints', 'amp0', 'amp1',]:
            witem.setText('{:d}'.format(int(value)))
        elif head in ['t0', 't1', 'x0', 'x1',]:
            witem.setText('{:.2f}'.format(float(value)))
        elif head in ['dt', 'slope']:
            witem.setText('{:.4f}'.format(value))
        else:
            print 'no writable head: skipping'

    def enableItem(self, index, col_index):
        witem = self.table.item(index, col_index)
        head = self.headers[col_index]
        status = self.enabled[head]
        # print(status)
        if status:
            witem.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled )  # force-enabling?
            witem.setBackground(QtGui.QColor('white'))
        else:
            witem.setFlags(QtCore.Qt.ItemIsEnabled)    # because this seems to disable
            witem.setBackground(QtGui.QColor('lightGray'))

    def update_enable(self):
        self.table.blockSignals(True)
        for index in range(self.table.rowCount()):
            for col_index in range(self.table.columnCount()):
                self.enableItem(index, col_index)
        self.table.blockSignals(False)

    def writeTableRow(self, index, row):
        for col_index, head in enumerate(self.headers):
            witem = QtGui.QTableWidgetItem()
            value = None
            if head in row:
                value = row[head]
            else:
                if head == 'dt':
                    value = row['t1'] - row['t0']
                elif head == 'slope':
                    try:
                        value = 1e3*(row['x1'] - row['x0'])/(row['t1'] - row['t0'])
                    except ZeroDivisionError as e:
                        print(e)
                        print('Will cast to nan')
                        value = np.nan
                elif head == 'Add':
                    widg = QPushButtonIndexed(index, text='Add',)
                    widg.setAutoDefault(False)
                    self.table.setCellWidget(index, col_index, widg)
                    widg.nextIndexSignal.connect(self.insertRow)
                elif head == 'Remove' and index > 0:
                    widg = QPushButtonIndexed(index, text='Remove')
                    widg.setAutoDefault(False)
                    self.table.setCellWidget(index, col_index, widg)
                    widg.indexSignal.connect(self.removeRow)
                else:
                    pass
            self.write_formatted_item(witem, head, value)
            self.table.setItem(index, col_index, witem)
            self.enableItem(index, col_index)
        self.updateRamps()



    @QtCore.Slot(QtGui.QTableWidgetItem)
    def updateItem(self, witem):
        index, col_index = witem.row(), witem.column()
        head = self.headers[col_index]
        row = self.readTableRow(index) # read updated values and format
        self.table.blockSignals(True)

        self.write_formatted_item(witem, head, row[head]) # first rewrite w. proper format
        # the update the rest of the table accordingly
        if not self.edit_slopes:
            for upd_head in ['dt', 'slope']:
                item = self.table.item(index, self.headers.index(upd_head))
                if upd_head == 'dt':
                    value = row['t1'] - row['t0']
                elif upd_head == 'slope':
                    try:
                        value = 1e3*(row['x1'] - row['x0'])/(row['t1'] - row['t0'])
                    except ZeroDivisionError as e:
                        print(e)
                        print('Will cast to nan')
                        value = np.nan
                self.write_formatted_item(item, upd_head, value)
        else:
            for upd_head in ['x1', 't1']:
                item = self.table.item(index, self.headers.index(upd_head))
                if upd_head == 'x1':
                    value = row['x0'] + 1e-3*row['slope']*row['dt']
                elif upd_head == 't1':
                    value = row['t0'] + row['dt']
                self.write_formatted_item(item, upd_head, value)

        self.table.blockSignals(False)

        ##### extra: join with previous ramp
        ### this is done with signals unblocked --> dt and slope of the previous ramp will update too
        if index > 0 and self.linkRampsCheckBox.isChecked():
            for upd_head in ['x1', 't1']:
                item = self.table.item(index - 1, self.headers.index(upd_head))
                if upd_head == 'x1':
                    value = row['x0']
                elif upd_head == 't1':
                    value = row['t0']
                self.write_formatted_item(item, upd_head, value)
        ##### extra: join with the next
        # if index < self.table.rowCount() and self.linkRampsCheckBox.isChecked():
        #     for upd_head in ['x0', 't0']:
        #         item = self.table.item(index + 1, self.headers.index(upd_head))
        #         if upd_head == 'x0':
        #             value = row['x1']
        #         elif upd_head == 't0':
        #             value = row['t1']
        #         self.write_formatted_item(item, upd_head, value)

        self.updateRamps()

    def readTableRow(self, index):
        row = {}
        for head in self.headers:
            col_index = self.headers.index(head)
            item = self.table.item(index, col_index)
            if head in ['omit',]:
                value = bool(item.checkState())
            elif head in ['npoints', 'amp0', 'amp1',]:
                try:
                    value = int(float(item.text()))
                except ValueError as e:
                    print(e)
                    print('Will cast to 0')
                    value = 0
            elif head in ['t0', 't1', 'x0', 'x1','dt','slope']:
                try:
                    value = float(item.text())
                except ValueError as e:
                    print(e)
                    print('Will cast to nan')
                    value = np.nan
            else: #is reading add/remove
                value = None
            row[head] = value
        return row


    def updateRamps(self):
        t, f, a = [], [], []
        for index in range(self.table.rowCount()):
            row = self.readTableRow(index)
            if not row['omit']:
                t.append(np.linspace(row['t0'], row['t1'], row['npoints'], endpoint=False))
                f.append(np.linspace(row['x0'], row['x1'], row['npoints'], endpoint=False))
                a.append(np.linspace(row['amp0'], row['amp1'], row['npoints'], endpoint=False))
        try:
            self.times = np.concatenate(t)
            self.freqs = np.concatenate(f)
            self.amps = np.concatenate(a)
            self.fcutDoubleSpinBox.setMaximum(self.times.max())
            J = np.where(self.freqs >= self.fcut)[0]
            self.times = self.times[J]
            self.freqs = self.freqs[J]
            self.amps = self.amps[J]
            self.amps[-1] = 1
        except ValueError:
            self.times = np.asarray([])
            self.amps = np.asarray([])
            self.freqs = np.asarray([])
        self.npoints, self.tfinal
        self.plotRamps()

    def plotRamps(self,):
        self.axes_f.cla()
        lf, = self.axes_f.plot(self.times, self.freqs, color='b', label='freq', **self.plot_kwargs)
        self.axes_f.grid(True)
        self.color_axes(self.axes_f, 'b')
        self.axes_a.cla()
        la, = self.axes_a.plot(self.times, self.amps, color='r', label='amp', **self.plot_kwargs)
        self.color_axes(self.axes_a, 'r', position='right')
        lines = [lf, la]
        labels = [line.get_label() for line in lines]
        self.axes_f.legend(lines, labels, loc=3)
        self.canvas.draw()

    def color_axes(self, ax, color, position='left'):
        ax.spines[position].set_color(color)
#        ax.xaxis.label.set_color('red')
        ax.tick_params(axis='y', colors=color)




    def new(self):
        self.clearTable()
        self.insertRow(0)
        self.currentRampName = None

    def load(self, fileName=None):
        if fileName is None or not os.path.isfile(fileName):
            fileName = QtGui.QFileDialog.getOpenFileName(self,'Open file',
                                                         filter='Ramp txt/csv (*.txt *.csv)',
                                                         dir=self.saveDir)[0]
            print('opening file: %s'%fileName)
            if fileName == '':
                print 'no file opening'
                return
            else:
                self.saveDir, self.currentRampName = os.path.split(fileName)
        self.clearTable()
        headers = ['npoints', 't0', 't1', 'x0', 'x1', 'amp0', 'amp1',]
        A = np.genfromtxt(fileName, usecols=(1,2,3,4,5,6,7))
        if len(A.shape) == 1:
            A = A.reshape((1,)+A.shape)
            print A.shape
        for index, values in enumerate(A):
            print values
            row = {'omit': False,}
            row.update(dict(zip(headers, values)))
            self.insertRow(index, row)

    def save_as(self):
        path = QtGui.QFileDialog.getSaveFileName(self,'Save as...',
                                                     filter='Ramp txt/csv (*.txt *.csv)',
                                                     dir=self.saveDir)[0]
        if path == '':
            print 'escaping'
            return
        else:
            self.save_to_txt(path)

    def save_to_txt(self, path=None):
        if path is None:
            if self.currentRampName is None:
                print 'None ramp'
                return
            path = os.path.join(self.saveDir, os.path.splitext(str(self.currentRampName))[0]+'.txt')
        else:
            self.saveDir, self.currentRampName = os.path.split(path)
        headers = ['npoints', 't0', 't1', 'x0', 'x1', 'amp0', 'amp1',]
        A = []
        for j in range(self.table.rowCount()):
            row = self.readTableRow(j)
            A.append(np.asarray([1,] + [row[k] for k in headers]))
        np.savetxt(path, A, fmt=['%d']*2 + ['%.2f']*4 + ['%d']*2)
        print('saved ramp as %s'%path)

    def on_write_out(self,):
        self.save_to_txt()
        self.system.evap_ramp_gen.write_out(times=self.times,
                                            freqs=self.freqs,
                                            amps=self.amps)
        self.close()


    def connectUi(self):
        self.loadPushButton.clicked.connect(self.load)
        self.newPushButton.clicked.connect(self.new)
        self.savePushButton.clicked.connect(self.save_to_txt)
        self.saveAsPushButton.clicked.connect(self.save_as)
        self.fcutDoubleSpinBox.valueChanged.connect(self.updateRamps)
        self.writeOutPushButton.clicked.connect(self.on_write_out)
        self.editSlopesCheckBox.toggled.connect(self.update_enable)

    def setupTable(self, table):
        self.horizHeader = table.horizontalHeader()
        self.vertHeader = table.verticalHeader()
        self.vertHeader.setVisible(True)
        table.setColumnCount(len(self.headers))
        table.setHorizontalHeaderLabels(self.headers)
        table.itemChanged.connect(self.updateItem)
#        table.blockSignals(True)
        if self.currentRampName is None:
            self.insertRow(0)
        else:
            path = os.path.join(self.saveDir, self.currentRampName)
            self.load(path)
        self.setFixedWidth(self.horizHeader.length() + 45)

    def setupPlotWidget(self, plotwidget):
        self.plot_kwargs = {'marker': 'o',
                            'ms': 4,
                            'ls': '-',
                            }
        self.figure, self.axes_f = plt.subplots(1,1, figsize=(4,3))
        self.axes_a = self.axes_f.twinx()
        self.axes_a.plot(np.random.rand(10))
        self.figure.set_facecolor('none')
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, parent=plotwidget, coordinates=False)
        self.toolbar.setOrientation(QtCore.Qt.Horizontal)
        self.plotwidgetLayout = QtGui.QVBoxLayout(plotwidget)
        self.plotwidgetLayout.addWidget(self.canvas)
        self.plotwidgetLayout.addWidget(self.toolbar)
        plotwidget.setLayout(self.plotwidgetLayout)
        self.canvas.draw()
