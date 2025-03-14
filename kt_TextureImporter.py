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
    
    def createTexture(self): #We need it here so we can create textures depending on the type (it doesn't depend on the widget or window)
        pass

    def showInformation(self):
        print("-----------------------------------------")
        print(f"name: {self.name}")
        print(f"baseColor: {self.baseColor}")
        print(f"metalness: {self.metalness}")
        print(f"specularRough: {self.specularRough}")
        print(f"normal: {self.normal}")
        print(f"displacement: {self.displacement}")
        print("-----------------------------------------")

class ArnoldTexture(Texture):
    """docstring for ClassName."""
    def __init__(self, name="ArnoldTexture", baseColor=None, metalness=None, specularRough=None, normal=None, displacement=None):
        super().__init__(name=name, baseColor=baseColor, metalness=metalness, specularRough=specularRough, normal=normal, displacement=displacement)

class KarmaTexture(Texture):
    """docstring for ClassName."""
    def __init__(self, name="KarmaTexture", baseColor=None, metalness=None, specularRough=None, normal=None, displacement=None):
        super().__init__(name=name, baseColor=baseColor, metalness=metalness, specularRough=specularRough, normal=normal, displacement=displacement)
#endregion

#region Widget
class ktTextureRowWidget(QtWidgets.QWidget):
    def __init__(self, label, fileType=hou.fileType.Image):
        super().__init__()

        self.label = label
        self.fileType = fileType
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

        # Connect the button's signal to update the text field
        self.btn.fileSelected.connect(lambda path: self.txt.setText(path))

        # Add widgets to the layout
        layout.addWidget(lbl)
        layout.addWidget(self.txt)
        layout.addWidget(self.btn)

        layout.setSpacing(5)  # Remove internal spacing
        layout.setContentsMargins(5, 0, 5, 0)  # Remove margins around the layout

        self.setLayout(layout)

    
class ktTextureWidget(QtWidgets.QWidget):
    def __init__(self, normal=False, displacement=False, texture=None):
        super().__init__()
        
        self.baseColor = True
        self.metalness = True
        self.specularRough = True
        self.normal = normal
        self.displacement = displacement
        self.visibility = False
        self.texture = texture

        
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
        # Using helper function for checkboxes
        # Create checkbox layouts
        self.baseColorSumLayout, self.baseColorCB = self._createSummaryRow("BC")
        self.metalnessSumLayout, self.metalnessCB = self._createSummaryRow("M")
        self.specularRoughSumLayout, self.specularRoughCB = self._createSummaryRow("SR")
        self.normalSumLayout, self.normalCB = self._createSummaryRow("N") if self.normal else (None, None)
        self.displacementSumLayout, self.displacementCB = self._createSummaryRow("D") if self.displacement else (None, None)

        self.visibilityBTN = QtWidgets.QPushButton() 
        #https://houdini-icons.dev/
        self.iconCollapsed = hou.qt.Icon("KEYS_Right")   # Left arrow when collapsed hicon:/SVGIcons.index?KEYS_Right.svg
        self.iconExpanded =  hou.qt.Icon("KEYS_Down")    # Down arrow when expanded hicon:/SVGIcons.index?KEYS_Down.svg
        self.visibilityBTN.setIcon(self.iconCollapsed)  # Default icon
        self.visibilityBTN.setFlat(True)
        self.visibilityBTN.setFixedWidth(30)

        # Set the button's style using setStyleSheet
        self.visibilityBTN.setStyleSheet("""
            QPushButton:flat {
                color: white;               /* White text */
                font-size: 16px;            /* Font size */
                border: 0px solid black;
                border-radius: 0px;         /* Rounded corners */
                padding: 10px 20px;         /* Padding inside the button */
            }
        """)

        # Create texture input widgets
        self.baseColorRow = ktTextureRowWidget("Base Color")
        self.metalnessRow = ktTextureRowWidget("Metalness")
        self.specularRoughRow = ktTextureRowWidget("Specular Rough")
        self.normalRow = ktTextureRowWidget("Normal") if self.normal else None
        self.displacementRow = ktTextureRowWidget("Displacement") if self.displacement else None

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
            QGroupBox {
                background-color: #4D4D4D;
                border: 0px solid #4D4D4D;  /* Border color and thickness */
                border-radius: 0px;
            }

            QGroupBox::title {
                color: white;  /* Title color (optional) */
            }
        """)

        # Add Checkboxes
        self.headerLYT.addWidget(self.selectedCB)
        self.headerLYT.addWidget(self.nameTXT)

        # Add layouts to grid
        for layout in [self.baseColorSumLayout, self.metalnessSumLayout, self.specularRoughSumLayout, self.normalSumLayout, self.displacementSumLayout]:
            self.headerLYT.addLayout(layout) 
                
        
        self.headerLYT.addWidget(self.visibilityBTN) 

        """Information Layout"""
        self.informationLYT = QtWidgets.QVBoxLayout(self) 
        self.informationLYT.setContentsMargins(0, 5, 0, 5)  # Remove all margins (left, top, right, bottom)

        self.informationGB = QtWidgets.QGroupBox("")
        self.informationGB.setLayout(self.informationLYT)
        self.informationGB.setVisible(self.visibility)
        self.informationGB.setStyleSheet("""
            QGroupBox {
                background-color: #363636;
                border: 0px solid #363636;  /* Border color and thickness */
                border-radius: 0px;
                padding: 0;
                margin: 0;
            }

            QGroupBox::title {
                color: white;  /* Title color (optional) */
            }
        """)
        
        
        # Add texture input widgets dynamically
        for row in [self.baseColorRow, self.metalnessRow, self.specularRoughRow, self.normalRow, self.displacementRow]:
            if row:
                self.informationLYT.addWidget(row)


        #self.mainLayout.addLayout(self.headerLYT)
        self.mainLayout.addWidget(self.headerGB)
        self.mainLayout.addWidget(self.informationGB)

    def createConnections(self):
        """Connect signals to slots for automatic checkbox updating."""
        self.nameTXT.textChanged.connect(lambda text: self.updateInformation('name', text, None))
        # Update Texture and setChecked when text changes
        self.baseColorRow.txt.textChanged.connect(lambda text: self.updateInformation('baseColor', text, self.baseColorCB))
        self.metalnessRow.txt.textChanged.connect(lambda text: self.updateInformation('metalness', text, self.metalnessCB))
        self.specularRoughRow.txt.textChanged.connect(lambda text: self.updateInformation('specularRough', text, self.specularRoughCB))

        if self.normal:
            self.normalRow.txt.textChanged.connect(lambda text: self.updateInformation('normal', text, self.normalCB))

        if self.displacement:
            self.displacementRow.txt.textChanged.connect(lambda text: self.updateInformation('displacement', text, self.displacementCB))

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
        setattr(self.texture, textureProperty, text.strip())  # Update the corresponding texture property
        if checkbox:
            checkbox.setChecked(bool(text.strip()))  # Set the checkbox status


    def loadInformation(self):
        #texture = Texture() # type: Texture
        self.nameTXT.setText(self.texture.name)
        self.baseColorRow.txt.setText(self.texture.baseColor)
        self.metalnessRow.txt.setText(self.texture.metalness)
        self.specularRoughRow.txt.setText(self.texture.specularRough)
        self.normalRow.txt.setText(self.texture.normal)
        self.displacementRow.txt.setText(self.texture.displacement)
        
        

#endregion
            
#region Main

def assignTextureToMaterial(path, material):
    files = os.listdir(path)
    for image in files:
        if 'diffuse.jpg' in image:
            material.parn('basecolor_useTexture').set(True)
            material.parn('basecolor_texture').set(path + '/' + image)
        elif 'roughness.jpg' in image:
            material.parn('rough_useTexture').set(True)
            material.parn('rough_texture').set(path + '/' + image)

def assignTexture(self):
    material = hou.selectedNodes()[0]
    path = self.folderPathTXT.text()
    assignTextureToMaterial(path, material)


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


        self.folderPathTXT = QtWidgets.QLineEdit()
        self.folderPathTXT.setReadOnly(True)
        self.folderPathBTN = hou.qt.FileChooserButton()
        self.folderPathBTN.setFileChooserTitle("Please select a directory")
        self.folderPathBTN.setFileChooserMode(hou.fileChooserMode.Read)
        self.folderPathBTN.setFileChooserFilter(hou.fileType.Directory)


        self.selectAllCB = QtWidgets.QCheckBox()
        self.createBTN = QtWidgets.QPushButton("Create")
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
        self.mainLayout.addLayout(self.folderPathLYT)
        self.mainLayout.addSpacing(25)
        self.mainLayout.addLayout(self.execLYT)
        self.mainLayout.addWidget(self.texScroll)

    def createConnections(self):
        self.folderPathBTN.fileSelected.connect(self.onClick_folderPathBTN)
        self.matPathBTN.nodeSelected.connect(self.onClick_matPathBTN)
        self.clearBTN.clicked.connect(self.onClick_clearBTN)
        self.selectAllCB.clicked.connect(self.onChange_selectAllCB)

    def onClick_clearBTN(self):
        self.clearLayout(self.texLYT)
        self.folderPathTXT.setText("")
    
    def onClick_folderPathBTN(self, filePath):
        if filePath:
            self.folderPathTXT.setText(filePath)
            self.loadTextures()
    
    def onClick_matPathBTN(self, node):
        if node:
            self.matPathTXT.setText(str(node.path()))
    
    def onChange_selectAllCB(self):
        if self.selectAllCB.isChecked:
            self.checkAllTextures()
    
    def loadTextures(self):
        self.clearLayout(self.texLYT)
        self.texList = []

        if self.textureTypeCMB.currentText() == "Arnold":
            testTexture = ArnoldTexture(name="Prueba", baseColor="Test.png", metalness="Test2.png")
            textureWD = ktTextureWidget(normal=True, displacement=True, texture=testTexture)
            self.texLYT.addWidget(textureWD)
            self.texList.append(textureWD)


        self.texLYT.addStretch()

        folder_path = "D:/OP_Houdini_Pipeline/HOUdini_Resources/HOUdini_Resources/textures/wall block/01_PUBLISH"

        user_pattern = "*_@objName_*_@texture_*_@texName_*.ext"

        # Convert user pattern into a regex pattern
        regex_pattern = re.escape(user_pattern)  # Escape special characters
        regex_pattern = regex_pattern.replace(r"\@", "")  # Remove escape on placeholders

        # Replace "*" (wildcard) with regex to match any value
        regex_pattern = regex_pattern.replace(r"\*", r"([^_]+)")  

        # Replace placeholders with named capturing groups
        regex_pattern = regex_pattern.replace("@objName", r"(?P<objName>[^_]+)")
        regex_pattern = regex_pattern.replace("@texture", r"(?P<texture>[^_]+)")
        regex_pattern = regex_pattern.replace("@texName", r"(?P<texName>[^_]+)")

        # Adjust for file extension dynamically
        regex_pattern = regex_pattern.replace(r"\.ext", r"\.\w{2,4}")

        # Debugging: Print generated regex pattern
        #print(f"Generated Regex Pattern: {regex_pattern}")

        textures = {}

        # Loop through files in the directory
        for filename in os.listdir(folder_path):
            
            if filename.endswith((".exr", ".tx")):  # Filter by file type
                match = re.match(regex_pattern, filename)
                if match:
                    objName = match.group("objName")
                    textureType = match.group("texture")
                    texName = match.group("texName")

                    finalName = objName + "_" + texName

                    # Create texture object if not exists
                    if finalName not in textures:
                        textures[finalName] = Texture(name=finalName)

                    # Assign the correct texture type (store only the filename)
                    if textureType == "BaseColor":
                        textures[finalName].baseColor = filename
                    elif textureType == "Metalness":
                        textures[finalName].metalness = filename
                    elif textureType == "Roughness":
                        textures[finalName].specularRough = filename
                    elif textureType == "Normal":
                        textures[finalName].normal = filename
                    elif textureType == "Displacement" or textureType == "Height" :
                        textures[finalName].displacement = filename

        # Display texture information
        for texture in textures.values():
            texture.showInformation()


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

    


#endregion

try:
    ktTextureImporter.close()
    ktTextureImporter.deleteLater()
except:
    pass

ktTextureImporter = ktTextureImporter()
ktTextureImporter.show()
