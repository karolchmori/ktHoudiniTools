
import hou

def fooText():
    print("This is a text")


def createGroups(kwargs):
    hda = kwargs['node']

    startPosition = hda.node('BEFORE_GROUPS')
    mergeNode = hda.node('merge_GROUPS')
    amountInstances = hda.parm('groupList').eval()

    # 2. Create and wire new nodes
    for i in range(1, amountInstances + 1):
        name = f'group{i}'

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
        
        

        print(f'Group {i}')
    
    hda.layoutChildren()