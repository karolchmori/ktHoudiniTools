import hou
from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

global _ktRenderHelperInstance

#region Objects

class FileParameter(object):
    def __init__(self, nodePath, nodeName, fileLabel, fileValue):
        self.nodePath = nodePath
        self.nodeName = nodeName
        self.fileLabel = fileLabel
        self.fileValue = fileValue

    def showInformation(self):
        """ Prints all attributes of the texture object except the `textureMapping` dictionary."""
        print("-----------------------------------------")
        for attribute, value in vars(self).items():  # Iterate over the instance's attributes
            print(f"{attribute}: {value}")
        print("-----------------------------------------")



class ExpandableBlock(QtWidgets.QGroupBox):
    def __init__(self, title):
        super().__init__(title)

        self.expandedDialog = None
        self.expandBTN = QtWidgets.QPushButton("Expandd")
        self.contentWDT = QtWidgets.QWidget()
        self.contentLYT = QtWidgets.QVBoxLayout(self.contentWDT)

        self.mainLYT = QtWidgets.QVBoxLayout()
        self.mainLYT.addWidget(self.contentWDT)
        self.mainLYT.addWidget(self.expandBTN)
        self.setLayout(self.mainLYT)

        self.createWidgets()
        self.createLayout()
        self.createConnection()

        self.expandBTN.clicked.connect(self.expandView)
        if self.window():
            self.window().destroyed.connect(self.closeExpandedDialog)

    
    def createWidgets(self):
        """Override this in subclasses to add custom widgets."""
        pass

    def createLayout(self):
        """Override this in subclasses to arrange widgets."""
        pass

    def createConnection(self):
        """Override this in subclasses to connect signals and slots."""
        pass

    def createWidgetsExpanded(self):
        """Override this in subclasses to add custom widgets to expanded view."""
        pass

    def createLayoutExpanded(self):
        """Override this in subclasses to arrange widgets to expanded view."""
        pass

    def createConnectionExpanded(self):
        """Override this in subclasses to connect signals and slots to expanded view."""
        pass

    def expandView(self):
        if self.expandedDialog is None:
            self.expandedDialog = QtWidgets.QDialog()
            self.expandedDialog.setWindowTitle(self.title())
            self.expandedDialog.setLayout(QtWidgets.QVBoxLayout())
            self.expandedDialog.resize(800, 600)
            
            # Create and populate expanded view
            self.createWidgetsExpanded()
            self.createLayoutExpanded()
            self.createConnectionExpanded()

        self.expandedDialog.exec_() # TODO: Maybe we have to change it to show

    def closeExpandedDialog(self):
        if self.expandedDialog is not None:
            self.expandedDialog.close()
            self.expandedDialog = None

#endregion

def getAllNodes(node, nodeList = None, level = 0):
    if nodeList is None:
        nodeList = []
    #print(" " * level + node.name())
    nodeList.append(node.path())

    for child in node.children():
        getAllNodes(child, nodeList, level + 1)

    return nodeList


#region Table 
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

class FilterableTable(QtWidgets.QWidget):
    def __init__(self, headers, parent=None):
        super().__init__(parent)

        self.headers = headers

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
    
        
    def createWidgets(self):
        # Models
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(self.headers)

        self.proxyModel = InvertibleFilterProxyModel()
        self.proxyModel.setSourceModel(self.model)
        self.proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxyModel.setFilterKeyColumn(-1)

        # Table
        self.table = QtWidgets.QTableView()
        self.table.setModel(self.proxyModel)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)

        # Filter UI
        self.filterCMB = QtWidgets.QComboBox()
        self.filterCMB.setEditable(True)
        self.filterCMB.setStyleSheet("""QComboBox { padding-right: 20px; }""")

        self.invertCB = QtWidgets.QCheckBox("Invert")

    def createLayouts(self):
        layout = QtWidgets.QVBoxLayout(self)

        filterLYT = QtWidgets.QHBoxLayout()
        filterLYT.addWidget(QtWidgets.QLabel("Filter:"))
        filterLYT.addWidget(self.filterCMB)
        filterLYT.addWidget(self.invertCB)

        layout.addLayout(filterLYT)
        layout.addWidget(self.table)
    
    def createConnections(self):
        self.filterCMB.lineEdit().textChanged.connect(self.proxyModel.setFilterText)
        self.invertCB.stateChanged.connect(lambda _: self.proxyModel.setInvert(self.invertCB.isChecked()))

    def clearContent(self):
        self.model.removeRows(0, self.model.rowCount())

        """
        for row in reversed(range(model.rowCount())):
            model.removeRow(row)
        """

    def addRow(self, values):
        items = [QtGui.QStandardItem(str(value)) for value in values]
        for item in items:
            item.setEditable(False)
        self.model.appendRow(items)

    def setColumnWidths(self, widths):
        for i, width in enumerate(widths):
            self.table.setColumnWidth(i, width)

    def getTable(self):
        return self.table

    def getModel(self):
        return self.model

    def getProxyModel(self):
        return self.proxyModel

#endregion

#region Blocks
class FileCheckBLK(ExpandableBlock):
    def __init__(self):
        super().__init__("File Checker")

        self.fileNodeParameters = []
        self.nodeList = []

    def getData(self):
        node = hou.node("/stage")
        self.nodeList = getAllNodes(node)
        self.fileNodeParameters = self.getFileParam(self.nodeList)
        
    def createWidgets(self):
        self.getData()
        
        self.label = QtWidgets.QLabel("$JOB - $HIP Amount: 0")

    def createLayout(self):
        self.contentLYT.addWidget(self.label)

    def createConnection(self):
        pass 

    def createWidgetsExpanded(self):
        self.fileNodeTBL = FilterableTable(["Node", "Parameter", "Value", "Path"])
        self.fileNodeTBL.filterCMB.addItems(['','$JOB','$HIP'])

        self.expandedLabel = QtWidgets.QLabel("Detailed summary with charts and tables")
        self.refreshBTN = QtWidgets.QPushButton("Refresh Data")

        # Load Data
        self.getData()
        self.loadTable(self.fileNodeParameters)

    def createLayoutExpanded(self):

        """Function that creates all the layouts and add widgets"""
        self.mainLayout = self.expandedDialog.layout()
        self.mainLayout.addWidget(self.fileNodeTBL)

    def createConnectionExpanded(self):
        self.fileNodeTBL.table.doubleClicked.connect(self.onCellDoubleClicked_nodeTBL)

    def loadTable(self, data):
        if data:
            self.fileNodeTBL.clearContent()
            items = []

            for param in data:
                variables = [param.nodeName, param.fileLabel, param.fileValue, param.nodePath]
                items = []
                for value in variables:
                    item = QtGui.QStandardItem(value)
                    item.setToolTip(value)
                    item.setEditable(False)
                    items.append(item)

                self.fileNodeTBL.model.appendRow(items)


    def onCellDoubleClicked_nodeTBL(self, index: QtCore.QModelIndex):
        
        sourceIndex = self.fileNodeTBL.proxyModel.mapToSource(index)
        if sourceIndex.column() == 3:
            value = sourceIndex.data()
            print(f"Double-clicked column 3 value: {value}")
            node = hou.node(value)
            if node:
                # Select the node
                node.setSelected(True, clear_all_selected=True)
                
                # Focus on the node in the network editor pane
                # Find the network editor pane that shows this node's context
                for pane in hou.ui.paneTabs():
                    if isinstance(pane, hou.NetworkEditor) and pane.pwd() == node.parent():
                        pane.setCurrentNode(node)
                        #pane.bringToFront()
                        #pane.show()
                        break
    
    def getFileParam(self, nodeList):
        
        paramList = []

        for path in nodeList:
            node = hou.node(path)

            parameters = node.parms()
            for param in parameters:
                paramName = param.name()
                if paramName not in ("rendergallerysource"):
                    paramType = param.parmTemplate().type()

                    if paramType.name() == 'String':
                        stringType = param.parmTemplate().stringType()
                        
                        if stringType.name() == 'FileReference':
                            paramValue = param.unexpandedString()
                            if paramValue:
                                newParam = FileParameter(nodePath=path, nodeName= node.name(), fileLabel=paramName, fileValue=paramValue)
                                paramList.append(newParam)

        return paramList


class CameraCheckBLK(ExpandableBlock):
    def __init__(self):
        super().__init__("Camera")

    def createWidgets(self):
        self.label = QtWidgets.QLabel("CAMERA Status 1")

    def createLayout(self):
        self.contentLYT.addWidget(self.label)

    def createWidgetsExpanded(self):
        self.expandedLabel = QtWidgets.QLabel("Detailed opportunity pipeline")
        self.refreshBTN = QtWidgets.QPushButton("Refresh Opportunities")

    def createLayoutExpanded(self):
        layout = self.expandedDialog.layout()
        layout.addWidget(self.expandedLabel)
        layout.addWidget(self.refreshBTN)

    def createConnectionExpanded(self):
        self.refreshBTN.clicked.connect(lambda: self.expandedLabel.setText("Opportunities updated!"))


class RenderVariablesBLK(ExpandableBlock):
    def __init__(self):
        super().__init__("Render VAR")

    def createWidgets(self):
        self.label = QtWidgets.QLabel("Table INSERT")

    def createLayout(self):
        self.contentLYT.addWidget(self.label)

    def createWidgetsExpanded(self):
        self.expandedLabel = QtWidgets.QLabel("Lead details and conversion funnel")
        self.refreshBTN = QtWidgets.QPushButton("Update Leads")

    def createLayoutExpanded(self):
        layout = self.expandedDialog.layout()
        layout.addWidget(self.expandedLabel)
        layout.addWidget(self.refreshBTN)

    def createConnectionExpanded(self):
        self.refreshBTN.clicked.connect(lambda: self.expandedLabel.setText("Leads refreshed!"))

class LightInformationBLK(ExpandableBlock):
    def __init__(self):
        super().__init__("Lights")

    def createWidgets(self):
        self.label = QtWidgets.QLabel("Light Contribution HERE")

    def createLayout(self):
        self.contentLYT.addWidget(self.label)

    def createWidgetsExpanded(self):
        self.expandedLabel = QtWidgets.QLabel("Lead details and conversion funnel")
        self.refreshBTN = QtWidgets.QPushButton("Update Leads")

    def createLayoutExpanded(self):
        layout = self.expandedDialog.layout()
        layout.addWidget(self.expandedLabel)
        layout.addWidget(self.refreshBTN)

    def createConnectionExpanded(self):
        self.refreshBTN.clicked.connect(lambda: self.expandedLabel.setText("Leads refreshed!"))

class RenderGeometryPrimitivesBLK(ExpandableBlock):
    def __init__(self):
        super().__init__("Render Geometry (Primitives)")

    def createWidgets(self):
        self.label = QtWidgets.QLabel("Render Primitives HERE")

    def createLayout(self):
        self.contentLYT.addWidget(self.label)

    def createWidgetsExpanded(self):
        self.expandedLabel = QtWidgets.QLabel("Lead details and conversion funnel")
        self.refreshBTN = QtWidgets.QPushButton("Update Leads")

    def createLayoutExpanded(self):
        layout = self.expandedDialog.layout()
        layout.addWidget(self.expandedLabel)
        layout.addWidget(self.refreshBTN)

    def createConnectionExpanded(self):
        self.refreshBTN.clicked.connect(lambda: self.expandedLabel.setText("Leads refreshed!"))


class RenderGeometryVisibilityBLK(ExpandableBlock):
    def __init__(self):
        super().__init__("Render Geometry (Visibility)")

    def createWidgets(self):
        self.label = QtWidgets.QLabel("Render Visibility HERE")

    def createLayout(self):
        self.contentLYT.addWidget(self.label)

    def createWidgetsExpanded(self):
        self.expandedLabel = QtWidgets.QLabel("Lead details and conversion funnel")
        self.refreshBTN = QtWidgets.QPushButton("Update Leads")

    def createLayoutExpanded(self):
        layout = self.expandedDialog.layout()
        layout.addWidget(self.expandedLabel)
        layout.addWidget(self.refreshBTN)

    def createConnectionExpanded(self):
        self.refreshBTN.clicked.connect(lambda: self.expandedLabel.setText("Leads refreshed!"))

#endregion

#region Main

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
        self.setMinimumWidth(1050)
        self.setMinimumHeight(650)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.expandableBlocks = []


        self.createWidgets()
        self.createLayout()
        self.createConnection()
    
    
    def createWidgets(self):
        self.tempLBL = QtWidgets.QLabel('TEMP')
        self.refreshBTN = QtWidgets.QPushButton("Refresh")


        self.fileCheckerBLK = FileCheckBLK()
        self.cameraBLK = CameraCheckBLK()
        self.renderVarBLK = RenderVariablesBLK()
        self.lightInfoBLK = LightInformationBLK()
        self.renderGeoPrimitivesBLK = RenderGeometryPrimitivesBLK()
        self.renderGeoVisibilityBLK = RenderGeometryVisibilityBLK()

        self.expandableBlocks.append(self.fileCheckerBLK)
        self.expandableBlocks.append(self.cameraBLK)
        self.expandableBlocks.append(self.renderVarBLK)
        self.expandableBlocks.append(self.lightInfoBLK)
        self.expandableBlocks.append(self.renderGeoPrimitivesBLK)
        self.expandableBlocks.append(self.renderGeoVisibilityBLK)

    def createLayout(self):
        mainLayout = QtWidgets.QVBoxLayout(self)
        headerLYT = QtWidgets.QHBoxLayout()
        headerLYT.addWidget(self.tempLBL)
        headerLYT.addWidget(self.refreshBTN)


        topLYT = QtWidgets.QGridLayout()
        topLYT.addWidget(self.fileCheckerBLK,0,0)
        topLYT.addWidget(self.cameraBLK,1,0)
        topLYT.addWidget(self.renderVarBLK,0,1,2,1)
        topLYT.addWidget(self.lightInfoBLK,0,2,2,1)
        
        bottomLYT = QtWidgets.QGridLayout()
        bottomLYT.addWidget(self.renderGeoPrimitivesBLK, 0,0)
        bottomLYT.addWidget(self.renderGeoVisibilityBLK, 0,1)

        mainLayout.addLayout(headerLYT)
        mainLayout.addSpacing(10)
        mainLayout.addLayout(topLYT)
        mainLayout.addLayout(bottomLYT)
        self.setLayout(mainLayout)


    def createConnection(self):
        pass
    
    def closeEvent(self, event):
        for block in self.expandableBlocks:
            block.closeExpandedDialog()
        super().closeEvent(event)

    
#endregion

try:
    kt_RenderHelper.close()
    kt_RenderHelper.deleteLater()
except:
    pass

ktRenderHelper = kt_RenderHelper()
ktRenderHelper.show()   



"""
try:
    if _ktRenderHelperInstance is not None: # type: ignore
        if _ktRenderHelperInstance.isVisible(): # type: ignore
            _ktRenderHelperInstance.raise_() # type: ignore
            _ktRenderHelperInstance.activateWindow() # type: ignore
        else:
            _ktRenderHelperInstance.show() # type: ignore
except NameError:
    _ktRenderHelperInstance = kt_RenderHelper()
    _ktRenderHelperInstance.show()
"""