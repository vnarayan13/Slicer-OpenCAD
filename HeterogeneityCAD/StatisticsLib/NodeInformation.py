from __main__ import vtk, qt, ctk, slicer
import string
import numpy

class NodeInformation:

  def __init__(self, dataNode, labelNode, allKeys):
    
    self.dataNode = dataNode
    self.labelNode = labelNode
    self.allKeys = allKeys
    
    self.nodeInformation = {}
    self.nodeInformation["Node"] = "self.nodeName(self.dataNode)"
     
  def EvaluateFeatures(self):   
    keys = set(self.allKeys).intersection(self.nodeInformation.keys())
    if not keys:
      return(self.nodeInformation)
    
    #Evaluate dictionary elements corresponding to user selected keys
    for key in keys:
      self.nodeInformation[key] = eval(self.nodeInformation[key])
    return(self.nodeInformation)
       
  def nodeName (self, node):
    return (node.GetName())
