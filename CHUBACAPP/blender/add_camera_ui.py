# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI/add_camera.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(470, 222)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setContentsMargins(-1, -1, -1, 10)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_12 = QtWidgets.QLabel(Dialog)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_4.addWidget(self.label_12)
        self.name = QtWidgets.QLineEdit(Dialog)
        self.name.setObjectName("name")
        self.horizontalLayout_4.addWidget(self.name)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.wi = QtWidgets.QLineEdit(Dialog)
        self.wi.setMaximumSize(QtCore.QSize(100, 16777215))
        self.wi.setAlignment(QtCore.Qt.AlignCenter)
        self.wi.setObjectName("wi")
        self.horizontalLayout_2.addWidget(self.wi)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.he = QtWidgets.QLineEdit(Dialog)
        self.he.setMaximumSize(QtCore.QSize(100, 16777215))
        self.he.setAlignment(QtCore.Qt.AlignCenter)
        self.he.setObjectName("he")
        self.horizontalLayout_2.addWidget(self.he)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_3.addWidget(self.label_4)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.cm7 = QtWidgets.QLineEdit(Dialog)
        self.cm7.setMaximumSize(QtCore.QSize(100, 16777215))
        self.cm7.setAlignment(QtCore.Qt.AlignCenter)
        self.cm7.setObjectName("cm7")
        self.gridLayout.addWidget(self.cm7, 2, 1, 1, 1)
        self.cm1 = QtWidgets.QLineEdit(Dialog)
        self.cm1.setMaximumSize(QtCore.QSize(100, 16777215))
        self.cm1.setAlignment(QtCore.Qt.AlignCenter)
        self.cm1.setObjectName("cm1")
        self.gridLayout.addWidget(self.cm1, 0, 1, 1, 1)
        self.cm4 = QtWidgets.QLineEdit(Dialog)
        self.cm4.setMaximumSize(QtCore.QSize(100, 16777215))
        self.cm4.setAlignment(QtCore.Qt.AlignCenter)
        self.cm4.setObjectName("cm4")
        self.gridLayout.addWidget(self.cm4, 1, 1, 1, 1)
        self.cm6 = QtWidgets.QLineEdit(Dialog)
        self.cm6.setMaximumSize(QtCore.QSize(100, 16777215))
        self.cm6.setAlignment(QtCore.Qt.AlignCenter)
        self.cm6.setObjectName("cm6")
        self.gridLayout.addWidget(self.cm6, 1, 5, 1, 1)
        self.label_6 = QtWidgets.QLabel(Dialog)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 1, 2, 1, 1)
        self.cm2 = QtWidgets.QLineEdit(Dialog)
        self.cm2.setMaximumSize(QtCore.QSize(100, 16777215))
        self.cm2.setAlignment(QtCore.Qt.AlignCenter)
        self.cm2.setObjectName("cm2")
        self.gridLayout.addWidget(self.cm2, 0, 3, 1, 1)
        self.cm3 = QtWidgets.QLineEdit(Dialog)
        self.cm3.setMaximumSize(QtCore.QSize(100, 16777215))
        self.cm3.setAlignment(QtCore.Qt.AlignCenter)
        self.cm3.setObjectName("cm3")
        self.gridLayout.addWidget(self.cm3, 0, 5, 1, 1)
        self.cm5 = QtWidgets.QLineEdit(Dialog)
        self.cm5.setMaximumSize(QtCore.QSize(100, 16777215))
        self.cm5.setAlignment(QtCore.Qt.AlignCenter)
        self.cm5.setObjectName("cm5")
        self.gridLayout.addWidget(self.cm5, 1, 3, 1, 1)
        self.cm9 = QtWidgets.QLineEdit(Dialog)
        self.cm9.setMaximumSize(QtCore.QSize(100, 16777215))
        self.cm9.setAlignment(QtCore.Qt.AlignCenter)
        self.cm9.setObjectName("cm9")
        self.gridLayout.addWidget(self.cm9, 2, 5, 1, 1)
        self.label_5 = QtWidgets.QLabel(Dialog)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)
        self.cm8 = QtWidgets.QLineEdit(Dialog)
        self.cm8.setMaximumSize(QtCore.QSize(100, 16777215))
        self.cm8.setAlignment(QtCore.Qt.AlignCenter)
        self.cm8.setObjectName("cm8")
        self.gridLayout.addWidget(self.cm8, 2, 3, 1, 1)
        self.label_7 = QtWidgets.QLabel(Dialog)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 0, 4, 1, 1)
        self.label_8 = QtWidgets.QLabel(Dialog)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 1, 4, 1, 1)
        self.horizontalLayout_3.addLayout(self.gridLayout)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.label_9 = QtWidgets.QLabel(Dialog)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout.addWidget(self.label_9)
        self.d1 = QtWidgets.QLineEdit(Dialog)
        self.d1.setMaximumSize(QtCore.QSize(100, 16777215))
        self.d1.setAlignment(QtCore.Qt.AlignCenter)
        self.d1.setObjectName("d1")
        self.horizontalLayout.addWidget(self.d1)
        self.label_10 = QtWidgets.QLabel(Dialog)
        self.label_10.setObjectName("label_10")
        self.horizontalLayout.addWidget(self.label_10)
        self.d2 = QtWidgets.QLineEdit(Dialog)
        self.d2.setMaximumSize(QtCore.QSize(100, 16777215))
        self.d2.setAlignment(QtCore.Qt.AlignCenter)
        self.d2.setObjectName("d2")
        self.horizontalLayout.addWidget(self.d2)
        self.label_11 = QtWidgets.QLabel(Dialog)
        self.label_11.setObjectName("label_11")
        self.horizontalLayout.addWidget(self.label_11)
        self.d3 = QtWidgets.QLineEdit(Dialog)
        self.d3.setMaximumSize(QtCore.QSize(100, 16777215))
        self.d3.setAlignment(QtCore.Qt.AlignCenter)
        self.d3.setObjectName("d3")
        self.horizontalLayout.addWidget(self.d3)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem4)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept) # type: ignore
        self.buttonBox.rejected.connect(Dialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Add Camera"))
        self.label_12.setText(_translate("Dialog", "Camera name :"))
        self.label.setText(_translate("Dialog", "Width (px) :"))
        self.wi.setText(_translate("Dialog", "1920"))
        self.label_2.setText(_translate("Dialog", "Height (px) :"))
        self.he.setText(_translate("Dialog", "1080"))
        self.label_4.setText(_translate("Dialog", "Camera matrix :"))
        self.cm7.setText(_translate("Dialog", "0"))
        self.cm1.setText(_translate("Dialog", "0"))
        self.cm4.setText(_translate("Dialog", "0"))
        self.cm6.setText(_translate("Dialog", "0"))
        self.label_6.setText(_translate("Dialog", "fy"))
        self.cm2.setText(_translate("Dialog", "0"))
        self.cm3.setText(_translate("Dialog", "0"))
        self.cm5.setText(_translate("Dialog", "0"))
        self.cm9.setText(_translate("Dialog", "1"))
        self.label_5.setText(_translate("Dialog", "fx"))
        self.cm8.setText(_translate("Dialog", "0"))
        self.label_7.setText(_translate("Dialog", "cx"))
        self.label_8.setText(_translate("Dialog", "cy"))
        self.label_3.setText(_translate("Dialog", "Distortion coeff. :  "))
        self.label_9.setText(_translate("Dialog", "d1"))
        self.d1.setText(_translate("Dialog", "0"))
        self.label_10.setText(_translate("Dialog", "d2"))
        self.d2.setText(_translate("Dialog", "0"))
        self.label_11.setText(_translate("Dialog", "d3"))
        self.d3.setText(_translate("Dialog", "0"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())