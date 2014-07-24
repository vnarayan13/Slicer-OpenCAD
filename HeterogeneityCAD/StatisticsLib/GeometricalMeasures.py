from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import math
import operator

class GeometricalMeasures:
  
  def __init__(self, labelNode, matrix, matrixCoordinates, parameterValues, allKeys):
    #manually pad extrudedMatrix +1 in all directions in 4 dimensions
    #nonlinear mapping of surface heights for normalization
    self.labelNode = labelNode
    self.matrix = matrix
    self.matrixCoordinates = matrixCoordinates
    self.parameterValues = parameterValues
    self.allKeys = allKeys
       
    self.GeometricalMeasures = {}
    self.GeometricalMeasures["Extruded Surface Area"] = "self.extrudedSurfaceArea(self.labelNode, self.extrudedMatrix, self.extrudedMatrixCoordinates, self.parameterValues)"
    self.GeometricalMeasures["Extruded Volume"] = "self.extrudedVolume(self.extrudedMatrix, self.extrudedMatrixCoordinates, cubicMMPerVoxel)"
    self.GeometricalMeasures["Extruded Surface:Volume Ratio"] = "self.extrudedSurfaceVolumeRatio(self.labelNode, self.extrudedMatrix, self.extrudedMatrixCoordinates, self.parameterValues, cubicMMPerVoxel)"
         
  def EvaluateFeatures(self):
    keys = set(self.allKeys).intersection(self.GeometricalMeasures.keys())
    if not keys:
      return(self.GeometricalMeasures)
    
    cubicMMPerVoxel = reduce(lambda x,y: x*y, self.labelNode.GetSpacing())
    
    extrudedShape = self.matrix.shape + (numpy.max(self.parameterValues),)
    extrudedShapePad = tuple(map(operator.add, extrudedShape, [2,2,2,2])) #to pad shape by 1 unit in all 8 directions
    self.extrudedMatrix = numpy.zeros(extrudedShapePad)   
    self.extrudedMatrixCoordinates = tuple(map(operator.add, self.matrixCoordinates, ([1,1,1]))) + (numpy.array([slice(1,value+1) for value in self.parameterValues]),)   
    for slice4D in zip(*self.extrudedMatrixCoordinates):
      self.extrudedMatrix[slice4D] = 1
    
    #Evaluate dictionary elements corresponding to user selected keys    
    for key in keys:
      self.GeometricalMeasures[key] = eval(self.GeometricalMeasures[key])
    return(self.GeometricalMeasures)    
    
  def extrudedSurfaceArea(self, labelNode, a, extrudedMatrixCoordinates, parameterValues):
    x, y, z = labelNode.GetSpacing()
       
    # surface area of different connections
    xz = x*z
    yz = y*z
    xy = x*y
    fourD = (2*xy + 2*xz + 2*yz)
    
    voxelTotalSA = (2*xy + 2*xz + 2*yz)
    totalSA = parameterValues.size * voxelTotalSA
    totalDimensionalSurfaceArea = (2*xy + 2*xz + 2*yz + 2*fourD)
    
    # in matrixSACoordinates
    # i corresponds to height (z)
    # j corresponds to vertical (y)
    # k corresponds to horizontal (x)
    # l corresponds to 4D
    
    i, j, k, l = 0, 0, 0, 0
    extrudedSurfaceArea = 0
    
    # remove loop
    for i,j,k,l_slice in zip(*extrudedMatrixCoordinates):
      for l in xrange(l_slice.start, l_slice.stop):
        fxy = numpy.array([ a[i+1,j,k,l], a[i-1,j,k,l] ]) == 0
        fyz = numpy.array([ a[i,j+1,k,l], a[i,j-1,k,l] ]) == 0
        fxz = numpy.array([ a[i,j,k+1,l], a[i,j,k-1,l] ]) == 0  
        f4d = numpy.array([ a[i,j,k,l+1], a[i,j,k,l-1] ]) == 0
               
        extrudedElementSurface = (numpy.sum(fxz) * xz) + (numpy.sum(fyz) * yz) + (numpy.sum(fxy) * xy) + (numpy.sum(f4d) * fourD)     
        extrudedSurfaceArea += extrudedElementSurface
    return (extrudedSurfaceArea)
  
  def extrudedVolume(self, extrudedMatrix, extrudedMatrixCoordinates, cubicMMPerVoxel):
    extrudedElementsSize = extrudedMatrix[numpy.where(extrudedMatrix == 1)].size
    return(extrudedElementsSize * cubicMMPerVoxel)
      
  def extrudedSurfaceVolumeRatio(self, labelNode, extrudedMatrix, extrudedMatrixCoordinates, parameterValues, cubicMMPerVoxel):
    extrudedSurfaceArea = self.extrudedSurfaceArea(labelNode, extrudedMatrix, extrudedMatrixCoordinates, parameterValues)
    extrudedVolume = self.extrudedVolume(extrudedMatrix, extrudedMatrixCoordinates, cubicMMPerVoxel)
    return(extrudedSurfaceArea/extrudedVolume)
