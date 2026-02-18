
import hou

def fooText():
    print("This is a text")


def createGroups(kwargs):
    hda = kwargs['node']

    startPosition = hda.node('BEFORE_GROUPS')
    mergeNode = hda.node('merge_GROUPS')
    amountInstances = hda.parm('groupList').eval()

    # 1. Clean up old nodes before creating new ones
    for child in hda.children():
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
            groupNode = hda.node(name)
            
            # If it doesn't exist then create it and wire it
            if not groupNode:
                groupNode = hda.createNode('groupcreate', name)
            
            
            # Wire Input: Connect to the 'BEFORE_GROUPS' null
            groupNode.setInput(0, startPosition)
            mergeNode.setInput(i-1, groupNode)
            
            # Relink data
            groupNode.parm('groupname').setExpression(f'chs("../groupName_{i}")')
            groupNode.parm('grouptype').setExpression(f'ch("../groupType_{i}")')
            groupNode.parm('basegroup').setExpression(f'chs("../groupBase_{i}")')
            groupNode.parm('geotype').setExpression(f'ch("../groupGeoType_{i}")')
            groupNode.parm('ordered').setExpression(f'ch("../groupGeoOrdered_{i}")')
            
            

            #print(f'Group {i}')
        
    hda.layoutChildren()
