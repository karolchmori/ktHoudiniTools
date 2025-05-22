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
        pass


    def createLayout(self):
        pass

    def createConnection(self):
        pass



try:
    kt_RenderHelper.close()
    kt_RenderHelper.deleteLater()
except:
    pass

ktRenderHelper = kt_RenderHelper()
ktRenderHelper.show()    
    