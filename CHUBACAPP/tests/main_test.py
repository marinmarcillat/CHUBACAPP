import unittest
import sys, os
from time import sleep
from pathlib import Path
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from CHUBACAPP import main as chubacapp

app = QApplication(sys.argv)


class interface(unittest.TestCase):
    def setUp(self):
        '''Create the GUI'''
        self.form = chubacapp.Window()
        self.data_path = os.path.join(Path(os.path.realpath(__file__)).parents[2],'example_data')

    def test_3Dplotter(self):
        '''Test the ice slider.
        Testing the minimum and maximum is left as an exercise for the reader.
        '''
        self.form.plot_model_path.setText(os.path.join(self.data_path, 'pl03_chubacapp', 'low_res', 'outReconstruction', 'MyProcessing_0_texrecon.obj'))
        self.form.plot_annotation_path.setText(os.path.join(self.data_path, 'pl03_chubacapp', 'point_output.json'))

        # Push OK with the left mouse button
        QTest.mouseClick(self.form.plot_launch, Qt.LeftButton)
        sleep(10)


if __name__ == '__main__':
    unittest.main()
