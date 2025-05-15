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
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)


        self.createWidgets()
        self.createLayout()
        self.createConnection()
    
    def createWidgets(self):

        self.nodeParentTXT = QtWidgets.QLineEdit()
        self.nodeParentTXT.setReadOnly(True)
        self.nodeParentBTN = hou.qt.NodeChooserButton()

        self.filterCMB = QtWidgets.QComboBox()
        self.filterCMB.setFixedWidth(600)
        self.filterCMB.addItem('')
        self.filterCMB.addItem('$HIP')
        self.filterCMB.addItem('$JOB')
        self.filterCMB.setEditable(True)

        self.invertFilterCB = QtWidgets.QCheckBox()

        self.nodeTBL = QtWidgets.QTableWidget()
        self.nodeTBL.setRowCount(0)
        self.nodeTBL.setColumnCount(5)
        self.nodeTBL.setHorizontalHeaderLabels(["Name","Node","Type","Value","Path"])

    def createLayout(self):
        """Function that creates all the layouts and add widgets"""
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        """ Header """
        self.nodeLYT = QtWidgets.QHBoxLayout()
        self.nodeLYT.addWidget(QtWidgets.QLabel('Parent: '))
        self.nodeLYT.addWidget(self.nodeParentTXT)
        self.nodeLYT.addWidget(self.nodeParentBTN)

        """ Pattern """
        self.filterLYT = QtWidgets.QHBoxLayout()
        filterLBL = QtWidgets.QLabel('Filter: ')
        self.filterLYT.addWidget(filterLBL)
        self.filterLYT.addWidget(self.filterCMB)
        self.filterLYT.addStretch()
        self.filterLYT.addWidget(QtWidgets.QLabel(' Invert: '))
        self.filterLYT.addWidget(self.invertFilterCB)
        
        self.mainLayout.addLayout(self.nodeLYT)
        self.mainLayout.addLayout(self.filterLYT)
        self.mainLayout.addWidget(self.nodeTBL)

    def createConnection(self):
        self.nodeParentBTN.nodeSelected.connect(self.onClick_nodeParentBTN)

    def onClick_nodeParentBTN(self, node):
        # Update the parent node
        if node:
            self.nodeParentTXT.setText(str(node.path()))

            # If loaded update table
            self.nodeList = getAllNodes(parentNode)
            self.paramList = getParamNodes(self.nodeList)

            # Add to table
            for param in self.paramList:
                #param.showInformation()
                rowPosition = self.nodeTBL.rowCount()
                self.nodeTBL.insertRow(rowPosition)
                variables = [param.paramName, param.nodeType, param.paramType, param.paramValue, param.nodePath]

                for i in range(self.nodeTBL.columnCount()):
                    item = QtWidgets.QTableWidgetItem(variables[i]) # type QtWidgets.QTableWidgetItem
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                    self.nodeTBL.setItem(rowPosition , i, item)

            self.nodeTBL.resizeColumnsToContents()


try:
    kt_RenderHelper.close()
    kt_RenderHelper.deleteLater()
except:
    pass

ktRenderHelper = kt_RenderHelper()
ktRenderHelper.show()    
    