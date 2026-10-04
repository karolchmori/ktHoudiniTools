
import hou
import os
import re
import voptoolutils

def importCardStage(kwargs):
    hda = kwargs['node']

    # Get values
    cardsName = hda.parm("cardsName").eval()
    matShape = hda.parm("matShape") #Links the parm value itself instead of the filepath
    matInvert = hda.parm("matInvert")
    sopPath = hda.node("OUT_CARDS").path()


    # Lauch Import
    root = hda.node('/stage')
    
    folderParent = root.createNode('subnet', cardsName)

    for child in folderParent.children():
            if child.name().startswith('output0') and child.type().name() == 'output':
                output = child
    

    sopImport = folderParent.createNode('sopimport', cardsName)
    sopImport.parm("soppath").set(sopPath)
    

    materialLibrary = folderParent.createNode('materiallibrary', f'{cardsName}_ML')
    createMaterial(materialLibrary, cardsName, matInvert, matShape)
    materialLibrary.parm("matnode1").set(f'{cardsName}_MAT')
    materialLibrary.parm("matpath1").set(f'{cardsName}_MAT')
    materialLibrary.parm("assign1").set(1)
    materialLibrary.parm("geopath1").set(f'%type:Boundable')

    materialLibrary.setInput(0, sopImport)

    renderGeo = folderParent.createNode('rendergeometrysettings', f'{cardsName}_RGS')

    renderGeo.setInput(0, materialLibrary)

    output.setInput(0, renderGeo)

    folderParent.layoutChildren()


def createMaterial(parentNode, name, invertValue, opacity=None,):
    imageType = "mtlximage"


    mask = voptoolutils.KARMAMTLX_TAB_MASK #voptoolutils._setupMtlXBuilderSubnet(subnet_node=subnet_node, destination_node=dst_node, name=name, mask=mask, folder_label=folder_label, render_context=render_context)
    
    materialBuilderNode = parentNode.createNode("subnet", f"{name}_MAT")
    voptoolutils._setupMtlXBuilderSubnet(materialBuilderNode, "karmamaterial", "karmamaterial", mask, "Karma Material Builder", "kma")

    standardSurfaceNode = materialBuilderNode.node("mtlxstandard_surface")

    outMaterialNode = materialBuilderNode.node("Material_Outputs_and_AOVs")
    outDisplacement = materialBuilderNode.node("mtlxdisplacement") 

    baseColorNode = materialBuilderNode.createNode("mtlxgeompropvalue", f"{name}_GPV")
    baseColorNode.parm("signature").set("color3")
    baseColorNode.parm("geomprop").set("displayColor")
    standardSurfaceNode.setNamedInput("base_color", baseColorNode, "out")


    if opacity:
        opacityNode = materialBuilderNode.createNode(imageType, f"{name}_OP")
        opacityNode.parm("file").set(opacity)
        opacityNode.parm("signature").set("default")

        invertNode = materialBuilderNode.createNode("mtlxinvert", f"{name}_INV")
        invertNode.parm("amount").set(invertValue)
        invertNode.setNamedInput("in", opacityNode, "out")

        standardSurfaceNode.setNamedInput("opacity", invertNode, "out")


    materialBuilderNode.layoutChildren()
