import hou
import os
from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

#region Texture
class Texture(object):
    """docstring for ClassName."""
    def __init__(self, baseColor, metalness, specularRough, normal=None, displacement=None):
        self.baseColor = baseColor
        self.metalness = metalness
        self.specularRough = specularRough
        self.normal = normal
        self.displacement = displacement
    
class ArnoldTexture(object):
    """docstring for ClassName."""
    def __init__(self, baseColor, metalness, specularRough, normal, displacement):
        super().__init__(baseColor=baseColor, metalness=metalness, specularRough=specularRough, normal=normal, displacement=displacement)

class KarmaTexture(object):
    """docstring for ClassName."""
    def __init__(self, baseColor, metalness, specularRough, normal, displacement):
        super().__init__(baseColor=baseColor, metalness=metalness, specularRough=specularRough, normal=normal, displacement=displacement)
#endregion

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

        layout.setSpacing(0)  # Remove internal spacing
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins around the layout

        self.setLayout(layout)

class TextureInfoWidget(QtWidgets.QWidget):
    def __init__(self, normal=False, displacement=False):
        super().__init__()

        # Using the same logic to handle visibility and creation of texture rows
        self.normal = normal
        self.displacement = displacement
        self.visibility = False

        # Create texture input widgets
        self.baseColorRow = ktTextureRowWidget("Base Color")
        self.metalnessRow = ktTextureRowWidget("Metalness")
        self.specularRoughRow = ktTextureRowWidget("Specular Rough")
        self.normalRow = ktTextureRowWidget("Normal") if self.normal else None
        self.displacementRow = ktTextureRowWidget("Displacement") if self.displacement else None

        # Create layout for the texture rows
        self.createLayouts()

    def createLayouts(self):
        """Create the layout for all texture rows."""
        self.informationLYT = QtWidgets.QVBoxLayout(self)

        # Add texture input widgets dynamically
        for row in [self.baseColorRow, self.metalnessRow, self.specularRoughRow, self.normalRow, self.displacementRow]:
            if row:
                self.informationLYT.addWidget(row)

        self.setLayout(self.informationLYT)

    def toggleVisibility(self, visibility):
        """Toggle the visibility of the texture rows."""
        self.baseColorRow.setVisible(visibility)
        self.metalnessRow.setVisible(visibility)
        self.specularRoughRow.setVisible(visibility)

        if self.normalRow:
            self.normalRow.setVisible(visibility)

        if self.displacementRow:
            self.displacementRow.setVisible(visibility)
            
    
class ktTextureWidget(QtWidgets.QWidget):
    def __init__(self, normal=False, displacement=False):
        super().__init__()
        
        self.baseColor = True
        self.metalness = True
        self.specularRough = True
        self.normal = normal
        self.displacement = displacement
        self.visibility = False
        
        """
        UI Creation
        """
        self.createWidgets()
        self.createLayouts()
        self.createConnections()


    def _createSummaryRow(self,label):
        """Creates a row with a QLabel and QCheckBox."""
        layout = QtWidgets.QVBoxLayout()
        lbl = QtWidgets.QLabel(label)
        cb = QtWidgets.QCheckBox()
        cb.setEnabled(False)

        layout.addWidget(lbl)
        layout.addWidget(cb)

        layout.setSpacing(0) 
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

        self.visibilityBTN = QtWidgets.QPushButton(">>")
        self.visibilityBTN.setFlat(True)

        # Set the button's style using setStyleSheet
        self.visibilityBTN.setStyleSheet("""
            QPushButton:flat {
                color: white;               /* White text */
                font-size: 16px;            /* Font size */
                border: 1px solid black;
                border-radius: 5px;         /* Rounded corners */
                padding: 10px 20px;         /* Padding inside the button */
            }
        """)

        # Create texture input widgets
        self.baseColorRow = ktTextureRowWidget("Base Color")
        self.baseColorRow.setVisible(self.visibility)
        self.metalnessRow = ktTextureRowWidget("Metalness")
        self.metalnessRow.setVisible(self.visibility)
        self.specularRoughRow = ktTextureRowWidget("Specular Rough")
        self.specularRoughRow.setVisible(self.visibility)
        self.normalRow = ktTextureRowWidget("Normal") if self.normal else None
        if self.normalRow:
            self.normalRow.setVisible(self.visibility)
        self.displacementRow = ktTextureRowWidget("Displacement") if self.displacement else None
        if self.displacementRow:
            self.displacementRow.setVisible(self.visibility)

    def createLayouts(self):
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.textureLYT = QtWidgets.QGridLayout(self)

        # Add Checkboxes
        self.textureLYT.addWidget(self.selectedCB, 0, 0)
        self.textureLYT.addWidget(self.nameTXT, 0, 1)

        # Add layouts to grid
        col = 2
        for layout in [self.baseColorSumLayout, self.metalnessSumLayout, self.specularRoughSumLayout, self.normalSumLayout, self.displacementSumLayout]:
            if layout:
                self.textureLYT.addLayout(layout, 0, col) 
                col += 1
        
        self.textureLYT.addWidget(self.visibilityBTN, 0, col) 

        """Information Layout"""
        self.informationLYT = QtWidgets.QVBoxLayout(self)  
        
        # Add texture input widgets dynamically
        for row in [self.baseColorRow, self.metalnessRow, self.specularRoughRow, self.normalRow, self.displacementRow]:
            if row:
                self.informationLYT.addWidget(row)


        self.mainLayout.addLayout(self.textureLYT)
        self.mainLayout.addLayout(self.informationLYT)

    def createConnections(self):
        """Connect signals to slots for automatic checkbox updating."""
        self.baseColorRow.txt.textChanged.connect(lambda text: self.baseColorCB.setChecked(bool(text.strip())))
        self.metalnessRow.txt.textChanged.connect(lambda text: self.metalnessCB.setChecked(bool(text.strip())))
        self.specularRoughRow.txt.textChanged.connect(lambda text: self.specularRoughCB.setChecked(bool(text.strip())))

        if self.normal:
            self.normalRow.txt.textChanged.connect(lambda text: self.normalCB.setChecked(bool(text.strip())))

        if self.displacement:
            self.displacementRow.txt.textChanged.connect(lambda text: self.displacementCB.setChecked(bool(text.strip())))

            # Connect visibility button to toggle texture row visibility
        self.visibilityBTN.clicked.connect(self.toggleVisibility)

    def toggleVisibility(self):
        """Toggle the visibility of the texture rows using the visibility flag."""
        # Toggle visibility flag
        self.visibility = not self.visibility
        
        # Set the visibility of each row based on the visibility flag
        self.baseColorRow.setVisible(self.visibility)
        self.metalnessRow.setVisible(self.visibility)
        self.specularRoughRow.setVisible(self.visibility)

        if self.normal:
            self.normalRow.setVisible(self.visibility)

        if self.displacement:
            self.displacementRow.setVisible(self.visibility)

            
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


def getHoudiniMainWindow():
    return hou.qt.mainWindow()
        

class CreateWindow(QtWidgets.QDialog):
    def __init__(self, parent=getHoudiniMainWindow()):
        super(CreateWindow, self).__init__(parent)
        
        self.setWindowTitle('Texture importer | kt_TextureImporter')
        self.setMinimumWidth(600)
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
        self.textureTypeCMB.setFixedWidth(150)
        self.clearBTN = QtWidgets.QPushButton("Clear")
        self.clearBTN.setFixedHeight(40)


        self.folderPathTXT = QtWidgets.QLineEdit()
        self.folderPathBTN = hou.qt.FileChooserButton()
        self.folderPathBTN.setFileChooserTitle("Please select a directory")
        self.folderPathBTN.setFileChooserMode(hou.fileChooserMode.Read)
        self.folderPathBTN.setFileChooserFilter(hou.fileType.Directory)

        self.testTextWidget = ktTextureWidget(normal=True, displacement=True)

            
    def createLayouts(self):
        """Function that creates all the layouts and add widgets"""
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        self.textureTypeLYT = QtWidgets.QHBoxLayout()
        self.textureTypeLYT.addWidget(QtWidgets.QLabel('Texture: '))
        self.textureTypeLYT.addWidget(self.textureTypeCMB)
        self.textureTypeLYT.addStretch(1)
        self.textureTypeLYT.addWidget(self.clearBTN)

        self.folderPathLYT = QtWidgets.QHBoxLayout()
        self.folderPathLYT.addWidget(QtWidgets.QLabel('Folder: '))
        self.folderPathLYT.addWidget(self.folderPathTXT)
        self.folderPathLYT.addWidget(self.folderPathBTN)

        self.mainLayout.addLayout(self.textureTypeLYT)
        self.mainLayout.addLayout(self.folderPathLYT)

        self.mainLayout.addWidget(self.testTextWidget)

            
    def createConnections(self):
        self.folderPathBTN.fileSelected.connect(self.setTexturePathLineEditText)
            
    def setTexturePathLineEditText(self, file_path):
        self.folderPathTXT.setText(file_path)
    
    def assignTexture(self):
        material = hou.selectedNodes()[0]
        path = self.folderPathTXT.text()
        assignTextureToMaterial(path, material)

#endregion

try:
    CreateWindow.close()
    CreateWindow.deleteLater()
except:
    pass

CreateWindow = CreateWindow()
CreateWindow.show()
