from PyQt5.QtWidgets import QDialog
from PyQt5 import QtGui
from CHUBACAPP.Biigle.choose_label_ui import Ui_Select_label
from collections import deque


class SelectWindow(QDialog, Ui_Select_label):
    def __init__(self, tree_label, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self.label_dict = deque(tree_label)
        self.show_tree()

    def show_tree(self):
        seen = {}
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Name', 'ID'])
        self.label_tree.header().setDefaultSectionSize(180)
        self.label_tree.setModel(self.model)

        root = self.model.invisibleRootItem()
        while self.label_dict:
            value = self.label_dict.popleft()
            if value['parent_id'] is None :
                parent = root
            else:
                pid = value['parent_id']
                if pid not in seen:
                    self.label_dict.append(value)
                    continue
                parent = seen[pid]
            id = value['id']
            parent.appendRow([
                QtGui.QStandardItem(value['name']),
                QtGui.QStandardItem(str(id)),
            ])
            seen[id] = parent.child(parent.rowCount() - 1)

        self.label_tree.expandAll()

    def get_value(self):
        index = self.label_tree.selectedIndexes()[0]
        value = index.data()
        i = 0
        while index.sibling(i,0).data() != value:
            i+=1
        id = index.sibling(i,1).data()
        return(id,value)
