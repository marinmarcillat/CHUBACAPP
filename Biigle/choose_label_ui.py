# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/choose_label.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Select_label(object):
    def setupUi(self, Select_label):
        Select_label.setObjectName("Select_label")
        Select_label.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(Select_label)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_tree = QtWidgets.QTreeView(Select_label)
        self.label_tree.setObjectName("label_tree")
        self.verticalLayout.addWidget(self.label_tree)
        self.buttonBox = QtWidgets.QDialogButtonBox(Select_label)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Select_label)
        self.buttonBox.accepted.connect(Select_label.accept)
        self.buttonBox.rejected.connect(Select_label.reject)
        QtCore.QMetaObject.connectSlotsByName(Select_label)

    def retranslateUi(self, Select_label):
        _translate = QtCore.QCoreApplication.translate
        Select_label.setWindowTitle(_translate("Select_label", "Choose label"))

