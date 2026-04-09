import hou
import os
import re
import voptoolutils

try:
    from PySide6 import QtCore, QtWidgets, QtGui
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui

def getAllNodes(node, nodeList = None, level = 0):
    if nodeList is None:
        nodeList = []
    #print(" " * level + node.name())
    nodeList.append(node.path())

    for child in node.children():
        getAllNodes(child, nodeList, level + 1)

    return nodeList

def exportComponentUSD(kwargs):
    '''
    node = hou.node('/stage/Dead_Common_Bush_01')
    node.parm("execute").pressButton()
    '''

    nodeRoot = hou.node('/stage')
    nodeList = getAllNodes(nodeRoot)

    
    # 'componentoutput'
    for node in nodeList:
        tempNode = hou.node(node)
        nodeType = tempNode.type().name()
        if nodeType == 'componentoutput':
            tempNode.parm("execute").pressButton()
            #print(tempNode)


def createComponentGeometry(kwargs):
    hda = kwargs['node']
    root = hda.node('/stage')

    nodeComp = root.createNode('componentgeometry')
    nodeAbc = nodeComp.createNode('alembic')



#region Main


def getHoudiniMainWindow():
    """
    Retrieves the main Houdini window.

    Returns:
        QWidget: The main Houdini Qt window.
    """
    return hou.qt.mainWindow()

class ktVeggieImporter(QtWidgets.QDialog):
    def __init__(self, parent=getHoudiniMainWindow()):
        """
        Initializes the ktTextureImporter dialog.

        This constructor sets up the dialog window, initializes UI elements, 
        and establishes connections between widgets and their event handlers.

        Args:
            parent (QWidget, optional): The parent widget, defaulting to the Houdini main window.
        """
        super(ktVeggieImporter, self).__init__(parent)
        
        self.setWindowTitle('kt_VeggieImporter')
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        
        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def keyPressEvent(self, event):
        """
        Overrides the key press event to prevent triggering actions on Enter key press.

        Args:
            event (QKeyEvent): The key event triggered by user input.
        """
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            event.accept()  # Prevents default behavior
            
    def createWidgets(self):
        """Function that creates all the widgets"""
        # --------------------------------------------
        self.matPathTXT = QtWidgets.QLineEdit()
        self.matPathTXT.setReadOnly(True)
        self.matPathBTN = hou.qt.NodeChooserButton()

        self.objPathTXT = QtWidgets.QLineEdit()
        self.objPathTXT.setReadOnly(True)
        self.objPathBTN = hou.qt.FileChooserButton()
        self.objPathBTN.setFileChooserTitle("Please select a directory")
        self.objPathBTN.setFileChooserMode(hou.fileChooserMode.Read)
        self.objPathBTN.setFileChooserFilter(hou.fileType.Directory)


        self.texPathTXT = QtWidgets.QLineEdit()
        self.texPathTXT.setReadOnly(True)
        self.texPathBTN = hou.qt.FileChooserButton()
        self.texPathBTN.setFileChooserTitle("Please select a directory")
        self.texPathBTN.setFileChooserMode(hou.fileChooserMode.Read)
        self.texPathBTN.setFileChooserFilter(hou.fileType.Directory)


        self.selectAllCB = QtWidgets.QCheckBox()
        self.createBTN = QtWidgets.QPushButton("Create")
        self.createBTN.setEnabled(False)
        self.clearBTN = QtWidgets.QPushButton("Clear")
        self.clearBTN.setFixedWidth(60)
        self.clearBTN.setFixedHeight(34)
        self.clearBTN.setStyleSheet("padding: 0px;")
            
    def createLayouts(self):
        """Function that creates all the layouts and add widgets"""
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        """ Header """
        self.textureTypeLYT = QtWidgets.QHBoxLayout()
        self.textureTypeLYT.addWidget(QtWidgets.QLabel(' Material Library: '))
        self.textureTypeLYT.addWidget(self.matPathTXT)
        self.textureTypeLYT.addWidget(self.matPathBTN)
        

        """ Objects Path """
        self.objPathLYT = QtWidgets.QHBoxLayout()
        self.objPathLYT.addWidget(QtWidgets.QLabel('Object Path: '))
        self.objPathLYT.addWidget(self.objPathTXT)
        self.objPathLYT.addWidget(self.objPathBTN)

        """ Texture Path """
        self.texPathLYT = QtWidgets.QHBoxLayout()
        self.texPathLYT.addWidget(QtWidgets.QLabel('Texture Path: '))
        self.texPathLYT.addWidget(self.texPathTXT)
        self.texPathLYT.addWidget(self.texPathBTN)

        """ Execution"""
        self.execLYT = QtWidgets.QHBoxLayout()
        self.execLYT.addWidget(self.selectAllCB)
        self.execLYT.addWidget(QtWidgets.QLabel('Select All'))
        self.execLYT.addStretch()
        self.execLYT.addWidget(self.createBTN)
        self.execLYT.addWidget(self.clearBTN)


        """ OBJECT CONTAINER """
        self.objScroll = QtWidgets.QScrollArea()             # Scroll Area which contains the widgets, set as the centralWidget
        self.objContainer = QtWidgets.QWidget()                 # Widget that contains the collection of Vertical Box
        self.objLYT = QtWidgets.QVBoxLayout()               # The Vertical Box that contains the Horizontal Boxes of  labels and buttons
        self.objLYT.setContentsMargins(0, 0, 0, 0)
        self.objLYT.setSpacing(0)

        self.objContainer.setLayout(self.objLYT)



        """ TEXTURES CONTAINER """
        self.texScroll = QtWidgets.QScrollArea()             # Scroll Area which contains the widgets, set as the centralWidget
        self.texContainer = QtWidgets.QWidget()                 # Widget that contains the collection of Vertical Box
        self.texLYT = QtWidgets.QVBoxLayout()               # The Vertical Box that contains the Horizontal Boxes of  labels and buttons
        self.texLYT.setContentsMargins(0, 0, 0, 0)
        self.texLYT.setSpacing(0)

        self.texContainer.setLayout(self.texLYT)

        #Scroll Area Properties
        self.texScroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.texScroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.texScroll.setWidgetResizable(True)
        self.texScroll.setWidget(self.texContainer)

        """ MAIN """
        self.mainLayout.addLayout(self.textureTypeLYT)
        self.mainLayout.addLayout(self.objPathLYT)
        self.mainLayout.addLayout(self.texPathLYT)
        self.mainLayout.addSpacing(25)
        self.mainLayout.addLayout(self.execLYT)
        self.mainLayout.addWidget(QtWidgets.QLabel('Objects'))
        self.mainLayout.addWidget(self.objScroll)
        self.mainLayout.addWidget(QtWidgets.QLabel('Textures'))
        self.mainLayout.addWidget(self.texScroll)

    def createConnections(self):
        pass
    



#endregion


try:
    ktVeggieImporter.close()
    ktVeggieImporter.deleteLater()
except:
    pass

ktVeggieImporter = ktVeggieImporter()
ktVeggieImporter.show()