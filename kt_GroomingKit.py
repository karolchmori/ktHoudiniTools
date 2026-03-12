
import hou
import toolutils

def fooText():
    print("This is a text")



def createMasks(kwargs):
    hda = kwargs['node']
    root = hda.node('HDA_IN_GEO/HDA_MASKS')
    startPositionA = root.node('BEFORE_MASK_BODY')
    startPositionB = root.node('BEFORE_MASK_SUBD')
    mergeNodeA = root.node('merge_MASKS_BODY')
    mergeNodeB = root.node('merge_MASKS_SUBD')
    amountInstances = hda.parm('maskList').eval()

    

    # 1. Clean up old nodes before creating new ones
    for child in root.children():
        if child.name().startswith('HDA_mask') and child.type().name() == 'attribpaint':
            child.destroy()

    # 2. Clean up connections between BEFORE_GROUPS and merge_GROUPS
    for m in [mergeNodeA, mergeNodeB]:
        for i in range(0, len(m.inputs())):
            m.setInput(i, None)

    #for i in range(0, len(mergeNodeA.inputs())):
        
    #    mergeNodeA.setInput(i, None)


    # 2. Always connect the base geometry to the first input (Index 0)
    #mergeNodeA.setInput(0, startPositionA)
    #mergeNodeB.setInput(0, startPositionB)

    # Counters for subsequent inputs (starting at 1)
    countA = 0
    countB = 0

    # 3. Create and wire new nodes
    for i in range(1, amountInstances + 1):
        name = f'HDA_mask{i}'

        # Check if the node exists
        maskNode = root.node(name)
        
        # If it doesn't exist then create it and wire it
        if not maskNode:
            maskNode = root.createNode('attribpaint', name)
        
        # Wire Input: Connect to the 'BEFORE_GROUPS' null
        choice = hda.parm(f'maskBase_{i}').eval()

        if choice == 0:
            maskNode.setInput(0, startPositionA)
            mergeNodeA.setInput(countA, maskNode)
            countA += 1
        else:
            maskNode.setInput(0, startPositionB)
            mergeNodeB.setInput(countB, maskNode)
            countB += 1

        
        # Relink data
        maskNode.parm('attribname1').setExpression(f'chs("../../../maskName_{i}")')
        maskNode.parm('attribtype1').setExpression(f'ch("../../../maskType_{i}")')
        maskNode.parm('attribreset1').setExpression(f'ch("../../../maskReset_{i}")')
        maskNode.parm('stroke_shape').setExpression(f'ch("../../../maskStrokeShape_{i}")')
        maskNode.parm('fgfloat').setExpression(f'ch("../../../maskFG_{i}")')
        maskNode.parm('bgfloat').setExpression(f'ch("../../../maskBG_{i}")')
        maskNode.parm('stroke_radius').setExpression(f'ch("../../../maskStrokeRadius_{i}")')
        maskNode.parm('stroke_opacitypressure').setExpression(f'ch("../../../maskStrokeOpacityPressure_{i}")')
        maskNode.parm('stroke_radiuspressure').setExpression(f'ch("../../../maskStrokeRadiusPressure_{i}")')

        maskNode.parm('domirror').setExpression(f'ch("../../../maskMirror_{i}")')
        maskNode.parm('mirror_tx').setExpression(f'ch("../../../maskMirrorOri_{i}x")')
        maskNode.parm('mirror_ty').setExpression(f'ch("../../../maskMirrorOri_{i}y")')
        maskNode.parm('mirror_tz').setExpression(f'ch("../../../maskMirrorOri_{i}z")')
        maskNode.parm('mirror_dirx').setExpression(f'ch("../../../maskMirrorDir_{i}x")')
        maskNode.parm('mirror_diry').setExpression(f'ch("../../../maskMirrorDir_{i}y")')
        maskNode.parm('mirror_dirz').setExpression(f'ch("../../../maskMirrorDir_{i}z")')

        maskNode.parm('recachemethod').setExpression(f'ch("../../../maskCacheMethod_{i}")')
        maskNode.parm('recache').setExpression(f'ch("../../../maskCacheStrokes_{i}")')
        maskNode.parm('savecache').setExpression(f'ch("../../../maskCacheSave_{i}")')
        maskNode.parm('livemode').setExpression(f'ch("../../../maskCacheLiveMode_{i}")')
        maskNode.parm('docaching').setExpression(f'ch("../../../maskCacheDo_{i}")')
        maskNode.parm('erasestrokes').setExpression(f'ch("../../../maskStrokeHistoryClear_{i}")')

        maskNode.parm('movestashtofile').setExpression(f'ch("../../../maskStashMoveFile_{i}")')
        maskNode.parm('loadstashfromfile').setExpression(f'ch("../../../maskStashLoadFile_{i}")')
        maskNode.parm('strokegeofile').setExpression(f'chs("../../../maskSnapStroke_{i}")')
        maskNode.parm('bakedgeofile').setExpression(f'chs("../../../maskSnapBakedGeo_{i}")')
  


    if mergeNodeA.input(0) is None:
        mergeNodeA.setInput(0, startPositionA)
        
    if mergeNodeB.input(0) is None:
        mergeNodeB.setInput(0, startPositionB)

    

    root.layoutChildren()        
    



def createGroups(kwargs):
    hda = kwargs['node']
    root = hda.node('HDA_IN_GEO/HDA_GEO')

    print(root)

    startPosition = root.node('BEFORE_GROUPS')
    mergeNode = root.node('merge_GROUPS')
    amountInstances = hda.parm('groupList').eval()

    # 1. Clean up old nodes before creating new ones
    for child in root.children():
        if child.name().startswith('HDA_group') and child.type().name() == 'groupcreate':
            child.destroy()


    # 2. Clean up connections between BEFORE_GROUPS and merge_GROUPS
    for i in range(1, len(mergeNode.inputs())):
        mergeNode.setInput(i, None)

    # 2. Depending on the amount of Instances we'll clean up or recreate
    if amountInstances == 0:
        # Reconnect BEFORE_GROUPS directly to merge_GROUPS
        mergeNode.setInput(0, startPosition)

    else:

        # 3. Create and wire new nodes
        for i in range(1, amountInstances + 1):
            name = f'HDA_group{i}'

            # Check if the node exists
            groupNode = root.node(name)
            
            # If it doesn't exist then create it and wire it
            if not groupNode:
                groupNode = root.createNode('groupcreate', name)
            
            
            # Wire Input: Connect to the 'BEFORE_GROUPS' null
            groupNode.setInput(0, startPosition)
            mergeNode.setInput(i-1, groupNode)
            
            # Relink data
            groupNode.parm('groupname').setExpression(f'chs("../../../groupName_{i}")')
            groupNode.parm('grouptype').setExpression(f'ch("../../../groupType_{i}")')
            groupNode.parm('basegroup').setExpression(f'chs("../../../groupBase_{i}")')
            groupNode.parm('geotype').setExpression(f'ch("../../../groupGeoType_{i}")')
            groupNode.parm('ordered').setExpression(f'ch("../../../groupGeoOrdered_{i}")')
            
            

            #print(f'Group {i}')
        
    root.layoutChildren()



def paintMask(kwargs):
    hda = kwargs['node']
    idx = kwargs.get('script_multiparm_index', 1)

    paint_node = hda.node(f'HDA_IN_GEO/HDA_MASKS/HDA_mask{idx}')

    
    if paint_node:
        # Force Houdini to focus on the internal paint node
        paint_node.setSelected(True, clear_all_selected=True)
        paint_node.setDisplayFlag(True)
