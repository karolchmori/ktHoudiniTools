
import hou

def fooText():
    print("This is a text")



def createMasks(kwargs):
    hda = kwargs['node']
    root = hda.node('HDA_MASKS')
    startPositionA = root.node('BEFORE_MASK_BODY')
    startPositionB = root.node('BEFORE_MASK_SUBD')
    mergeNodeA = root.node('merge_MASKS_BODY')
    mergeNodeB = root.node('merge_MASKS_SUBD')
    amountInstances = hda.parm('maskList').eval()

    amountA = 0
    amountB = 0

    # 1. Clean up old nodes before creating new ones
    for child in root.children():
        if child.name().startswith('HDA_mask') and child.type().name() == 'attribpaint':
            child.destroy()

    # 2. Clean up connections between BEFORE_GROUPS and merge_GROUPS
    for i in range(1, len(mergeNodeA.inputs())):
        mergeNodeA.setInput(i, None)

    
    for i in range(1, len(mergeNodeB.inputs())):
        mergeNodeB.setInput(i, None)



    # 2. Depending on the amount of Instances we'll clean up or recreate
    if amountInstances == 0:
        # Reconnect BEFORE_GROUPS directly to merge_GROUPS
        mergeNodeA.setInput(0, startPositionA)
        mergeNodeB.setInput(0, startPositionB)

    else:

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
                mergeNodeA.setInput(amountA, maskNode)
                amountA = amountA + 1
            else:
                maskNode.setInput(0, startPositionB)
                mergeNodeB.setInput(amountB, maskNode)
                amountB = amountB + 1

            
            # Relink data
            maskNode.parm(f'attribname1').setExpression(f'chs("../../maskName_{i}")')
            maskNode.parm('stroke_shape').setExpression(f'chs("../../maskStrokeShape_{i}")')
            maskNode.parm('fgfloat').setExpression(f'ch("../../maskFG_{i}")')
            maskNode.parm('bgfloat').setExpression(f'chs("../../maskBG_{i}")')
            maskNode.parm('stroke_radius').setExpression(f'ch("../../maskStrokeRadius_{i}")')
            maskNode.parm('stroke_opacitypressure').setExpression(f'ch("../../maskStrokeOpacityPressure_{i}")')
            maskNode.parm('stroke_radiuspressure').setExpression(f'ch("../../maskStrokeRadiusPressure_{i}")')
            
            
    root.layoutChildren()        
    



def createGroups(kwargs):
    hda = kwargs['node']
    root = hda.node('HDA_GEO')

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
            groupNode.parm('groupname').setExpression(f'chs("../../groupName_{i}")')
            groupNode.parm('grouptype').setExpression(f'ch("../../groupType_{i}")')
            groupNode.parm('basegroup').setExpression(f'chs("../../groupBase_{i}")')
            groupNode.parm('geotype').setExpression(f'ch("../../groupGeoType_{i}")')
            groupNode.parm('ordered').setExpression(f'ch("../../groupGeoOrdered_{i}")')
            
            

            #print(f'Group {i}')
        
    root.layoutChildren()
