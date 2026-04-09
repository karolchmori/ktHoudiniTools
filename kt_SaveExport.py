import hou

def getAllNodes(node, nodeList = None, level = 0):
    if nodeList is None:
        nodeList = []
    #print(" " * level + node.name())
    nodeList.append(node.path())

    for child in node.children():
        getAllNodes(child, nodeList, level + 1)

    return nodeList

def exportComponentUSD():
    '''
    node = hou.node('/stage/Dead_Common_Bush_01')
    node.parm("execute").pressButton()
    '''

    nodeRoot = hou.node('/stage')
    nodeList = getAllNodes(nodeRoot)

    
    # 'componentoutput'
    for node in nodeList:
        tempNode = hou.node(node)
        nodeType = tempNode.type().name()
        if nodeType == 'componentoutput':
            tempNode.parm("execute").pressButton()
            #print(tempNode)


exportComponentUSD()