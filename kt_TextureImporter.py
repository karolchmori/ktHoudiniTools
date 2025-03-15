import hou
import os
import re
from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

#region Texture
class Texture(object):

    """docstring for ClassName."""
    def __init__(self, name, baseColor=None, metalness=None, specularRough=None, normal=None, displacement=None):
        self.name = name
        self.baseColor = baseColor
        self.metalness = metalness
        self.specularRough = specularRough
        self.normal = normal
        self.displacement = displacement

        self.textureMapping = {
            "baseColor": {"label": "Base Color", "abbreviation": "BC", "mapping": ["basecolor", "base"]},
            "metalness": {"label": "Metalness", "abbreviation": "M", "mapping": ["metalness", "metallic"]},
            "specularRough": {"label": "Specular Rough", "abbreviation": "SR", "mapping": ["roughness", "specular"]},
            "normal": {"label": "Normal", "abbreviation": "N", "mapping": ["normal"]},
            "displacement": {"label": "Displacement", "abbreviation": "D", "mapping": ["height", "displacement"]},
        }
    
    def createTexture(self): #We need it here so we can create textures depending on the type (it doesn't depend on the widget or window)
        pass

    def getTypeFromAttr(self, attr, text):
        for parent, children in self.textureMapping.items():
            if text in children[attr]:
                return parent
        return None

    def showInformation(self):
        print("-----------------------------------------")
        for attribute, value in vars(self).items():  # Iterate over the instance's attributes
            if attribute != "textureMapping":  # Exclude textureMapping from being printed
                print(f"{attribute}: {value}")
        print("-----------------------------------------")

class ArnoldTexture(Texture):
    """docstring for ClassName."""
    def __init__(self, name="ArnoldTexture", baseColor=None, metalness=None, specularRough=None, normal=None, displacement=None):
        super().__init__(name=name, baseColor=baseColor, metalness=metalness, specularRough=specularRough, normal=normal, displacement=displacement)
    
    def createTexture(self, parentNode, path):
        # Create the Arnold Material Builder node
        materialBuilderNode = parentNode.createNode("arnold_materialbuilder", self.name)
        outMaterialNode = materialBuilderNode.node("OUT_material")
        standardSurfaceNode = materialBuilderNode.createNode("arnold::standard_surface", f"{self.name}_SDR")
        
        outMaterialNode.setNamedInput("surface", standardSurfaceNode, "shader")
        
        def getFullPath(textureName, path):
            return os.path.join(path, textureName) if textureName else None
        
        # Add the various texture nodes and connect them to the material
        if self.baseColor:
            baseColorNode = materialBuilderNode.createNode("arnold::image", f"{self.name}_BC")
            baseColorNode.parm("filename").set(getFullPath(self.baseColor, path))

            colorCorrectNode = materialBuilderNode.createNode("arnold::color_correct", f"{self.name}_CC") 
            colorCorrectNode.setNamedInput("input", baseColorNode, "rgba")
            standardSurfaceNode.setNamedInput("base_color", colorCorrectNode, "rgba")
 
        if self.metalness:
            metalnessNode = materialBuilderNode.createNode("arnold::image", f"{self.name}_M")
            metalnessNode.parm("filename").set(getFullPath(self.metalness, path))
            standardSurfaceNode.setNamedInput("metalness", metalnessNode, "r")

        if self.specularRough:
            specularRoughNode = materialBuilderNode.createNode("arnold::image", f"{self.name}_SR")
            specularRoughNode.parm("filename").set(getFullPath(self.specularRough, path))
            standardSurfaceNode.setNamedInput("specular_roughness", specularRoughNode, "r")

        if self.normal:
            normalNode = materialBuilderNode.createNode("arnold::image", f"{self.name}_N")
            normalNode.parm("filename").set(getFullPath(self.normal, path))

            normalMapNode = materialBuilderNode.createNode("arnold::normal_map", f"{self.name}_NM") 
            normalMapNode.setNamedInput("input", normalNode, "rgba")
            standardSurfaceNode.setNamedInput("normal", normalMapNode, "vector")

        if self.displacement:
            displacementNode = materialBuilderNode.createNode("arnold::image", f"{self.name}_D")
            displacementNode.parm("filename").set(getFullPath(self.displacement, path))

            rangeNode = materialBuilderNode.createNode("arnold::range", f"{self.name}_RNG") 
            rangeNode.setNamedInput("input", displacementNode, "r")
            outMaterialNode.setNamedInput("displacement", rangeNode, "r")

        # Organize layout
        materialBuilderNode.layoutChildren()

        return materialBuilderNode

class KarmaTexture(Texture):
    """docstring for ClassName."""
    def __init__(self, name="KarmaTexture", baseColor=None, metalness=None, specularRough=None, normal=None, displacement=None, ambientOcclusion=None):
        super().__init__(name=name, baseColor=baseColor, metalness=metalness, specularRough=specularRough, normal=normal, displacement=displacement)
        self.ambientOcclusion = ambientOcclusion
        self.textureMapping["ambientOcclusion"] =  {"label": "Ambient Occlusion", "abbreviation": "AO", "mapping": ["ao","ambientocclusion"]}

#endregion

#region Widget
class ktTextureRowWidget(QtWidgets.QWidget):
    def __init__(self, label, fileType=hou.fileType.Image, mainPath=None):
        super().__init__()

        self.label = label
        self.fileType = fileType
        self.mainPath = mainPath
        self.initUI()

    def initUI(self):
        """Set up the layout, label, text field, and button."""
        layout = QtWidgets.QHBoxLayout(self)

        lbl = QtWidgets.QLabel(self.label)
        self.txt = QtWidgets.QLineEdit()
        self.btn = hou.qt.FileChooserButton()
        self.btn.setFileChooserTitle(f"Please select a {self.label} file")
        self.btn.setFileChooserMode(hou.fileChooserMode.Read)
        self.btn.setFileChooserFilter(self.fileType)

        if self.mainPath:
            self.btn.setFileChooserStartDirectory(self.mainPath)

        # Connect the button's signal to update the text field
        #self.btn.fileSelected.connect(lambda path: self.txt.setText(path))
        self.btn.fileSelected.connect(self.onFileSelected_btn)

        # Add widgets to the layout
        layout.addWidget(lbl)
        layout.addWidget(self.txt)
        layout.addWidget(self.btn)

        layout.setSpacing(5)  # Remove internal spacing
        layout.setContentsMargins(5, 0, 5, 0)  # Remove margins around the layout

        self.setLayout(layout)

    def onFileSelected_btn(self, path):
        """Update the text field when a file is selected."""
        relativePath = os.path.relpath(path, self.mainPath)
        relativePath = relativePath.replace("\\", "/")
        self.txt.setText(relativePath)

    
class ktTextureWidget(QtWidgets.QWidget):
    def __init__(self, texture=None, mainPath=None):
        super().__init__()
        
        self.visibility = False
        self.texture = texture
        self.mainPath = mainPath
        
        """
        UI Creation
        """
        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.loadInformation()


    def _createSummaryRow(self,label):
        """Creates a row with a QLabel and QCheckBox."""
        layout = QtWidgets.QVBoxLayout()
        lbl = QtWidgets.QLabel(label)
        lbl.setFixedHeight(15)
        lbl.setStyleSheet("font-size: 14px;")
        cb = QtWidgets.QCheckBox()
        cb.setEnabled(False)
        layout.addWidget(lbl)
        layout.addWidget(cb)

        layout.setSpacing(1) 
        layout.setContentsMargins(0, 0, 0, 0)
        return layout, cb

    def createWidgets(self):
        """Description widgets"""
        self.selectedCB = QtWidgets.QCheckBox()
        self.nameTXT = QtWidgets.QLineEdit()

        # Storage for checkbox layouts
        self.summaryLayouts = []
        self.textureRows = []

        for attr, details in self.texture.textureMapping.items():
            if hasattr(self.texture, attr):  # Only create if the attribute exists
                sumLayout, checkbox = self._createSummaryRow(details["abbreviation"])
                self.summaryLayouts.append((sumLayout, checkbox))
                
                rowWidget = ktTextureRowWidget(label=details["label"], mainPath=self.mainPath)
                self.textureRows.append(rowWidget)

        self.visibilityBTN = QtWidgets.QPushButton() 
        #https://houdini-icons.dev/
        self.iconCollapsed = hou.qt.Icon("KEYS_Right")   # Left arrow when collapsed hicon:/SVGIcons.index?KEYS_Right.svg
        self.iconExpanded =  hou.qt.Icon("KEYS_Down")    # Down arrow when expanded hicon:/SVGIcons.index?KEYS_Down.svg
        self.visibilityBTN.setIcon(self.iconCollapsed)  # Default icon
        self.visibilityBTN.setFlat(True)
        self.visibilityBTN.setFixedWidth(30)

        # Set the button's style using setStyleSheet
        self.visibilityBTN.setStyleSheet("""
            QPushButton:flat {color: white; font-size: 16px; border: 0px solid black; border-radius: 0px; padding: 10px 20px;
            }
        """)

    def createLayouts(self):
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.headerLYT = QtWidgets.QHBoxLayout(self)
        self.headerLYT.setContentsMargins(0, 0, 0, 0)
        self.headerGB = QtWidgets.QGroupBox("")
        self.headerGB.setLayout(self.headerLYT)
        self.headerGB.setFixedHeight(60)
        self.headerGB.setStyleSheet("""
            QGroupBox {background-color: #4D4D4D; border: 0px solid #4D4D4D; border-radius: 0px; }
            QGroupBox::title { color: white; }
        """)

        # Add Checkboxes
        self.headerLYT.addWidget(self.selectedCB)
        self.headerLYT.addWidget(self.nameTXT)

        # Dynamically add summary rows to the header layout
        for layout, checkbox in self.summaryLayouts:
            self.headerLYT.addLayout(layout)
                
        
        self.headerLYT.addWidget(self.visibilityBTN) 

        """Information Layout"""
        self.informationLYT = QtWidgets.QVBoxLayout(self) 
        self.informationLYT.setContentsMargins(0, 5, 0, 5)  # Remove all margins (left, top, right, bottom)

        self.informationGB = QtWidgets.QGroupBox("")
        self.informationGB.setLayout(self.informationLYT)
        self.informationGB.setVisible(self.visibility)
        self.informationGB.setStyleSheet("""
            QGroupBox { background-color: #363636; border: 0px solid #363636; border-radius: 0px; padding: 0; margin: 0; }
            QGroupBox::title { color: white; }
        """)
        
        # Add texture input widgets dynamically
        for row in self.textureRows:
            if row:
                self.informationLYT.addWidget(row)


        #self.mainLayout.addLayout(self.headerLYT)
        self.mainLayout.addWidget(self.headerGB)
        self.mainLayout.addWidget(self.informationGB)

    def createConnections(self):
        """Connect signals to slots for automatic checkbox updating."""
        self.nameTXT.textChanged.connect(lambda text: self.updateInformation('name', text, None))

        # Dynamically connect each texture row's textChanged signal
        for row, (sumLayout, checkbox) in zip(self.textureRows, self.summaryLayouts):
            row.txt.textChanged.connect(lambda text, row=row, checkbox=checkbox: self.updateInformation(row.label, text, checkbox))

        # Connect visibility button to toggle texture row visibility
        self.visibilityBTN.clicked.connect(self.toggleVisibility)

    def toggleVisibility(self):
        """Toggle the visibility of the texture rows using the visibility flag."""
        # Toggle visibility flag
        self.visibility = not self.visibility
        self.informationGB.setVisible(self.visibility)
        self.visibilityBTN.setIcon(self.iconExpanded if self.visibility else self.iconCollapsed)

    def updateInformation(self, textureProperty, text, checkbox):
        """Update the texture property and checkbox status."""
        textureType = self.texture.getTypeFromAttr("label", textureProperty)
        
        setattr(self.texture, str(textureType), text.strip())  # Update the corresponding texture property

        if checkbox:
            checkbox.setChecked(bool(text.strip()))  # Set the checkbox status


    def loadInformation(self):
        #texture = Texture() # type: Texture
        self.nameTXT.setText(self.texture.name)
        # Dynamically load information for each texture row
        for row, (attr, details) in zip(self.textureRows, self.texture.textureMapping.items()):
            # Check if the attribute exists in the texture and load its value
            value = getattr(self.texture, attr, "")
            #print(f"type: {attr} value: {value}")
            row.txt.setText(value)
        
        

#endregion
            
#region Main



def getHoudiniMainWindow():
    return hou.qt.mainWindow()

class ktTextureImporter(QtWidgets.QDialog):
    def __init__(self, parent=getHoudiniMainWindow()):
        super(ktTextureImporter, self).__init__(parent)
        
        self.setWindowTitle('kt_TextureImporter')
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        
        self.createWidgets()
        self.createLayouts()
        self.createConnections()

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            event.accept()  # Prevents default behavior
        '''else:
            super(ktTextureImporter, self).keyPressEvent(event) '''
            
    def createWidgets(self):
        """Function that creates all the widgets"""
        # --------------------------------------------
        self.textureTypeCMB = QtWidgets.QComboBox()
        self.textureTypeCMB.addItem('Arnold')
        self.textureTypeCMB.addItem('Karma')
        self.textureTypeCMB.setFixedWidth(120)

        self.matPathTXT = QtWidgets.QLineEdit()
        self.matPathTXT.setReadOnly(True)
        self.matPathBTN = hou.qt.NodeChooserButton()

        self.patternCMB = QtWidgets.QComboBox()
        self.patternCMB.addItem('@objName_@texName_*_@texType_*.@id.ext')
        self.patternCMB.addItem('*_*_*_@objName_*_*_@texName_@texType.ext')
        self.patternCMB.addItem('@texName_*_@texType_*.@id.ext')
        self.patternCMB.setEditable(True)
        self.patternCMB.lineEdit().installEventFilter(self)
        self.patternCMB.setStyleSheet("""
            QComboBox { padding-right: 20px; }
        """)

        self.folderPathTXT = QtWidgets.QLineEdit()
        self.folderPathTXT.setReadOnly(True)
        self.folderPathBTN = hou.qt.FileChooserButton()
        self.folderPathBTN.setFileChooserTitle("Please select a directory")
        self.folderPathBTN.setFileChooserMode(hou.fileChooserMode.Read)
        self.folderPathBTN.setFileChooserFilter(hou.fileType.Directory)


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
        self.textureTypeLYT.addWidget(QtWidgets.QLabel('Texture: '))
        self.textureTypeLYT.addWidget(self.textureTypeCMB)
        self.textureTypeLYT.addWidget(QtWidgets.QLabel(' Material Library: '))
        self.textureTypeLYT.addWidget(self.matPathTXT)
        self.textureTypeLYT.addWidget(self.matPathBTN)

        """ Pattern """
        self.patternLYT = QtWidgets.QHBoxLayout()
        patternLBL = QtWidgets.QLabel('Pattern: ')
        patternLBL.setFixedWidth(60)
        self.patternLYT.addWidget(patternLBL)
        self.patternLYT.addWidget(self.patternCMB)
        

        """ Folder """
        self.folderPathLYT = QtWidgets.QHBoxLayout()
        self.folderPathLYT.addWidget(QtWidgets.QLabel('Folder: '))
        self.folderPathLYT.addWidget(self.folderPathTXT)
        self.folderPathLYT.addWidget(self.folderPathBTN)

        """ Execution"""
        self.execLYT = QtWidgets.QHBoxLayout()
        self.execLYT.addWidget(self.selectAllCB)
        self.execLYT.addWidget(QtWidgets.QLabel('Select All'))
        self.execLYT.addStretch()
        self.execLYT.addWidget(self.createBTN)
        self.execLYT.addWidget(self.clearBTN)


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
        self.mainLayout.addLayout(self.patternLYT)
        self.mainLayout.addLayout(self.folderPathLYT)
        self.mainLayout.addSpacing(25)
        self.mainLayout.addLayout(self.execLYT)
        self.mainLayout.addWidget(self.texScroll)

    def createConnections(self):
        self.folderPathBTN.fileSelected.connect(self.onClick_folderPathBTN)
        self.matPathBTN.nodeSelected.connect(self.onClick_matPathBTN)
        self.clearBTN.clicked.connect(self.onClick_clearBTN)
        self.selectAllCB.clicked.connect(self.onChange_selectAllCB)
        self.createBTN.clicked.connect(self.onClick_createBTN)
        self.textureTypeCMB.currentIndexChanged.connect(self.onChange_textureTypeCMB)
        self.patternCMB.lineEdit().textChanged.connect(self.onChange_Finished_patternCMB)
    
    def showMessageError(self, message):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText("Error: " + message)
        msg.setWindowTitle("Houdini Error")
        msg.exec_()

    def onClick_clearBTN(self):
        self.clearLayout(self.texLYT)
        self.folderPathTXT.setText("")
        self.matPathTXT.setText("")
        self.createBTN.setEnabled(False)
    
    def onClick_folderPathBTN(self, filePath):
        if filePath:
            self.folderPathTXT.setText(filePath)
            self.loadTextures()
    
    def onClick_matPathBTN(self, node):
        if node:
            typeNode = node.type().name()
            if typeNode == "materiallibrary":
                self.matPathTXT.setText(str(node.path()))
            else:
              self.showMessageError("The node selected is not a Material Library, please check")
    
    def onClick_createBTN(self):
        parentNode = hou.node(self.matPathTXT.text())
        
        if parentNode:
            folderPath = self.folderPathTXT.text()
            for tex in self.texList:
                #tex = ktTextureWidget() # type: ktTextureWidget
                if tex.selectedCB.isChecked():
                    tex.texture.createTexture(parentNode,folderPath)

            parentNode.layoutChildren()
        else:
            self.showMessageError("A material Library needs to be selected")
    
    def onChange_selectAllCB(self):
        if self.selectAllCB.isChecked:
            self.checkAllTextures()
    
    def onChange_textureTypeCMB(self):
            if self.folderPathTXT.text():
                self.loadTextures()
    
    def onChange_Finished_patternCMB(self):
        if self.folderPathTXT.text():
            self.loadTextures()
            

    def loadTextures(self):
        self.clearLayout(self.texLYT)
        self.texList = []

        folderPath = self.folderPathTXT.text()
        filePattern = self.patternCMB.currentText()
        regexPattern = self.getRegexPattern(filePattern)
        textureType = self.textureTypeCMB.currentText() + "Texture"
        textureClass = globals().get(textureType)

        textures = self.readTexturesFromFolder(folderPath, regexPattern, textureClass)

        if textures:
            self.createBTN.setEnabled(True)
            # Display texture information
            for texture in textures.values():
                #texture = Texture() # type: Texture
                texture.showInformation()
                attributes = {key: value for key, value in vars(texture).items() if key != "textureMapping"}
                newTexture = textureClass(**attributes)

                textureWD = ktTextureWidget(texture=newTexture, mainPath=folderPath)
                self.texLYT.addWidget(textureWD)
                self.texList.append(textureWD)

            self.texLYT.addStretch()
        else:
            self.createBTN.setEnabled(False)
            # Show a message on the screen saying there's no results
            lbl = QtWidgets.QLabel("No results. Verify Pattern")
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet("background-color: #995D58; color: white; padding: 10px; font-weight: bold;")
            self.texLYT.addWidget(lbl)

    def readTexturesFromFolder(self, folderPath, regexPattern, textureClass=Texture):
        textures = {}
        print(f"BEFORE readTexturesFromFolder = {folderPath}")
        folderPath = self.verifyFolderPath(folderPath)
        print(f"AFTER readTexturesFromFolder = {folderPath}")

        # Loop through files in the directory
        for filename in os.listdir(folderPath):
            
            if filename.endswith((".exr", ".png")):  # Filter by file type
                match = re.match(regexPattern, filename)
                if match:
                    objName = match.group("objName") if "objName" in match.groupdict() else None
                    texName = match.group("texName")
                    textureType = match.group("texType")
                    textureId = match.group("id") if "id" in match.groupdict() else None

                    if objName:
                        finalName = objName + "_" + texName
                    else:
                        finalName = texName

                    # Create texture object if not exists
                    if finalName not in textures:
                        textures[finalName] = textureClass(name=finalName) 
                        print(f"Created {textures[finalName].__class__.__name__} object: {finalName}")  # Debugging output
                
                    # Replace @id with $F in the filename if @id is present
                    #if textureId:
                        #filename = filename.replace(textureId, "$F")

                    textureType = textureType.lower()
                    textureParent = textures[finalName].getTypeFromAttr("mapping", textureType)

                    # Check if the textureType exists in the mapping dictionary
                    if textureParent:
                        setattr(textures[finalName], textureParent, filename)
        
        return textures

    def checkAllTextures(self):
        for textureWD in self.texList:
            textureWD.selectedCB.setChecked(self.selectAllCB.isChecked())

    def clearLayout(self, layout):
        self.selectAllCB.setChecked(False)
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item.widget(): 
                widgetToRemove = item.widget()
                layout.removeWidget(widgetToRemove)
                widgetToRemove.setParent(None)
            else: 
                layout.removeItem(item)
        

    def getRegexPattern(self, userPattern):
        # Convert user pattern into a regex pattern
        regexPattern = re.escape(userPattern)  # Escape special characters
        regexPattern = regexPattern.replace(r"\@", "")  # Remove escape on placeholders
        regexPattern = regexPattern.replace(r"\*", r"([^_]+)")  # Replace "*" (wildcard) with regex to match any value

        # Replace placeholders with named capturing groups
        regexPattern = regexPattern.replace("@objName", r"(?P<objName>[^_]+)?")
        regexPattern = regexPattern.replace("@texName", r"(?P<texName>[^_]+)")
        regexPattern = regexPattern.replace("@texType", r"(?P<texType>[^_]+)")
        regexPattern = regexPattern.replace("@id", r"(?P<id>\d+)?")  # Capture @id as a number

        # Adjust for file extension dynamically
        regexPattern = regexPattern.replace(r"\.ext", r"\.\w{2,4}")

        # Print generated regex pattern
        #print(f"Generated Regex Pattern: {regexPattern}")
        return regexPattern

    def verifyFolderPath(self, folderPath):
        pathRoot = folderPath.partition("/")[0]
        pathOriginal = folderPath.partition("/")[2]

        finalPath = None
        prefix = None

        if pathRoot == "$HOME":
            prefix=str(hou.getenv("HOME"))
        elif pathRoot == "$HIP":
            prefix=str(hou.getenv("HIP"))
        elif pathRoot == "$JOB":
            prefix=str(hou.getenv("JOB"))

        if prefix:
            finalPath = prefix + "/" + pathOriginal
        else:
            finalPath = folderPath

        return finalPath


#endregion

try:
    ktTextureImporter.close()
    ktTextureImporter.deleteLater()
except:
    pass

ktTextureImporter = ktTextureImporter()
ktTextureImporter.show()
