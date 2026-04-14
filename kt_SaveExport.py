import hou
import os
import re
import voptoolutils

try:
    from PySide6 import QtCore, QtWidgets, QtGui
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui


#region Objects
class Texture(object):
    """
    A class representing a texture object with various material properties.

    Attributes:
        name (str): The name of the texture.
        baseColor (str, optional): The base color texture file value.
        metalness (str, optional): The metalness texture file value.
        specularRough (str, optional): The specular roughness texture file value.
        normal (str, optional): The normal map texture file value.
        displacement (str, optional): The displacement map texture file value.
        ambientOcclusion (str, optional): The Ambient Occlusion map texture file value. Defaults to None.
        textureMapping (dict): A dictionary mapping texture attributes to their corresponding labels, abbreviations and mappings.
    """
    def __init__(self, name, baseColor=None, metalness=None, specularRough=None, normal=None, displacement=None, ambientOcclusion=None,
                 opacity=None):
        """
        Initializes a Texture object with various material properties.

        Args:
            name (str): The name of the texture.
            baseColor (str, optional): The base color texture file value. Defaults to None.
            metalness (str, optional): The metalness texture file value. Defaults to None.
            specularRough (str, optional): The specular roughness texture file value. Defaults to None.
            normal (str, optional): The normal map texture file value. Defaults to None.
            displacement (str, optional): The displacement map texture file value. Defaults to None.
            ambientOcclusion (str, optional): The Ambient Occlusion map texture file value. Defaults to None.
        
        Attributes:
            textureMapping (dict): A dictionary mapping texture attributes to their corresponding labels, abbreviations and mappings.
        """
        self.name = name
        self.baseColor = baseColor
        self.metalness = metalness
        self.specularRough = specularRough
        self.normal = normal
        self.displacement = displacement
        self.ambientOcclusion = ambientOcclusion
        self.opacity = opacity

        self.textureMapping = {
            "baseColor": {"label": "Base Color", "abbreviation": "BC", "mapping": ["basecolor", "base", "albedo"]},
            "metalness": {"label": "Metalness", "abbreviation": "M", "mapping": ["metalness", "metallic"]},
            "specularRough": {"label": "Specular Rough", "abbreviation": "SR", "mapping": ["roughness", "specular"]},
            "normal": {"label": "Normal", "abbreviation": "N", "mapping": ["normal"]},
            "displacement": {"label": "Displacement", "abbreviation": "D", "mapping": ["height", "displacement"]},
            "ambientOcclusion": {"label": "Ambient Occlusion", "abbreviation": "AO", "mapping": ["ao","ambientocclusion","ambientoclussion"]},
            "opacity": {"label": "Opacity", "abbreviation": "OP", "mapping": ["opacity"]},
        }



    
    def createTexture(self):
        """Placeholder method for creating a texture object."""
        pass

    def getTypeFromAttr(self, attr, text):
        """
        Determines the texture type based on a given attribute and text mapping.

        Args:
            attr (str): The attribute name to check within the texture mapping.
            text (str): The text used to identify the corresponding texture type.

        Returns:
            str or None: The parent texture type if found, otherwise None.
        """
        for parent, children in self.textureMapping.items():
            if text in children[attr]:
                return parent
        return None

    def showInformation(self):
        """ Prints all attributes of the texture object except the `textureMapping` dictionary."""
        print("-----------------------------------------")
        for attribute, value in vars(self).items():  # Iterate over the instance's attributes
            if attribute != "textureMapping":  # Exclude textureMapping from being printed
                print(f"{attribute}: {value}")
        print("-----------------------------------------")

class ArnoldTexture(Texture):
    """
    This class extends the `Texture` class and provides functionality to create 
    an Arnold Material Builder node with various texture inputs in a shader network.

    Attributes:
        Inherits all attributes from the `Texture` class.
    """
    def __init__(self, name="ArnoldTexture", baseColor=None, metalness=None, specularRough=None, normal=None, displacement=None, ambientOcclusion=None,
                 opacity=None):
        """Initializes a ArnoldTexture with various material properties

        Args:
            name (str, optional): Name of the texture. Defaults to "ArnoldTexture".
            baseColor (str, optional): The baseColor texture file value. Defaults to None.
            metalness (str, optional): The metalness texture file value. Defaults to None.
            specularRough (str, optional): The specularRough texture file value. Defaults to None.
            normal (str, optional): The displacement texture file value. Defaults to None.
            displacement (str, optional): The base color texture file value. Defaults to None.
        """
        super().__init__(name=name, baseColor=baseColor, metalness=metalness, specularRough=specularRough, normal=normal, displacement=displacement, ambientOcclusion=ambientOcclusion,
                         opacity=opacity)
    
    def createTexture(self, parentNode, path, imageFormat=None):
        """Creates an Arnold Material Builder node connecting Arnold shader nodes for various texture attributes.

        Args:
            parentNode (obj): Parent node where all nodes will be created an connected
            path (str): Folder path where the files will be located

        Returns:
            obj: Returns material node created with everything connected
        """
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

            if self.ambientOcclusion:
                ambientOcclusionNode = materialBuilderNode.createNode("arnold::image", f"{self.name}_AO")
                ambientOcclusionNode.parm("filename").set(getFullPath(self.ambientOcclusion, path))
                multiplyNode = materialBuilderNode.createNode("arnold::multiply", f"{self.name}_Multi")
                multiplyNode.setNamedInput("input1", baseColorNode, "rgba")
                multiplyNode.setNamedInput("input2", ambientOcclusionNode, "rgba")

                colorCorrectNode.setNamedInput("input", multiplyNode, "rgb")
            else:
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

            rangeNode = materialBuilderNode.createNode("arnold::range", f"{self.name}_D_RNG")
            rangeNode.parm("output_max").set(0.001) 
            rangeNode.setNamedInput("input", displacementNode, "r")
            outMaterialNode.setNamedInput("displacement", rangeNode, "r")

        if self.opacity:
            opacityNode = materialBuilderNode.createNode("arnold::image", f"{self.name}_OP")
            rangeNode = materialBuilderNode.createNode("arnold::range", f"{self.name}_OP_RNG")
            rangeNode.parm("output_min").set(1) 
            rangeNode.setNamedInput("input", opacityNode, "rgba")

            standardSurfaceNode.setNamedInput("opacity", rangeNode, "rgb")

        # Organize layout
        materialBuilderNode.layoutChildren()

        return materialBuilderNode

class KarmaTexture(Texture):
    """
    This class extends the `Texture` class and provides functionality to create 
    an Karma Material Builder node with various texture inputs in a shader network.

    Attributes:
        Inherits all attributes from the `Texture` class.
    """
    def __init__(self, name="KarmaTexture", baseColor=None, metalness=None, specularRough=None, normal=None, displacement=None, ambientOcclusion=None,
                 opacity=None):
        """Initializes a KarmaTexture with various material properties

        Args:
            name (str, optional): Name of the texture. Defaults to "KarmaTexture".
            baseColor (str, optional): The baseColor texture file value. Defaults to None.
            metalness (str, optional): The metalness texture file value. Defaults to None.
            specularRough (str, optional): The specularRough texture file value. Defaults to None.
            normal (str, optional): The displacement texture file value. Defaults to None.
            displacement (str, optional): The base color texture file value. Defaults to None.
            ambientOcclusion (str, optional): The ambient occlusion texture file value. Defaults to None.
        """
        super().__init__(name=name, baseColor=baseColor, metalness=metalness, specularRough=specularRough, normal=normal, displacement=displacement, ambientOcclusion=ambientOcclusion,
                         opacity=opacity)


    def createTexture(self, parentNode, path, imageFormat=None):
        """Creates an Karma Material Builder node connecting MaterialX shader nodes for various texture attributes.

        Args:
            parentNode (obj): Parent node where all nodes will be created an connected
            path (str): Folder path where the files will be located

        Returns:
            obj: Returns material node created with everything connected
        """
        # Create the Arnold Material Builder node
        mask = voptoolutils.KARMAMTLX_TAB_MASK #voptoolutils._setupMtlXBuilderSubnet(subnet_node=subnet_node, destination_node=dst_node, name=name, mask=mask, folder_label=folder_label, render_context=render_context)

        materialBuilderNode = parentNode.createNode("subnet", self.name)
        voptoolutils._setupMtlXBuilderSubnet(materialBuilderNode, "karmamaterial", "karmamaterial", mask, "Karma Material Builder", "kma")

        standardSurfaceNode = materialBuilderNode.node("mtlxstandard_surface")

        outMaterialNode = materialBuilderNode.node("Material_Outputs_and_AOVs")
        outDisplacement = materialBuilderNode.node("mtlxdisplacement") 

        imageType = "mtlximage"


        def getFullPath(textureName, path):
            return os.path.join(path, textureName) if textureName else None
        
        # Add the various texture nodes and connect them to the material
        if self.baseColor:
            baseColorNode = materialBuilderNode.createNode(imageType, f"{self.name}_BC")
            baseColorNode.parm("file").set(getFullPath(self.baseColor, path))
            baseColorNode.parm("signature").set("color3")
            colorCorrNode = materialBuilderNode.createNode("mtlxcolorcorrect", f"{self.name}_CC")
            colorCorrNode.setNamedInput("in", baseColorNode, "out")
            standardSurfaceNode.setNamedInput("base_color", colorCorrNode, "out")

        if self.ambientOcclusion:
            ambientOcclusionNode = materialBuilderNode.createNode(imageType, f"{self.name}_AO")
            ambientOcclusionNode.parm("file").set(getFullPath(self.ambientOcclusion, path))
            ambientOcclusionNode.parm("signature").set("color3")

            standardSurfaceNode.setNamedInput("base", ambientOcclusionNode, "out")

        if self.metalness:
            metalnessNode = materialBuilderNode.createNode(imageType, f"{self.name}_M")
            metalnessNode.parm("file").set(getFullPath(self.metalness, path))
            metalnessNode.parm("signature").set("default")
            standardSurfaceNode.setNamedInput("metalness", metalnessNode, "out")

        if self.specularRough:
            specularRoughNode = materialBuilderNode.createNode(imageType, f"{self.name}_SR")
            specularRoughNode.parm("file").set(getFullPath(self.specularRough, path))
            specularRoughNode.parm("signature").set("default")
            standardSurfaceNode.setNamedInput("specular_roughness", specularRoughNode, "out")

        if self.normal:
            normalNode = materialBuilderNode.createNode(imageType, f"{self.name}_N")
            normalNode.parm("file").set(getFullPath(self.normal, path))
            normalNode.parm("signature").set("vector3")

            normalMapNode = materialBuilderNode.createNode("mtlxnormalmap", f"{self.name}_NM") 
            normalMapNode.setNamedInput("in", normalNode, "out")
            standardSurfaceNode.setNamedInput("normal", normalMapNode, "out")

        if self.displacement:
            displacementNode = materialBuilderNode.createNode(imageType, f"{self.name}_D")
            displacementNode.parm("file").set(getFullPath(self.displacement, path))
            displacementNode.parm("signature").set("default")
            outDisplacement.setNamedInput("displacement", displacementNode, "out")

        # Organize layout
        materialBuilderNode.layoutChildren()

        return materialBuilderNode

class ComponentMesh(object):

    def __init__(self, name, mainPath, file = None, materialLibrary = None, compOutNode=None, compMatNode = None):

        self.name = name
        self.mainPath = mainPath
        self.file = file
        self.materialLibrary = materialLibrary
        self.compOutNode = compOutNode
        self.compMatNode = compMatNode

    def getTypeFromAttr(self, label, text):
        """
        Determines the texture type based on a given attribute and text mapping.

        Args:
            attr (str): The attribute name to check within the texture mapping.
            text (str): The text used to identify the corresponding texture type.

        Returns:
            str or None: The parent texture type if found, otherwise None.
        """
        for parent, children in self.fieldMapping.items():
            if text in children[label]:
                return parent
        return None


    def showInformation(self):
        """ Prints all attributes of the texture object except the `textureMapping` dictionary."""
        print("-----------------------------------------")
        for attribute, value in vars(self).items():  # Iterate over the instance's attributes
            print(f"{attribute}: {value}")
        print("-----------------------------------------")

    def createComponent(self, parentNode, path, scale, color):

        def getFullPath(name, path):
            return os.path.join(path, name) if name else None

        # Component Geometry
        compNode = parentNode.createNode('componentgeometry')
        compNode.parm("authortimesamples").set('auto')

        compGeoNode = compNode.node("sopnet/geo")

        abcNode = compGeoNode.createNode('alembic')
        abcNode.parm("fileName").set(getFullPath(self.file, path))

        transNode = compGeoNode.createNode('xform')
        transNode.parm("scale").set(scale)
        transNode.setInput(0, abcNode)

        defaultNode = compGeoNode.node('default')
        defaultNode.setInput(0, transNode)

        unpackNode = compGeoNode.createNode('unpack')
        unpackNode.setInput(0, transNode)

        wrapNode = compGeoNode.createNode('shrinkwrap::2.0')
        wrapNode.setInput(0, unpackNode)
        
        colorNode = compGeoNode.createNode('color')
        r, g, b = color.rgb()
        colorNode.parm("colorr").set(r)
        colorNode.parm("colorg").set(g)
        colorNode.parm("colorb").set(b)
        colorNode.setInput(0, wrapNode)

        proxyNode = compGeoNode.node('proxy')
        proxyNode.setInput(0, colorNode)

        compGeoNode.layoutChildren()

        # Component Material
        self.compMatNode = parentNode.createNode('componentmaterial')
        self.compMatNode.setInput(0, compNode)
        self.compMatNode.parm("addmateriallibrary").pressButton()
        self.materialLibrary = self.compMatNode.input(1)

        # Component Output
        self.compOutNode = parentNode.createNode('componentoutput', self.name)
        self.compOutNode.parm("lopoutput").set(f'{path}Export/`chs("name")`/`chs("filename")`')

        #self.compOutNode.parm("localizesubdir").set(f'{hou.getenv("HIP")}/usd/textures')

        self.compOutNode.parm("localizesubdir").set(f'{hou.expandString(path)}usd/textures')

        self.compOutNode.setInput(0, self.compMatNode)



    def connectTextures(self):
        fileName = self.file.split(".")[0]

        # 1. Get the path
        primPath = f'/ASSET/geo/render/{fileName}/'
        texPath = self.materialLibrary.parm("matpathprefix").eval() #/ASSET/mtl/
    
        # 2. Get all the textures inside the material library
        texList = [child.path() for child in self.materialLibrary.children()]
        matAssignList = []

        for tex in texList:
            texName = tex.split("/")[-1]
            newPrim = f"{primPath}{texName}/{texName}_Shape"
            newMat = f"{texPath}{texName}"

            matAssignList.append((newPrim, newMat))

            #print(f"PRIM:  {newPrim}")
            #print(f"MAT:  {newMat}")

        # 3. Assign materials to Component Material, depending on the amount of elements
        compMat = self.compMatNode 

        compMat.parm("nummaterials").set(len(matAssignList))

        for i, (prim, mat) in enumerate(matAssignList, start=1):
            compMat.parm(f"primpattern{i}").set(prim)
            compMat.parm(f"matspecpath{i}").set(mat)
        
        


#endregion

#region Widget

class ktFileRowWidget(QtWidgets.QWidget):
    def __init__(self, label, fileType=hou.fileType.Image, mainPath=None):
        """Creates a horizontal widget that contains a label, text field and button.

        Args:
            label (str): _description_
            fileType (hou.fileType, optional): Type of file Type that the selection is going to filter. Defaults to hou.fileType.Image.
            mainPath (str, optional): Folder Path selected by the user. Defaults to None.
        """
        super().__init__()

        self.label = label
        self.fileType = fileType
        self.mainPath = mainPath
        self.initUI()

    def initUI(self):
        """Set up the layout, label, text field and button."""
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
        self.btn.fileSelected.connect(self.onFileSelected_btn)

        # Add widgets to the layout
        layout.addWidget(lbl)
        layout.addWidget(self.txt)
        layout.addWidget(self.btn)

        layout.setSpacing(5)  # Remove internal spacing
        layout.setContentsMargins(5, 0, 5, 0)  # Remove margins around the layout

        self.setLayout(layout)

    def onFileSelected_btn(self, path):
        """Update the text field when a file is selected but only the relativePath.

        Args:
            path (str): Full path selected by the user
        """
        
        relativePath = os.path.relpath(path, self.mainPath)
        relativePath = relativePath.replace("\\", "/")
        self.txt.setText(relativePath)

class ktTextureWidget(QtWidgets.QWidget):
    """
    A Qt widget for displaying and managing texture properties in a UI.

    This widget provides an interface for users to view and modify texture attributes.
    It dynamically creates UI elements based on the given texture's properties and
    allows toggling visibility of detailed texture inputs.

    Attributes:
        visibility (bool): Determines if texture rows are visible.
        texture (Texture): The texture object containing attributes like base color, normal, etc.
        mainPath (str): The main directory path where texture files are stored.
        selectedCB (QCheckBox): Checkbox for selecting the texture.
        nameTXT (QLineEdit): Text input for the texture's name.
        summaryLayouts (list): List of dynamically created layouts for texture attributes.
        textureRows (list): List of dynamically created texture row widgets.
        visibilityBTN (QPushButton): Button for toggling visibility of detailed texture inputs.
        headerLYT (QHBoxLayout): Layout for the header section.
        informationLYT (QVBoxLayout): Layout for detailed texture inputs.
    """
    def __init__(self, texture=None, mainPath=None):
        """
        Initializes the ktTextureWidget with a given texture and path.

        Args:
            texture (Texture, optional): The texture object containing material properties. Defaults to None.
            mainPath (str, optional): The main directory path where texture files are stored. Defaults to None.
        """
        super().__init__()
        
        self.visibility = False
        self.texture = texture
        self.mainPath = mainPath
        

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.loadInformation()


    def _createSummaryRow(self,label):
        """
        Creates a row with a QLabel and a QCheckBox for summarizing texture properties.

        Args:
            label (str): The text label for the row.

        Returns:
            tuple: A layout containing the label and the checkbox widget itself.
        """
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
        """
        Creates UI widgets for the texture properties.

        Initializes checkboxes, text fields, visibility buttons, and dynamically generates
        texture-related rows based on the texture object.
        """
        self.selectedCB = QtWidgets.QCheckBox()
        self.nameTXT = QtWidgets.QLineEdit()

        # Storage for checkbox layouts
        self.summaryLayouts = []
        self.textureRows = []

        for attr, details in self.texture.textureMapping.items():
            if hasattr(self.texture, attr):  # Only create if the attribute exists
                sumLayout, checkbox = self._createSummaryRow(details["abbreviation"])
                self.summaryLayouts.append((sumLayout, checkbox))
                
                rowWidget = ktFileRowWidget(label=details["label"], mainPath=self.mainPath)
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
        """
        Organizes and arranges UI elements into structured layouts.

        Sets up the header section, summary layout, and detailed texture input layout
        while applying styling and spacing.
        """
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.headerLYT = QtWidgets.QHBoxLayout()
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
        self.informationLYT = QtWidgets.QVBoxLayout() 
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
        """
        Establishes connections between UI elements and their respective functions.

        Connects signals such as textChanged and button clicks to methods that handle
        updating texture properties and toggling visibility.
        """
        self.nameTXT.textChanged.connect(lambda text: self.updateInformation('name', text, None))

        # Dynamically connect each texture row's textChanged signal
        for row, (sumLayout, checkbox) in zip(self.textureRows, self.summaryLayouts):
            row.txt.textChanged.connect(lambda text, row=row, checkbox=checkbox: self.updateInformation(row.label, text, checkbox))

        # Connect visibility button to toggle texture row visibility
        self.visibilityBTN.clicked.connect(self.toggleVisibility)

    def toggleVisibility(self):
        """Toggle the visibility of the texture rows using the visibility flag."""
        self.visibility = not self.visibility
        self.informationGB.setVisible(self.visibility)
        self.visibilityBTN.setIcon(self.iconExpanded if self.visibility else self.iconCollapsed)

    def updateInformation(self, textureProperty, text, checkbox):
        """
        Updates the texture object based on user input.

        Args:
            textureProperty (str): The texture property being modified.
            text (str): The new value entered by the user.
            checkbox (QCheckBox, optional): The checkbox linked to this property, updated accordingly.
        """
        if textureProperty == 'name':
            textureType = 'name'
        else:
            textureType = self.texture.getTypeFromAttr("label", textureProperty)
        setattr(self.texture, str(textureType), text.strip())  # Update the corresponding texture property

        if checkbox:
            checkbox.setChecked(bool(text.strip()))  # Set the checkbox status


    def loadInformation(self):
        """
        Loads existing texture information into the UI. Fills text fields with saved texture values 
        and updates checkboxes based on existing data.
        """
        self.nameTXT.setText(self.texture.name)
        # Dynamically load information for each texture row
        for row, (attr, details) in zip(self.textureRows, self.texture.textureMapping.items()):
            # Check if the attribute exists in the texture and load its value
            value = getattr(self.texture, attr, "")
            #print(f"type: {attr} value: {value}")
            row.txt.setText(value)

class ktObjectWidget(QtWidgets.QWidget):

    def __init__(self, obj=None, mainPath=None):
        super().__init__()
        
        self.visibility = False
        self.mainPath = mainPath
        self.obj = obj

        self.createWidgets()
        self.createLayouts()
        self.createConnections()
        self.loadInformation()

    def createWidgets(self):
        """
        Creates UI widgets for the texture properties.

        Initializes checkboxes, text fields, visibility buttons, and dynamically generates
        texture-related rows based on the texture object.
        """
        self.selectedCB = QtWidgets.QCheckBox()
        self.nameTXT = QtWidgets.QLineEdit()

        self.collapsibleRows = []
        
        self.fileWidget = ktFileRowWidget(label='File', mainPath=self.mainPath, fileType=hou.fileType.Alembic)

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
        """
        Organizes and arranges UI elements into structured layouts.

        Sets up the header section, summary layout, and detailed texture input layout
        while applying styling and spacing.
        """
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.headerLYT = QtWidgets.QHBoxLayout()
        self.headerLYT.setContentsMargins(0, 0, 0, 0)
        self.headerGB = QtWidgets.QGroupBox("")
        self.headerGB.setLayout(self.headerLYT)
        self.headerGB.setFixedHeight(55)
        self.headerGB.setStyleSheet("""
            QGroupBox {background-color: #4D4D4D; border: 0px solid #4D4D4D; border-radius: 0px; }
            QGroupBox::title { color: white; }
        """)

        # Add Checkboxes
        self.headerLYT.addWidget(self.selectedCB)
        self.headerLYT.addWidget(self.nameTXT)
        self.headerLYT.addWidget(self.visibilityBTN) 

        """Information Layout"""
        self.informationLYT = QtWidgets.QVBoxLayout() 
        self.informationLYT.setContentsMargins(0, 5, 0, 5)  # Remove all margins (left, top, right, bottom)

        self.informationGB = QtWidgets.QGroupBox("")
        self.informationGB.setLayout(self.informationLYT)
        self.informationGB.setVisible(self.visibility)
        self.informationGB.setStyleSheet("""
            QGroupBox { background-color: #363636; border: 0px solid #363636; border-radius: 0px; padding: 0; margin: 0; }
            QGroupBox::title { color: white; }
        """)
        
        #
        self.informationLYT.addWidget(self.fileWidget)

        #self.mainLayout.addLayout(self.headerLYT)
        self.mainLayout.addWidget(self.headerGB)
        self.mainLayout.addWidget(self.informationGB)

    def createConnections(self):
        self.nameTXT.textChanged.connect(lambda text: self.updateInformation('name', text, None))
        self.fileWidget.txt.textChanged.connect(lambda text: self.updateInformation('file', text, None))

        self.visibilityBTN.clicked.connect(self.toggleVisibility)

    
    def updateInformation(self, fieldProperty, text, checkbox):
        """
        Updates the texture object based on user input.

        Args:
            textureProperty (str): The texture property being modified.
            text (str): The new value entered by the user.
            checkbox (QCheckBox, optional): The checkbox linked to this property, updated accordingly.
        """
        if fieldProperty == 'name':
            fieldType = 'name'
        elif fieldProperty == 'file':
            fieldType = 'file'

        setattr(self.obj, str(fieldType), text.strip())  # Update the corresponding texture property

        if checkbox:
            checkbox.setChecked(bool(text.strip()))  # Set the checkbox status

    def loadInformation(self):
        """
        Loads existing texture information into the UI. Fills text fields with saved texture values 
        and updates checkboxes based on existing data.
        """
        self.nameTXT.setText(self.obj.name)
        self.fileWidget.txt.setText(self.obj.file)


    def toggleVisibility(self):
        """Toggle the visibility of the texture rows using the visibility flag."""
        self.visibility = not self.visibility
        self.informationGB.setVisible(self.visibility)
        self.visibilityBTN.setIcon(self.iconExpanded if self.visibility else self.iconCollapsed)

class ktRangeSlider(QtWidgets.QWidget):
    # Define a custom signal to notify when the value changes
    valueChangedEvent = QtCore.Signal(float)

    def __init__(self, textWidth=60, sliderWidth=150, devValue=0, minValue=0, maxValue=10, showValueField=True, showMinMaxField=True, stepSize=1, enabled=True):
        super().__init__()

        """
        Variables definition
        """
        self.textWidth = textWidth
        self.sliderWidth = sliderWidth
        self.devValue = devValue
        self.minValue = minValue
        self.maxValue = maxValue
        self.showValueField = showValueField
        self.showMinMaxField = showMinMaxField
        self.stepSize = stepSize
        self.enabled = enabled
        
        """
        UI Creation
        """
        self.createWidgets()
        self.createLayouts()
        self.createConnections()

        houdiniStyle = """
            /* Main Widget Background */
            QWidget {
                color: #dfdfdf;
                font-family: "Segoe UI", Helvetica, Arial, sans-serif;
                font-size: 14px;
            }

            /* Houdini Style SpinBoxes */
            QDoubleSpinBox {
                border: 1px solid #1a1a1a;
                border-radius: 2px;
                padding: 2px 4px;
                selection-background-color: #d18c3b; /* Houdini orange highlight */
            }

            QDoubleSpinBox:focus {
                border: 1px solid #DEAE6F;
            }

            /* Hide the up/down buttons for a cleaner Houdini parameter look */
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 0px; 
                border: none;
            }

            /* Houdini Style Slider */
            QSlider::groove:horizontal {
                border: 1px solid #1a1a1a;
                height: 4px;
                background: #222222;
                border-radius: 2px;
            }

            /* The filled part of the slider */
            QSlider::sub-page:horizontal {
                background: #004A98;
                border-radius: 1px;
            }

            /* The slider handle */
            QSlider::handle:horizontal {
                background: #6b6b6b;
                border: 1px solid #1a1a1a;
                width: 10px;
                margin-top: -13px;
                margin-bottom: -13px;
                border-radius: 2px;
            }

            QSlider::handle:horizontal:hover {
                background: #888888;
            }
        """

        self.setStyleSheet(houdiniStyle)

    def createWidgets(self):
        # Scaling factor to allow fractional precision (not modifiable pre=2)
        self.scaleFactor = 100 
        
        # Scale values to integers
        self.minValueScaled = int(self.minValue * self.scaleFactor)
        self.maxValueScaled = int(self.maxValue * self.scaleFactor)
        self.stepSizeScaled = int(self.stepSize * self.scaleFactor)
        self.devValueScaled = int(self.devValue * self.scaleFactor)

        
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(self.minValueScaled, self.maxValueScaled)
        self.slider.setValue(self.devValueScaled)
        self.slider.setFixedWidth(self.sliderWidth)
        self.slider.setTickInterval(self.stepSizeScaled)
        self.slider.setSingleStep(self.stepSizeScaled)

        # Create QDoubleSpinBox for min and max
        self.minField = QtWidgets.QDoubleSpinBox()
        self.minField.setFixedWidth(self.textWidth)
        self.minField.setValue(self.minValue)
        self.minField.setSingleStep(self.stepSize)

        self.maxField = QtWidgets.QDoubleSpinBox()
        self.maxField.setFixedWidth(self.textWidth)
        self.maxField.setValue(self.maxValue)
        self.maxField.setSingleStep(self.stepSize)

        # Create QDoubleSpinBox for the slider's value
        self.valueField = QtWidgets.QDoubleSpinBox()
        self.valueField.setRange(self.minValue, self.maxValue)
        self.valueField.setFixedWidth(self.textWidth)
        self.valueField.setSingleStep(self.stepSize)
        self.valueField.setValue(self.slider.value() / self.scaleFactor)
        
        self.setEnabled(self.enabled)

    def createLayouts(self):
        mainLayout = QtWidgets.QHBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        if self.showValueField:
            mainLayout.addWidget(self.valueField)
        
        mainLayout.addWidget(self.slider)

        if self.showMinMaxField:
            mainLayout.addWidget(self.minField)
            mainLayout.addWidget(self.maxField)

    def createConnections(self):
        """When values change update the widgets with the functions innit"""
        self.slider.valueChanged.connect(self.__onSliderValueChanged)
        self.minField.valueChanged.connect(self.__setMinSlider)
        self.maxField.valueChanged.connect(self.__setMaxSlider)
        self.valueField.valueChanged.connect(self.__setSliderValue)
    

    def setEnabled(self, enabled):

        self.slider.setEnabled(enabled)
        self.minField.setEnabled(enabled)
        self.maxField.setEnabled(enabled)
        self.valueField.setEnabled(enabled)

    def setMinValue(self, value):
        self.minField.setValue(value)
        self.setMinSlider()
    
    def setMaxValue(self, value):
        self.maxField.setValue(value)
        self.setMaxSlider()
    
    def setValueField(self, value):
        self.valueField.setValue(value)

    def __onSliderValueChanged(self):
        """This function will be called whenever the slider value changes, and will 
            emit a custom signal when the slider value changes"""
        self.valueField.setValue(self.slider.value() / self.scaleFactor)
        self.valueChangedEvent.emit(self.valueField.value())
        #print(f"Slider value changed: {value}")

    def __setMinSlider(self):
        """Update the slider's minimum value based on the input."""
        self.minValueScaled = int(self.minField.value() * self.scaleFactor)

        """If the min value is smaller than max then update it, otherwise revert it"""
        if self.minValueScaled < self.maxValueScaled:
            self.slider.setMinimum(self.minValueScaled)
            self.valueField.setMinimum(self.slider.minimum() / self.scaleFactor)
        else:
            self.minField.setValue(self.slider.minimum() / self.scaleFactor)
        
        # Force UI refresh
        self.slider.update()
        self.slider.repaint()

    def __setMaxSlider(self):
        """Update the slider's maximum value based on the input."""
        self.maxValueScaled = int(self.maxField.value() * self.scaleFactor)

        """If the max value is bigger than min then update it, otherwise revert it"""
        if self.maxValueScaled > self.minValueScaled:
            self.slider.setMaximum(self.maxValueScaled)
            self.valueField.setMaximum(self.slider.maximum() / self.scaleFactor)
        else:
            self.maxField.setValue(self.slider.maximum() / self.scaleFactor)
        
        # Force UI refresh
        self.slider.update()
        self.slider.repaint()

    def __setSliderValue(self):
        """Update the slider's value when the spinbox value changes."""
        self.slider.setValue(int(self.valueField.value() * self.scaleFactor))
    
    def getValue(self):
        return self.slider.value() / self.scaleFactor
    
    def getMinValue(self):
        return self.minField.value()
    
    def getMaxValue(self):
        return self.maxField.value()
    

#endregion



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
        super(ktVeggieImporter, self).__init__(parent)
        
        self.setWindowTitle('kt_VeggieImporter')
        self.setMinimumWidth(600)
        self.setMinimumHeight(800)
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
        self.rootPathTXT = QtWidgets.QLineEdit()
        self.rootPathTXT.setReadOnly(True)
        self.rootPathBTN = hou.qt.NodeChooserButton()
        self.rootPathTXT.setText('/stage')

        self.folderPathTXT = QtWidgets.QLineEdit()
        self.folderPathTXT.setReadOnly(True)
        self.folderPathBTN = hou.qt.FileChooserButton()
        self.folderPathBTN.setFileChooserTitle("Please select a directory")
        self.folderPathBTN.setFileChooserMode(hou.fileChooserMode.Read)
        self.folderPathBTN.setFileChooserFilter(hou.fileType.Directory)

        self.colorBTN = hou.qt.ColorField()
        self.scaleSLD = ktRangeSlider(devValue=1, minValue=0.01, maxValue=2, showMinMaxField=False, showValueField=True, textWidth=50, sliderWidth=150)

        self.mergeCB = QtWidgets.QCheckBox("")
        self.exportUsdBTN = QtWidgets.QPushButton("Export USD")
        self.exportUsdBTN.setFixedHeight(35)

        self.selectAllCB = QtWidgets.QCheckBox()
        self.createBTN = QtWidgets.QPushButton("Create")
        self.createBTN.setEnabled(False)
        self.clearBTN = QtWidgets.QPushButton("Clear")
        self.clearBTN.setFixedWidth(60)
        self.clearBTN.setFixedHeight(35)
        self.clearBTN.setStyleSheet("padding: 0px;")
            
    def createLayouts(self):
        """Function that creates all the layouts and add widgets"""
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        """ Header """
        self.textureTypeLYT = QtWidgets.QHBoxLayout()
        self.textureTypeLYT.addWidget(QtWidgets.QLabel(' Root: '))
        self.textureTypeLYT.addWidget(self.rootPathTXT)
        self.textureTypeLYT.addWidget(self.rootPathBTN)
        

        """ Objects Path """
        self.folderPathLYT = QtWidgets.QHBoxLayout()
        self.folderPathLYT.addWidget(QtWidgets.QLabel('Folder Path: '))
        self.folderPathLYT.addWidget(self.folderPathTXT)
        self.folderPathLYT.addWidget(self.folderPathBTN)


        """ General Settings Path """
        self.generalSetLYT = QtWidgets.QHBoxLayout()
        self.generalSetLYT.addWidget(QtWidgets.QLabel('Size:'))
        self.generalSetLYT.addWidget(self.scaleSLD)
        self.generalSetLYT.addWidget(QtWidgets.QLabel('   Color:'))
        self.generalSetLYT.addWidget(self.colorBTN)
        self.generalSetLYT.addWidget(QtWidgets.QLabel('   Merge:'))
        self.generalSetLYT.addWidget(self.mergeCB)
        self.generalSetLYT.addStretch()


        """ Execution"""
        self.execLYT = QtWidgets.QHBoxLayout()
        self.execLYT.addWidget(self.selectAllCB)
        self.execLYT.addWidget(QtWidgets.QLabel('Select All'))
        self.execLYT.addStretch()
        self.execLYT.addWidget(self.createBTN)
        self.execLYT.addWidget(self.clearBTN)
        self.execLYT.addWidget(self.exportUsdBTN)


        """ OBJECT CONTAINER """
        self.objScroll = QtWidgets.QScrollArea()             # Scroll Area which contains the widgets, set as the centralWidget
        self.objScroll.setFixedHeight(360)
        self.objContainer = QtWidgets.QWidget()                 # Widget that contains the collection of Vertical Box
        self.objLYT = QtWidgets.QVBoxLayout()               # The Vertical Box that contains the Horizontal Boxes of  labels and buttons
        self.objLYT.setContentsMargins(0, 0, 0, 0)
        self.objLYT.setSpacing(0)

        self.objContainer.setLayout(self.objLYT)

        #Scroll Area Properties
        self.objScroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.objScroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.objScroll.setWidgetResizable(True)
        self.objScroll.setWidget(self.objContainer)


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
        self.mainLayout.addWidget(QtWidgets.QLabel(' '))  
        self.mainLayout.addWidget(QtWidgets.QLabel('General Settings'))
        self.mainLayout.addLayout(self.generalSetLYT)
        self.mainLayout.addSpacing(25)
        self.mainLayout.addLayout(self.execLYT)
        self.mainLayout.addWidget(QtWidgets.QLabel('Objects'))
        self.mainLayout.addWidget(self.objScroll)
        self.mainLayout.addWidget(QtWidgets.QLabel('Textures'))
        self.mainLayout.addWidget(self.texScroll)

    def createConnections(self):
        self.folderPathBTN.fileSelected.connect(self.onClick_folderPathBTN)
        self.rootPathBTN.nodeSelected.connect(self.onClick_rootPathBTN)
        self.createBTN.clicked.connect(self.onClick_createBTN)
        self.selectAllCB.clicked.connect(self.onChange_selectAllCB)
        self.exportUsdBTN.clicked.connect(self.onClick_exportUsdBTN)

#region UI

    def onClick_folderPathBTN(self, filePath):
        if filePath:
            self.folderPathTXT.setText(filePath)
            if self.folderPathTXT.text():

                self.clearLayout(self.objLYT)
                self.clearLayout(self.texLYT)

                self.loadObjects()
                self.loadTextures()
                

    def onClick_rootPathBTN(self, node):
        if node:
            self.rootPathTXT.setText(str(node.path()))


    def onClick_createBTN(self):
        parentNode = hou.node(self.rootPathTXT.text())
        scale = self.scaleSLD.getValue()
        colorWidget = self.colorBTN.color()
        r, g, b, a = colorWidget.getRgbF()
        color = hou.Color((r, g, b))
        
        if parentNode:
            folderPath = self.folderPathTXT.text() 

            if self.objList:
                if self.mergeCB.isChecked():
                    # Create merge node
                    mergeNode = parentNode.createNode('merge')

                for objItem in self.objList:
                    if objItem.selectedCB.isChecked():
                        objItem.obj.createComponent(parentNode, folderPath, scale, color)
                        materialNode = objItem.obj.materialLibrary
                        if materialNode:
                            if self.texList:
                                for tex in self.texList:
                                    #tex = ktTextureWidget() # type: ktTextureWidget
                                    if tex.selectedCB.isChecked():
                                        tex.texture.createTexture(materialNode, folderPath)
                                materialNode.layoutChildren()
                                objItem.obj.connectTextures()
                        if self.mergeCB.isChecked():
                            #connect to merge node
                            outputNode = objItem.obj.compOutNode
                            mergeNode.setNextInput(outputNode)
                            

                parentNode.layoutChildren()

                

            else:
                self.showMessageError("No object has been selected to create")
        else:
            self.showMessageError("A material Library needs to be selected")

    def onChange_selectAllCB(self):
        """
        Toggles the selection state of all texture checkboxes.

        If checked, all textures in the list are selected for import.
        """
        checkValue = self.selectAllCB.isChecked()

        if self.objList:
            self.checkAllTextures(checkValue)
        
        if self.texList:
            self.checkAllObjects(checkValue)

    def onClick_exportUsdBTN(self):

        exported = self.exportComponentUSD()

        if exported:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("Export complete.")
            msg.setWindowTitle("Export Status")
            msg.exec_()
        else:
            self.showMessageError("Export couldn't process.")

    
    def clearLayout(self, layout):
        """
        Clears all widgets and items from a given layout.

        Args:
            layout (QLayout): The layout to be cleared.
        """
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

#region Objects

    def checkAllObjects(self, checkValue):
        """
        Selects or deselects all texture checkboxes based on the "Select All" state.
        """
        if self.objList:
            for objectWD in self.objList:
                objectWD.selectedCB.setChecked(checkValue)

    def loadObjects(self):
        self.objList = []
        folderPath = self.folderPathTXT.text()

        objects = self.readObjectsFromFolder(folderPath)

        if objects:
            self.createBTN.setEnabled(True)
            # Display texture information
            #for obj in objects:
            for obj in objects.values():
                attributes = {key: value for key, value in vars(obj).items() if key != "fieldMapping"}
                newObject = ComponentMesh(**attributes)
                
                objectWD = ktObjectWidget(obj=newObject, mainPath=folderPath)
                self.objLYT.addWidget(objectWD)
                self.objList.append(objectWD)

            self.objLYT.addStretch()
        else:
            self.createBTN.setEnabled(False)
            # Show a message on the screen saying there's no results
            lbl = QtWidgets.QLabel("No results.")
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet("background-color: #995D58; color: white; padding: 10px; font-weight: bold;")
            self.objLYT.addWidget(lbl)

    def readObjectsFromFolder(self, folderPath, objectClass=ComponentMesh):
        objects = {}
        folderPath = self.verifyFolderPath(folderPath)

        try:
            # Loop through files in the directory
            for root, dirs, files in os.walk(folderPath):
                for filename in files:
                    if filename.endswith((".abc")):  # Filter by file type

                        # 1. Get the new name
                        parts = filename.split('.')
                        finalName = parts[0]
                        # 2. Save the name in the objects list
                        
                        if finalName not in objects:
                                objects[finalName] = objectClass(name=finalName, mainPath=folderPath) 
                        #objects.append(filename)

                        # 3. Save the filepath in the list
                        relativePath = os.path.relpath(root, folderPath)
                        relativePath = relativePath.replace("\\", "/")

                        if relativePath != ".":
                            finalPath = relativePath + "/" + filename
                        else:
                            finalPath = filename

                        setattr(objects[finalName], 'mainPath', folderPath) 
                        setattr(objects[finalName], 'file', finalPath) 


        except OSError as e:
            self.showMessageError(f"Error reading directory: {e}")
        
        return objects
    
#endregion

#region Textures

    def checkAllTextures(self, checkValue):
        """
        Selects or deselects all texture checkboxes based on the "Select All" state.
        """
        if self.texList:
            for textureWD in self.texList:
                textureWD.selectedCB.setChecked(checkValue)

    def loadTextures(self):
        """
        Loads textures from the selected folder based on the current pattern.

        Uses regex matching to filter textures and displays matching results 
        in the UI.
        """
        #self.clearLayout(self.texLYT)
        self.texList = []

        folderPath = self.folderPathTXT.text()
        regexPattern = r'^(?P<texName>[A-Za-z0-9]+)(?:_(?P<texType>[A-Za-z]+))?(\.[a-z0-9]+)$'
        textureType = "KarmaTexture"
        textureClass = globals().get(textureType)

        textures = self.readTexturesFromFolder(folderPath, regexPattern, textureClass)

        if textures:
            self.createBTN.setEnabled(True)
            # Display texture information
            for texture in textures.values():
                #texture = Texture() # type: Texture
                #texture.showInformation()
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
        """
        Reads and organizes textures from a specified folder.

        Iterates through files in the given directory, applies regex matching 
        to extract texture information, and maps them to texture attributes.

        Args:
            folderPath (str): The directory containing texture files.
            regexPattern (str): The regex pattern to match filenames.
            textureClass (type): The texture class used to instantiate textures.

        Returns:
            dict: A dictionary of texture objects mapped by texture names.
        """
        textures = {}
        folderPath = self.verifyFolderPath(folderPath)

        try:
            # Loop through files in the directory
            for root, dirs, files in os.walk(folderPath):
                ignoreFolders = {"usd", "temp", "cache","export"}
                dirs[:] = [d for d in dirs if d.lower() not in ignoreFolders]


                for filename in files:
                    if filename.endswith((".exr", ".png", ".jpg")):  # Filter by file type
                        match = re.match(regexPattern, filename)
                        if match:
                            texName = match.group('texName')
                            textureType = match.group("texType") if match.group("texType") else 'albedo'

                            finalName = texName
                            finalName = finalName.replace(' ', '_') # FIX: Spaces could create problem when searching a node

                            # Create texture object if not exists
                            if finalName not in textures:
                                textures[finalName] = textureClass(name=finalName) 
                                #print(f"Created {textures[finalName].__class__.__name__} object: {finalName}")  # Debugging output

                            textureType = textureType.lower()
                            textureParent = textures[finalName].getTypeFromAttr("mapping", textureType)

                            # Check if the textureType exists in the mapping dictionary
                            if textureParent:
                                relativePath = os.path.relpath(root, folderPath)
                                relativePath = relativePath.replace("\\", "/")

                                if relativePath != ".":
                                    finalPath = relativePath + "/" + filename
                                else:
                                    finalPath = filename                            
                                setattr(textures[finalName], textureParent, finalPath)
        except OSError as e:
            self.showMessageError(f"Error reading directory: {e}")
        
        return textures

#endregion 

#region Utils

    def showMessageError(self, message):
        """
        Displays an error message dialog.

        Args:
            message (str): The error message to display.
        """
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText("Error: " + message)
        msg.setWindowTitle("Houdini Error")
        msg.exec_()

    def verifyFolderPath(self, folderPath):
        """
        Resolves environment variable prefixes in a folder path.

        If the folder path contains Houdini environment variables ($HOME, $HIP, $JOB),
        this function replaces them with their corresponding values. Otherwise, it 
        returns the original path.

        Args:
            folderPath (str): The folder path, potentially containing Houdini variables.

        Returns:
            str: The resolved absolute folder path.
        """
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
    

    def exportComponentUSD(self):
        '''
        node = hou.node('/stage/Dead_Common_Bush_01')
        node.parm("execute").pressButton()
        '''

        def getAllNodes(node, nodeList = None, level = 0):
            if nodeList is None:
                nodeList = []
            #print(" " * level + node.name())
            nodeList.append(node.path())

            for child in node.children():
                getAllNodes(child, nodeList, level + 1)

            return nodeList


        parentNode = hou.node(self.rootPathTXT.text())
        nodeList = getAllNodes(parentNode)

        if nodeList:
        
            # 'componentoutput'
            for node in nodeList:
                tempNode = hou.node(node)
                nodeType = tempNode.type().name()
                if nodeType == 'componentoutput':
                    tempNode.parm("execute").pressButton()
            return True
        
        else:
            return False

        
#endregion



#endregion


try:
    ktVeggieImporter.close()
    ktVeggieImporter.deleteLater()
except:
    pass

ktVeggieImporter = ktVeggieImporter()
ktVeggieImporter.show()