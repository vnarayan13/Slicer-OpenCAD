from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import vtk.util.numpy_support
from vtk import vtkShortArray, vtkDoubleArray


class SegmentCADLogic:
  # Logic for SegmentCAD divided into sequential functions with helper functions at the bottom
  def __init__(self, SegmentCAD, nodePre, node1, node4):
    self.SegmentCADLabelMap = SegmentCAD
    self.volumePre = nodePre
    self.volume1 = node1
    self.volume4 = node4
    self.ROIOn = False
    
    self.minimumThreshold = 0.75
    self.curve1Minimum = 0.2
    self.curve3Maximum = -0.2
        
  def initializeNodeArrays (self):
    # Computes percentage increase from baseline (pre-contrast) at each voxel for each volume as numpy arrays.
    # Initializes a numpy array of zeroes as numpy.int16 vtkShortArray for the SegmentCAD label map output.
    
    # Convert volumes into arrays of of intensity values
    self.nodeArrayPre = self.createNumpyArray (self.volumePre)
    self.nodeArray1 = self.createNumpyArray (self.volume1)
    self.nodeArray4 = self.createNumpyArray (self.volume4)
    
    # Initial Rise at each voxel (percentage increase from pre-contrast to first post-contrast)
    self.nodeArrayInitialRise = ((self.nodeArray1).__truediv__(self.nodeArrayPre+1.0))-1.0
    # Compute slope at each voxel from first to fourth volume to determine curve type
    self.slopeArray1_4 = (self.nodeArray4 - self.nodeArray1).__truediv__(self.nodeArray1)
    # Initialize SegmentCAD label map as numpy array
    shape = self.nodeArrayPre.shape
    self.nodeArraySegmentCADLabel = numpy.zeros(shape, dtype=numpy.int16)
    
  def arrayProcessing(self):
    # Iterates through ROI coordinates and checks for initial rise percentage > minimum threshold
    # If no ROI is provided, iterates through array of initial rise percentages with same shape as input volumes
    # Determine if delayed curve is of type 1, 2, or 3 and assigns corresponding label color via colorAssign()

    if self.ROIOn:
      numberCoordinates = self.arrayLabelMapROICoordinates.shape[0]
      for i in xrange (numberCoordinates):
        index = tuple(self.arrayLabelMapROICoordinates[i])
        if ((self.nodeArrayInitialRise[index] > self.minimumThreshold) and (self.nodeArrayPre[index] > 100)):
          self.colorAssign(self.slopeArray1_4[index], index)
    else:
      for ind, x in numpy.ndenumerate(self.nodeArrayInitialRise):
        if ((x > self.minimumThreshold) and (self.nodeArrayPre[ind] > 100)):
          self.colorAssign(self.slopeArray1_4[ind], ind)
    
  def renderLabelMap(self):
    # Initializes a vtkMRMLScalarVolumeNode for the SegmentCAD Output and copies ijkToRAS matrix and Image data from nodeLabel
    ijkToRASMatrix = vtk.vtkMatrix4x4()
    self.volumePre.GetIJKToRASMatrix(ijkToRASMatrix)
    self.SegmentCADLabelMap.SetIJKToRASMatrix(ijkToRASMatrix)
    SegmentCADLabelMapImageData = vtk.vtkImageData()
    SegmentCADLabelMapImageData.DeepCopy(self.volumePre.GetImageData())
    SegmentCADLabelMapPointData = SegmentCADLabelMapImageData.GetPointData()
    # Numpy array is converted from signed int16 to signed vtkShortArray
    scalarArray = vtk.vtkShortArray()
    dims1D = SegmentCADLabelMapPointData.GetScalars().GetSize()
    self.nodeArraySegmentCADLabel = self.nodeArraySegmentCADLabel.reshape(dims1D, order='C')
    scalarArray = vtk.util.numpy_support.numpy_to_vtk(self.nodeArraySegmentCADLabel)
    # PointData() of SegmentCAD label output pointed to new vtkShortArray for scalar values
    SegmentCADLabelMapImageData.SetScalarTypeToShort()
    SegmentCADLabelMapPointData.SetScalars(scalarArray)
    SegmentCADLabelMapPointData.Update()
    SegmentCADLabelMapImageData.Update()
    self.SegmentCADLabelMap.SetAndObserveImageData(SegmentCADLabelMapImageData)
    # Corresponding display node and color table nodes created for SegmentCAD label Output
    self.SegmentCADLabelMapDisplay = slicer.vtkMRMLLabelMapVolumeDisplayNode()
    self.SegmentCADLabelMapDisplay.SetScene(slicer.mrmlScene)
    self.SegmentCADLabelMapDisplay.SetAndObserveColorNodeID('vtkMRMLColorTableNodeFileGenericColors.txt')
    self.SegmentCADLabelMapDisplay.SetInputImageData(SegmentCADLabelMapImageData)
    self.SegmentCADLabelMapDisplay.UpdateImageDataPipeline()
    
    slicer.mrmlScene.AddNode(self.SegmentCADLabelMapDisplay)
    self.SegmentCADLabelMap.SetAndObserveDisplayNodeID(self.SegmentCADLabelMapDisplay.GetID())
    self.SegmentCADLabelMapDisplay.UpdateScene(slicer.mrmlScene)
    
  def renderVolume(self):
    volumeRenderingLogic = slicer.modules.volumerendering.logic()
    SegmentCADVolumeRenderingDisplay = volumeRenderingLogic.CreateVolumeRenderingDisplayNode()
    slicer.mrmlScene.AddNode(SegmentCADVolumeRenderingDisplay)
    SegmentCADVolumeRenderingDisplay.UnRegister(volumeRenderingLogic)
    volumeRenderingLogic.UpdateDisplayNodeFromVolumeNode(SegmentCADVolumeRenderingDisplay, self.SegmentCADLabelMap)
    self.SegmentCADLabelMap.AddAndObserveDisplayNodeID(SegmentCADVolumeRenderingDisplay.GetID())
    
    cameraNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLCameraNode')
    activeCamera = (slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLCameraNode')-1)
    activeCameraNode = cameraNodes.GetItemAsObject(activeCamera)
    camera = activeCameraNode.GetCamera()
    camera.SetPosition(0, 0, -600)
    camera.SetViewUp(0, 1, 0)
    
  def setAdvancedParameters(self, minimumThreshold=0.75, curve1Minimum=0.2, curve3Maximum=-0.2):
    self.minimumThreshold = minimumThreshold
    self.curve1Minimum = curve1Minimum
    self.curve3Maximum = curve3Maximum
    
  def setLabelROI (self, nodeLabel):
    self.ROIOn = True
    self.nodeArrayLabelMapROI = self.createNumpyArray(nodeLabel)
    self.arrayLabelMapROICoordinates = numpy.transpose(numpy.where(self.nodeArrayLabelMapROI != 0))
    
  def colorAssign(self, slope, index):
    # Values assigned based on a ColorTableNode
    if (slope > self.curve1Minimum):
      # blue (slope of curve1 min = 0.2(default), Persistent Slope)
      self.nodeArraySegmentCADLabel[index] = 306
    elif (slope < self.curve3Maximum):
      # red (slope of curve3 max = -0.2(default), Washout Slope )
      self.nodeArraySegmentCADLabel[index] = 32
    else:
      # yellow (Plateau Slope)
      self.nodeArraySegmentCADLabel[index] = 291
    
  def createNumpyArray (self, node):
    # Generate Numpy Array from vtkMRMLScalarVolumeNode
    imageData = vtk.vtkImageData()
    imageData = node.GetImageData()
    shapeData = list(imageData.GetDimensions())
    return (vtk.util.numpy_support.vtk_to_numpy(imageData.GetPointData().GetScalars()).reshape(shapeData))
   
