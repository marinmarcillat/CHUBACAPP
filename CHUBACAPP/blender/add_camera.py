from PyQt5.QtWidgets import QDialog
from CHUBACAPP.blender.add_camera_ui import Ui_Dialog


class AddCameraWindow(QDialog, Ui_Dialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)

    def get_value(self):
        name = self.name.text()
        ocm = [
            [float(self.cm1.text()), float(self.cm2.text()), float(self.cm3.text())],
            [float(self.cm4.text()), float(self.cm5.text()), float(self.cm6.text())],
            [float(self.cm7.text()), float(self.cm8.text()), float(self.cm9.text())]
        ]
        dist_coeff = [float(self.d1.text()), float(self.d2.text()), float(self.d3.text())]
        res = (float(self.he.text()), float(self.wi.text()))

        return name, ocm, dist_coeff, res
