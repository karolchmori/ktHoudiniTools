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

class CameraParameter(object):
    def __init__(self, nodePath, nodeName, nodeAction= None, shutterOpen= None, shutterClose= None):
        self.nodePath = nodePath
        self.nodeName = nodeName
        self.nodeAction = nodeAction
        self.shutterOpen = shutterOpen
        self.shutterClose = shutterClose

    def showInformation(self):
        """ Prints all attributes of the texture object except the `textureMapping` dictionary."""
        print("-----------------------------------------")
        for attribute, value in vars(self).items():  # Iterate over the instance's attributes
            print(f"{attribute}: {value}")
        print("-----------------------------------------")


class LightParameter(object):
    def __init__(self, nodePath, nodeName, nodeType, camera= None, diffuse= None, specular= None, transmission= None, 
                 sss= None, volume= None, indirect= None, aovGroup= None):
        self.nodePath = nodePath
        self.nodeName = nodeName
        self.nodeType = nodeType
        self.camera = camera
        self.diffuse = diffuse
        self.specular = specular
        self.transmission = transmission
        self.sss = sss
        self.volume = volume
        self.indirect = indirect
        self.aovGroup = aovGroup

    def showInformation(self):
        """ Prints all attributes of the texture object except the `textureMapping` dictionary."""
        print("-----------------------------------------")
        for attribute, value in vars(self).items():  # Iterate over the instance's attributes
            print(f"{attribute}: {value}")
        print("-----------------------------------------")

class RenderVarParameter(object):
    def __init__(self, nodePath, nodeName, dataType = None, sourceName= None, sourceType= None, aovFormat= None):
        self.nodePath = nodePath
        self.nodeName = nodeName
        self.dataType = dataType
        self.sourceName = sourceName
        self.sourceType = sourceType
        self.aovFormat = aovFormat

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
        # Widget
        self.expandBTN = QtWidgets.QPushButton("+")
        self.expandBTN.setFixedSize(30, 30)  # Small size

        self.contentWDT = QtWidgets.QWidget()
        
        # Layout
        self.headerLYT = QtWidgets.QHBoxLayout()
        self.headerLYT.addStretch()
        self.headerLYT.addWidget(self.expandBTN)

        self.contentLYT = QtWidgets.QVBoxLayout(self.contentWDT)
        self.contentLYT.setContentsMargins(0, 0, 0, 0)
        self.contentLYT.setSpacing(2)

        self.mainLYT = QtWidgets.QVBoxLayout()
        self.mainLYT.setContentsMargins(5, 5, 5, 5) 
        self.mainLYT.setSpacing(2)    
        self.mainLYT.addLayout(self.headerLYT)
        self.mainLYT.addWidget(self.contentWDT)
        
        self.setLayout(self.mainLYT)

        self.createWidgets()
        self.createLayout()
        self.createConnection()

        # Connections
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
        self.expandedDialog = QtWidgets.QDialog()
        self.expandedDialog.setWindowTitle(self.title())
        self.expandedDialog.setLayout(QtWidgets.QVBoxLayout())
        self.expandedDialog.setMinimumSize(800, 500)
        
        # Create and populate expanded view
        self.createWidgetsExpanded()
        self.createLayoutExpanded()
        self.createConnectionExpanded()

        self.expandedDialog.show()

    def closeExpandedDialog(self):
        if self.expandedDialog is not None:
            self.expandedDialog.close()
            self.expandedDialog = None
    
    def handleDoubleClickToSelectNode(self, tableWidget, columnIndex):
        """
        Common behavior for handling double-clicks on a specific column in the table to jump to the Houdini node.
        """
        def onDoubleClick(index: QtCore.QModelIndex):
            sourceIndex = tableWidget.proxyModel.mapToSource(index)
            if sourceIndex.column() == columnIndex:
                value = sourceIndex.data()
                node = hou.node(value)
                if node:
                    node.setSelected(True, clear_all_selected=True)
                    for pane in hou.ui.paneTabs():
                        if isinstance(pane, hou.NetworkEditor) and pane.pwd() == node.parent():
                            pane.setCurrentNode(node)
                            break

        return onDoubleClick
    
    def getData(self):
        """Override"""
        pass

    def refreshData(self):
        self.getData()

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
        self.filterCMB.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)


        self.invertCB = QtWidgets.QCheckBox("Invert")

    def createLayouts(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        filterLYT = QtWidgets.QHBoxLayout()
        filterLYT.setContentsMargins(0, 0, 0, 0)
        filterLYT.setSpacing(2)
        filterLYT.addWidget(QtWidgets.QLabel("Filter:"))
        filterLYT.addWidget(self.filterCMB, stretch=1)
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
    def __init__(self, nodeList):
        self.nodeList = nodeList
        self.fileNodeParameters = []
        self.counters = []
        super().__init__("File Checker")

    def getData(self):
    
        self.fileNodeParameters = self.getFileParam(self.nodeList)
        self.counters = self.groupData(self.fileNodeParameters)

        for i in range(3):
            item = QtWidgets.QTableWidgetItem(str(self.counters[i])) # type QtWidgets.QTableWidgetItem
            item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.summaryTBL.setItem(0 , i, item)

            
    def groupData(self, parmList):
        hipCount = 0
        jobCount = 0
        othersCount = 0

        for parm in parmList:
            if "$HIP" in parm.fileValue:
                hipCount += 1
            elif "$JOB" in parm.fileValue:
                jobCount += 1
            else:
                othersCount += 1
        
        return [hipCount, jobCount, othersCount]
        
    def createWidgets(self):
        self.summaryTBL = QtWidgets.QTableWidget(1, 3)
        self.summaryTBL.setHorizontalHeaderLabels(["$HIP", "$JOB", "Others"])
        self.summaryTBL.setSortingEnabled(False)
        self.summaryTBL.verticalHeader().setVisible(False)
        self.summaryTBL.resizeColumnsToContents()
        self.summaryTBL.resizeRowsToContents()
        self.summaryTBL.setColumnWidth(0, 40)
        self.summaryTBL.setColumnWidth(1, 40)
        self.summaryTBL.setColumnWidth(2, 80)
        self.summaryTBL.setFixedSize(190,65)
        self.summaryTBL.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.getData()
        

    def createLayout(self):
        self.contentLYT.addWidget(self.summaryTBL, alignment=QtCore.Qt.AlignHCenter)


    def createConnection(self):
        pass 

    def createWidgetsExpanded(self):
        self.fileNodeTBL = FilterableTable(["Node", "Parameter", "Value", "Path"])
        self.fileNodeTBL.filterCMB.addItems(['','$JOB','$HIP'])
        self.fileNodeTBL.table.setColumnWidth(0, 100)
        self.fileNodeTBL.table.setColumnWidth(1, 100)
        self.fileNodeTBL.table.setColumnWidth(2, 270)
        self.fileNodeTBL.table.setColumnWidth(3, 200)

        # Load Data
        self.getData()
        self.loadTable(self.fileNodeParameters)

    def createLayoutExpanded(self):

        """Function that creates all the layouts and add widgets"""
        layout = self.expandedDialog.layout()
        layout.addWidget(self.fileNodeTBL)

    def createConnectionExpanded(self):
        lastColumn = self.fileNodeTBL.model.columnCount()-1
        self.fileNodeTBL.table.doubleClicked.connect(self.handleDoubleClickToSelectNode(self.fileNodeTBL, lastColumn))

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
    def __init__(self, nodeList):
        self.nodeList = nodeList
        self.cameraParameters = []
        self.counters = []

        super().__init__("Camera")
    
    def getData(self):
    
        self.cameraParameters = self.getCamParam(self.nodeList)
        self.counters = self.groupData(self.cameraParameters)

        for i in range(2):
            item = QtWidgets.QTableWidgetItem(str(self.counters[i])) # type QtWidgets.QTableWidgetItem
            item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.summaryTBL.setItem(0 , i, item)
    
    def groupData(self, parmList):
        camCreate = 0
        camEdit = 0

        for parm in parmList:
            if "Create" in parm.nodeAction:
                camCreate += 1
            else:
                camEdit += 1
        
        return [camCreate, camEdit]

    def createWidgets(self):
        self.summaryTBL = QtWidgets.QTableWidget(1, 2)
        self.summaryTBL.setHorizontalHeaderLabels(["Create", "Edit"])
        self.summaryTBL.setSortingEnabled(False)
        self.summaryTBL.verticalHeader().setVisible(False)
        self.summaryTBL.setColumnWidth(0, 60)
        self.summaryTBL.setColumnWidth(1, 60)
        self.summaryTBL.setFixedSize(190,65)
        self.summaryTBL.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)


        self.getData()

    def createLayout(self):
        self.contentLYT.addWidget(self.summaryTBL, alignment=QtCore.Qt.AlignHCenter)

    def createWidgetsExpanded(self):
        self.camNodeTBL = FilterableTable(["Node", "Action", "Shutter Open", "Shutter Close", "Path"])
        self.camNodeTBL.filterCMB.addItems(['','Create','Edit'])
        self.camNodeTBL.table.setColumnWidth(0, 150)
        self.camNodeTBL.table.setColumnWidth(1, 100)
        self.camNodeTBL.table.setColumnWidth(2, 125)
        self.camNodeTBL.table.setColumnWidth(3, 125)
        self.camNodeTBL.table.setColumnWidth(4, 200)

        # Load Data
        self.getData()
        self.loadTable(self.cameraParameters)

    def createLayoutExpanded(self):
        layout = self.expandedDialog.layout()
        layout.addWidget(self.camNodeTBL)

    def createConnectionExpanded(self):
        pass
    
    def loadTable(self, data):
        if data:
            self.camNodeTBL.clearContent()
            items = []

            for param in data:
                variables = [param.nodeName, param.nodeAction, str(param.shutterOpen), str(param.shutterClose), param.nodePath]
                items = []
                for value in variables:
                    item = QtGui.QStandardItem(value)
                    item.setToolTip(value)
                    item.setEditable(False)
                    items.append(item)

                self.camNodeTBL.model.appendRow(items)

    def getCamParam(self, nodeList):
        paramList = []

        for path in nodeList:
            node = hou.node(path)
            if node.type().name() == 'camera':
                parameters = node.parms()
                shutterOpen = ''
                shutterClose = ''
                nodeAction = ''

                for param in parameters:
                    if "createprims" in param.name():
                        nodeAction = param.menuLabels()[param.eval()]

                    if param.name() in ("xn__shutteropen_0ta","xn__shutterclose_nva") and not param.isDisabled():
                        
                        if param.name() == "xn__shutteropen_0ta":
                            shutterOpen = param.eval()
                        if param.name() == "xn__shutterclose_nva":
                            shutterClose = param.eval()

                newParam = CameraParameter(nodePath=path, nodeName= node.name(), shutterOpen=shutterOpen, shutterClose=shutterClose, nodeAction= nodeAction)
                paramList.append(newParam)

        return paramList

class RenderVariablesBLK(ExpandableBlock):
    def __init__(self, nodeList):
        self.nodeList = nodeList
        self.renderVarNodeParameters = []

        super().__init__("Render VAR")
    
    def getData(self):
    
        self.renderVarNodeParameters = self.getVarParam(self.nodeList)

        self.summaryTBL.setRowCount(0)

        for var in self.renderVarNodeParameters:
            rowPosition = self.summaryTBL.rowCount()
            self.summaryTBL.insertRow(rowPosition)

            values = [var.nodeName, var.dataType, var.sourceName, var.sourceType, var.aovFormat]

            for col, val in enumerate(values):

                item = QtWidgets.QTableWidgetItem(val)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.summaryTBL.setItem(rowPosition, col, item)

    def createWidgets(self):
        self.summaryTBL = QtWidgets.QTableWidget()
        self.summaryTBL.setColumnCount(5)
        self.summaryTBL.setHorizontalHeaderLabels(["Node", "Data Type", "Source Name", "Source Type","Format"])
        self.summaryTBL.setSortingEnabled(True)
        self.summaryTBL.verticalHeader().setVisible(False)
        self.summaryTBL.resizeColumnsToContents()
        self.summaryTBL.resizeRowsToContents()
        self.summaryTBL.setColumnWidth(0, 120)
        self.summaryTBL.setColumnWidth(1, 100)
        self.summaryTBL.setColumnWidth(2, 120)
        self.summaryTBL.setColumnWidth(3, 120)
        self.summaryTBL.setColumnWidth(4, 70)
        self.summaryTBL.setMinimumWidth(540)
        self.summaryTBL.setMinimumHeight(250)
        self.summaryTBL.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.getData()

    def createLayout(self):
        self.contentLYT.addWidget(self.summaryTBL, alignment=QtCore.Qt.AlignHCenter)

    def createWidgetsExpanded(self):
        self.renderVarNodeTBL = FilterableTable(["Node", "Data Type", "Source Name", "Source Type","Format","Path"])
        self.renderVarNodeTBL.filterCMB.addItems([''])
        self.renderVarNodeTBL.table.setColumnWidth(0, 100)

        # Load Data
        self.getData()
        self.loadTable(self.renderVarNodeParameters)

    def createLayoutExpanded(self):
        layout = self.expandedDialog.layout()
        layout.addWidget(self.renderVarNodeTBL)

    def createConnectionExpanded(self):
        lastColumn = self.renderVarNodeTBL.model.columnCount()-1
        self.renderVarNodeTBL.table.doubleClicked.connect(self.handleDoubleClickToSelectNode(self.renderVarNodeTBL, lastColumn))

    
    def loadTable(self, data):
        if data:
            self.renderVarNodeTBL.clearContent()
            items = []

            for param in data:

                variables = [param.nodeName, param.dataType, param.sourceName, param.sourceType, param.aovFormat, param.nodePath]
                items = []
                for value in variables:
                    if not value:
                        value = ""
                
                    item = QtGui.QStandardItem(value)
                    item.setToolTip(value)
                    item.setEditable(False)
                    items.append(item)

                self.renderVarNodeTBL.model.appendRow(items)
    
    def getVarParam(self, nodeList):
        paramList = []

        variablesList = ["dataType","sourceName","sourceType","xn__driverparametersaovformat_shbkd"]

        for path in nodeList:
            node = hou.node(path)
            if node.type().name() == "rendervar":
                parameters = node.parms()
                newRenderVar = RenderVarParameter(nodePath=path, nodeName= node.name())

                for param in parameters:
                    #print(param.parmTemplate())
                    paramName = param.name()
                    if paramName in variablesList:

                        if param.parmTemplate().type().name() == "String":
                            paramValue = param.unexpandedString()
                        else:
                            paramValue = param.eval()
                            if not paramValue:
                                paramValue = "0.0"

                        if paramValue:
                            if paramName == variablesList[0]: newRenderVar.dataType = str(paramValue)
                            elif paramName == variablesList[1]: newRenderVar.sourceName = str(paramValue)
                            elif paramName == variablesList[2]: newRenderVar.sourceType = str(paramValue)
                            elif paramName == variablesList[3]: newRenderVar.aovFormat = str(paramValue)
                
                paramList.append(newRenderVar)

        return paramList

class LightInformationBLK(ExpandableBlock):
    def __init__(self, nodeList):
        self.nodeList = nodeList
        self.lightNodeParameters = []
        super().__init__("Lights")
    
    def getData(self):
        self.lightNodeParameters = self.getLightParam(self.nodeList)
        self.summaryTBL.setRowCount(0)

        for light in self.lightNodeParameters:
            rowPosition = self.summaryTBL.rowCount()
            self.summaryTBL.insertRow(rowPosition)

            values = [light.nodeName, light.camera, light.diffuse, light.specular,
            light.transmission, light.sss, light.volume, light.indirect,
            light.aovGroup,]

            for col, val in enumerate(values):

                item = QtWidgets.QTableWidgetItem(val)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.summaryTBL.setItem(rowPosition, col, item)

    def createWidgets(self):

        self.summaryTBL = QtWidgets.QTableWidget()
        self.summaryTBL.setColumnCount(9)
        self.summaryTBL.setHorizontalHeaderLabels(["Node", "C", "D", "S","T","SS","V","I","Group"])
        self.summaryTBL.setSortingEnabled(True)
        self.summaryTBL.verticalHeader().setVisible(False)
        self.summaryTBL.resizeColumnsToContents()
        self.summaryTBL.resizeRowsToContents()
        self.summaryTBL.setColumnWidth(0, 100)
        self.summaryTBL.setColumnWidth(8, 150)
        for i in range(1,7):
            self.summaryTBL.setColumnWidth(i, 50)
        self.summaryTBL.setMinimumWidth(540)
        self.summaryTBL.setMinimumHeight(250)
        self.summaryTBL.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.getData()

    def createLayout(self):
        self.contentLYT.addWidget(self.summaryTBL, alignment=QtCore.Qt.AlignHCenter)

    def createWidgetsExpanded(self):
        self.lightNodeTBL = FilterableTable(["Node","Type","C", "D", "S","T","SS","V","I","Group","Path"])
        self.lightNodeTBL.filterCMB.addItems([''])
        self.lightNodeTBL.table.setColumnWidth(0, 100)
        for i in range(2,9):
            self.lightNodeTBL.table.setColumnWidth(i, 50)

        # Load Data
        self.getData()
        self.loadTable(self.lightNodeParameters)

    def createLayoutExpanded(self):
        layout = self.expandedDialog.layout()
        layout.addWidget(self.lightNodeTBL)

    def createConnectionExpanded(self):
        lastColumn = self.lightNodeTBL.model.columnCount()-1
        self.lightNodeTBL.table.doubleClicked.connect(self.handleDoubleClickToSelectNode(self.lightNodeTBL, lastColumn))

    
    def loadTable(self, data):
        if data:
            self.lightNodeTBL.clearContent()
            items = []

            for param in data:

                variables = [param.nodeName, param.nodeType, param.camera, param.diffuse, param.specular, param.transmission,
                             param.sss, param.volume, param.indirect, param.aovGroup, param.nodePath]
                items = []
                for value in variables:
                    if not value:
                        value = ""
                
                    item = QtGui.QStandardItem(value)
                    item.setToolTip(value)
                    item.setEditable(False)
                    items.append(item)

                self.lightNodeTBL.model.appendRow(items)
    
    def getLightParam(self, nodeList):
        paramList = []
        variablesList = ["xn__primvarsarnoldcamera_p8ag",
                     "xn__primvarsarnolddiffuse_cbbg",
                     "xn__primvarsarnoldspecular_ycbg",
                     "xn__primvarsarnoldtransmission_hjbg",
                     "xn__primvarsarnoldsss_t3ag",
                     "xn__primvarsarnoldvolume_p8ag",
                     "xn__primvarsarnoldindirect_ycbg",
                     "xn__primvarsarnoldaov_t3ag",
                     #"xn__primvarsarnoldmax_bounces_uhbg",
                     ]
        

        for path in nodeList:
            node = hou.node(path)
            if "light" in node.type().name() and node.type().name() not in ("lightmixer","lightfilterlibrary","lightlinker","arnold::light_decay","arnold_light"):
                parameters = node.parms()
                newLight = LightParameter(nodePath=path, nodeName= node.name(), nodeType=node.type().name())

                for param in parameters:
                    paramName = param.name()
                    #print(param.parmTemplate())
                    if paramName in variablesList and not param.isDisabled():
                        
                        if param.parmTemplate().type().name() == "String":
                            paramValue = param.unexpandedString()
                        else:
                            paramValue = param.eval()
                            if not paramValue:
                                paramValue = "0.0"

                          
                        if paramValue:
                            if paramName == variablesList[0]: newLight.camera = str(paramValue)
                            elif paramName == variablesList[1]: newLight.diffuse = str(paramValue)
                            elif paramName == variablesList[2]: newLight.specular = str(paramValue)
                            elif paramName == variablesList[3]: newLight.transmission = str(paramValue)
                            elif paramName == variablesList[4]: newLight.sss = str(paramValue)
                            elif paramName == variablesList[5]: newLight.volume = str(paramValue)
                            elif paramName == variablesList[6]: newLight.indirect = str(paramValue)
                            elif paramName == variablesList[7]: 
                                newLight.aovGroup = paramValue if str(paramValue).strip() not in ("", "0", "1") else ""
                    

                paramList.append(newLight)

        return paramList

class RenderGeometryPrimitivesBLK(ExpandableBlock):
    def __init__(self, nodeList):
        self.nodeList = nodeList
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
    def __init__(self, nodeList):
        self.nodeList = nodeList

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
        self.setMinimumWidth(1400)
        self.setMinimumHeight(750)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        #self.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.Window)

        self.expandableBlocks = []
        self.allNodes = []
        self.getData()
        
        self.createWidgets()
        self.createLayout()
        self.createConnection()

    def getData(self):
        node = hou.node("/stage")
        self.allNodes = getAllNodes(node)
    
    def createWidgets(self):
        self.tempLBL = QtWidgets.QLabel(' ')
        self.refreshBTN = QtWidgets.QPushButton("Refresh")


        self.fileCheckerBLK = FileCheckBLK(self.allNodes)
        self.cameraBLK = CameraCheckBLK(self.allNodes)
        self.renderVarBLK = RenderVariablesBLK(self.allNodes)
        self.lightInfoBLK = LightInformationBLK(self.allNodes)
        self.renderGeoPrimitivesBLK = RenderGeometryPrimitivesBLK(self.allNodes)
        self.renderGeoVisibilityBLK = RenderGeometryVisibilityBLK(self.allNodes)

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
        headerLYT.addStretch()
        headerLYT.addWidget(self.refreshBTN)


        topLYT = QtWidgets.QGridLayout()
        topLYT.setColumnStretch(0, 0)  # A and B column: do NOT stretch
        topLYT.setColumnStretch(1, 1)  # C column: stretch
        topLYT.setColumnStretch(2, 1)  # C column: stretch
        topLYT.setColumnStretch(3, 1)  # D column: stretch
        topLYT.setColumnStretch(4, 1)  # D column: stretch
        topLYT.addWidget(self.fileCheckerBLK,0,0)
        topLYT.addWidget(self.cameraBLK,1,0)
        topLYT.addWidget(self.renderVarBLK,0,1,2,2)
        topLYT.addWidget(self.lightInfoBLK,0,3,2,2)
        
        bottomLYT = QtWidgets.QGridLayout()
        bottomLYT.addWidget(self.renderGeoPrimitivesBLK, 0,0)
        bottomLYT.addWidget(self.renderGeoVisibilityBLK, 0,1)

        mainLayout.addLayout(headerLYT)
        mainLayout.addSpacing(10)
        mainLayout.addLayout(topLYT)
        mainLayout.addLayout(bottomLYT)
        self.setLayout(mainLayout)


    def createConnection(self):
        self.refreshBTN.clicked.connect(self.refreshAllBlocks)
    
    def closeEvent(self, event):
        for block in self.expandableBlocks:
            block.closeExpandedDialog()
        super().closeEvent(event)
    
    def refreshAllBlocks(self):
        self.getData()

        for block in self.expandableBlocks:
            block.nodeList = self.allNodes
            block.refreshData()                

    
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