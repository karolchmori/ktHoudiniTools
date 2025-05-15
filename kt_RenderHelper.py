import hou
from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

parentNode = hou.node('/stage')

class Parameter(object):
    def __init__(self, nodePath, nodeType, paramName, paramType, paramValue):
        self.nodePath = nodePath
        self.nodeType = nodeType
        self.paramName = paramName
        self.paramType = paramType
        self.paramValue = paramValue

    def showInformation(self):
        """ Prints all attributes of the texture object except the `textureMapping` dictionary."""
        print("-----------------------------------------")
        for attribute, value in vars(self).items():  # Iterate over the instance's attributes
            print(f"{attribute}: {value}")
        print("-----------------------------------------")

def getAllNodes(node, nodeList = None, level = 0):
    if nodeList is None:
        nodeList = []
    #print(" " * level + node.name())
    nodeList.append(node.path())

    for child in node.children():
        getAllNodes(child, nodeList, level + 1)

    return nodeList

def getParamNodes(nodeList):
    paramList = []

    for path in nodeList:
        node = hou.node(path)
        nodeType = node.type().name()

        parameters = node.parms()
        for param in parameters:
            paramName = param.name()
            paramType = param.parmTemplate().type()
            
            if paramType.name() == 'String':
                stringType = param.parmTemplate().stringType()
                if stringType.name() == 'FileReference':
                    paramValue = param.eval()
                    if paramValue:
                        newParam = Parameter(nodePath=path, nodeType= nodeType, paramName=paramName, 
                                             paramType=paramType.name(), paramValue=paramValue)
                        paramList.append(newParam)
    
    return paramList

def getHoudiniMainWindow():
    """
    Retrieves the main Houdini window.

    Returns:
        QWidget: The main Houdini Qt window.
    """
    return hou.qt.mainWindow()

class kt_RenderHelper(QtWidgets.QDialog):
    def __init__(self, parent=getHoudiniMainWindow()):
        super(kt_RenderHelper, self).__init__(parent)

        self.setWindowTitle('kt_RenderHelper')
        self.setMinimumWidth(850)
        self.setMinimumHeight(450)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)


        self.createWidgets()
        self.createLayout()
        self.createConnection()
    
    def createWidgets(self):

        self.nodeParentTXT = QtWidgets.QLineEdit()
        self.nodeParentTXT.setReadOnly(True)
        self.nodeParentBTN = hou.qt.NodeChooserButton()

        self.filterCMB = QtWidgets.QComboBox()
        self.filterCMB.setFixedWidth(400)
        self.filterCMB.addItem('')
        self.filterCMB.addItem('$HIP')
        self.filterCMB.addItem('$JOB')
        self.filterCMB.setEditable(True)
        self.filterCMB.setStyleSheet("""
            QComboBox { padding-right: 20px; }
        """)

        self.invertFilterCB = QtWidgets.QCheckBox()

        """
        # Table with results
        self.nodeTBL = QtWidgets.QTableWidget()
        self.nodeTBL.setRowCount(0)
        self.nodeTBL.setColumnCount(5)
        self.nodeTBL.setColumnWidth(0, 150)
        self.nodeTBL.setColumnWidth(1, 140)
        self.nodeTBL.setColumnWidth(2, 60)
        self.nodeTBL.setColumnWidth(3, 200)
        self.nodeTBL.setColumnWidth(4, 200)
        self.nodeTBL.setHorizontalHeaderLabels(["Name","Node","Type","Value","Path"])
        """
        self.nodeTBL = QtWidgets.QTableView()
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Name", "Node", "Type", "Value", "Path"])


        # Proxy model for sorting/filtering
        self.proxyModel = QtCore.QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.model)
        self.proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxyModel.setFilterKeyColumn(-1)  # -1 means filter all columns

        self.nodeTBL.setModel(self.proxyModel)
        self.nodeTBL.verticalHeader().setVisible(False)
        self.nodeTBL.setColumnWidth(0, 150)
        self.nodeTBL.setColumnWidth(1, 140)
        self.nodeTBL.setColumnWidth(2, 60)
        self.nodeTBL.setColumnWidth(3, 240)
        self.nodeTBL.setColumnWidth(4, 200)
        self.nodeTBL.setSortingEnabled(True)

    def createLayout(self):
        """Function that creates all the layouts and add widgets"""
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        """ Header """
        self.nodeLYT = QtWidgets.QHBoxLayout()
        self.nodeLYT.addWidget(QtWidgets.QLabel('Parent: '))
        self.nodeLYT.addWidget(self.nodeParentTXT)
        self.nodeLYT.addWidget(self.nodeParentBTN)
        filterLBL = QtWidgets.QLabel('Filter: ')
        self.nodeLYT.addWidget(filterLBL)
        self.nodeLYT.addWidget(self.filterCMB)
        self.nodeLYT.addStretch()
        self.nodeLYT.addWidget(QtWidgets.QLabel(' Invert: '))
        self.nodeLYT.addWidget(self.invertFilterCB)

        self.mainLayout.addLayout(self.nodeLYT)
        self.mainLayout.addWidget(self.nodeTBL)

    def createConnection(self):
        self.nodeParentBTN.nodeSelected.connect(self.onClick_nodeParentBTN)
        #self.nodeTBL.cellDoubleClicked.connect(self.onCellDoubleClicked_nodeTBL)
        self.nodeTBL.doubleClicked.connect(self.onCellDoubleClicked_nodeTBL)
        self.filterCMB.lineEdit().textChanged.connect(self.proxyModel.setFilterFixedString)
        self.invertFilterCB.stateChanged.connect(self.onInvertFilterChanged)

    def onClick_nodeParentBTN(self, node):
        # Update the parent node
        if node:
            self.nodeParentTXT.setText(str(node.path()))

            # If loaded update table
            self.nodeList = getAllNodes(parentNode)
            self.paramList = getParamNodes(self.nodeList)

            items = []
            # Add to table
            for param in self.paramList:
                variables = [param.paramName, param.nodeType, param.paramType, param.paramValue, param.nodePath]

                items = []
                for value in variables:
                    item = QtGui.QStandardItem(value)
                    item.setToolTip(value)
                    item.setEditable(False)
                    items.append(item)

                self.model.appendRow(items)

                """
                #param.showInformation()
                rowPosition = self.nodeTBL.rowCount()
                self.nodeTBL.insertRow(rowPosition)
                variables = [param.paramName, param.nodeType, param.paramType, param.paramValue, param.nodePath]

                for i in range(self.nodeTBL.columnCount()):
                    item = QtWidgets.QTableWidgetItem(variables[i]) # type QtWidgets.QTableWidgetItem
                    item.setToolTip(variables[i])
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    self.nodeTBL.setItem(rowPosition , i, item)
                """
                


    def onCellDoubleClicked_nodeTBL(self, index: QtCore.QModelIndex):
        sourceIndex = self.proxyModel.mapToSource(index)
        if sourceIndex.column() == 4:
            value = sourceIndex.data()
            print(f"Double-clicked column 4 value: {value}")

    """
    def onCellDoubleClicked_nodeTBL(self, row, column):
        if column == 4:  # Only for column 4, prints the path
            item = self.nodeTBL.item(row, column)
            if item:
                print(f"Double-clicked value: {item.text()}")
    """

try:
    kt_RenderHelper.close()
    kt_RenderHelper.deleteLater()
except:
    pass

ktRenderHelper = kt_RenderHelper()
ktRenderHelper.show()    
    