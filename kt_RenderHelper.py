import hou
from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

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

            if 'primpattern' in paramName:
                print(param.parmTemplate())
                print(param.unexpandedString()) # TODO:  "`lopinputprims('.', 0)`" means default???

            if paramType.name() == 'String':
                stringType = param.parmTemplate().stringType()
                
                if stringType.name() == 'FileReference':
                    paramValue = param.unexpandedString()
                    if paramValue:
                        newParam = Parameter(nodePath=path, nodeType= nodeType, paramName=paramName, 
                                             paramType=paramType.name(), paramValue=paramValue)
                        paramList.append(newParam)
                elif stringType.name() == 'Regular':
                    if paramName == 'xn__primvarsarnoldsubdiv_type_uhbg': # FIX
                        pass
                        #print(param.isDisabled()) # TODO: To check if the parameter is Set to create (True) or Do nothing (False)

            elif paramType.name() == 'Toggle':
                pass
            elif paramType.name() == 'Float':
                pass
            elif paramType.name() == 'Int':
                pass
            elif paramType.name() == 'Menu':
                pass
                
    
    return paramList

def getHoudiniMainWindow():
    """
    Retrieves the main Houdini window.

    Returns:
        QWidget: The main Houdini Qt window.
    """
    return hou.qt.mainWindow()


class InvertibleFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._invert = False
        self._filterText = ""

    def setInvert(self, invert: bool):
        self._invert = invert
        self.invalidateFilter()  # refresh filtering

    def setFilterText(self, text: str):
        self._filterText = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        # If no filter text, accept everything
        if not self._filterText:
            return True if not self._invert else False

        model = self.sourceModel()
        column_count = model.columnCount()

        # Check if any column contains the filter text (case insensitive)
        matched = False
        for column in range(column_count):
            index = model.index(source_row, column, source_parent)
            data = model.data(index)
            if data and self._filterText in str(data).lower():
                matched = True
                break

        # Return True if matched and not inverted; or if NOT matched and inverted
        return matched != self._invert  # XOR logic


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
        self.filterCMB.setFixedWidth(420)
        self.filterCMB.addItem('')
        self.filterCMB.addItem('$HIP')
        self.filterCMB.addItem('$JOB')
        self.filterCMB.setEditable(True)
        self.filterCMB.setStyleSheet("""
            QComboBox { padding-right: 20px; }
        """)

        self.invertFilterCB = QtWidgets.QCheckBox()

        self.nodeTBL = QtWidgets.QTableView()
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Name", "Node", "Type", "Value", "Path"])


        # Proxy model for sorting/filtering
        self.proxyModel = InvertibleFilterProxyModel()
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
        self.nodeTBL.doubleClicked.connect(self.onCellDoubleClicked_nodeTBL)
        self.filterCMB.lineEdit().textChanged.connect(self.proxyModel.setFilterText)
        self.invertFilterCB.stateChanged.connect(lambda _: self.proxyModel.setInvert(self.invertFilterCB.isChecked()))

    def onClick_nodeParentBTN(self, node):
        # Update the parent node
        if node:
            self.nodeParentTXT.setText(str(node.path()))
            self.clearTableView(self.model)
            # If loaded update table
            self.nodeList = getAllNodes(node)
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

    def onCellDoubleClicked_nodeTBL(self, index: QtCore.QModelIndex):
        sourceIndex = self.proxyModel.mapToSource(index)
        if sourceIndex.column() == 4:
            value = sourceIndex.data()
            #print(f"Double-clicked column 4 value: {value}")
            node = hou.node(value)
            if node:
                # Select the node
                node.setSelected(True, clear_all_selected=True)
                
                # Focus on the node in the network editor pane
                # Find the network editor pane that shows this node's context
                for pane in hou.ui.paneTabs():
                    if isinstance(pane, hou.NetworkEditor) and pane.pwd() == node.parent():
                        pane.setCurrentNode(node)
                        pane.bringToFront()
                        break
    
    def clearTableView(self, model):
        for row in reversed(range(model.rowCount())):
            model.removeRow(row)



try:
    kt_RenderHelper.close()
    kt_RenderHelper.deleteLater()
except:
    pass

ktRenderHelper = kt_RenderHelper()
ktRenderHelper.show()    
    