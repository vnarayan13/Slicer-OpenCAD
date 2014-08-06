from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import vtk.util.numpy_support
from vtk import vtkShortArray, vtkDoubleArray

class SegmentCADLogic:
  # Logic for SegmentCAD divided into sequential functions with helper functions at the bottom
  def __init__(self, SegmentCAD):
    self.SegmentCADLabelMap = SegmentCAD
    self.ROIOn = False
    
    self.minimumThreshold = 0.75
    self.curve1Minimum = 0.2
    self.curve3Maximum = -0.2
  
  
  def setInputMultiVolumeNode(self, multiVolumeNode):
    self.multiVolumeNode = multiVolumeNode
    self.nodePre = slicer.vtkMRMLScalarVolumeNode()
    extract = vtk.vtkImageExtractComponents()
    if vtk.VTK_MAJOR_VERSION <= 5:
      extract.SetInput(self.multiVolumeNode.GetImageData())
    else:
      extract.SetInputData(self.multiVolumeNode.GetImageData)
    extract.SetComponents(0)
    extract.Update()
    ras2ijk = vtk.vtkMatrix4x4()
    ijk2ras = vtk.vtkMatrix4x4()
    self.multiVolumeNode.GetRASToIJKMatrix(ras2ijk)
    self.multiVolumeNode.GetIJKToRASMatrix(ijk2ras)

    self.nodePre.SetRASToIJKMatrix(ras2ijk)
    self.nodePre.SetIJKToRASMatrix(ijk2ras)
    self.nodePre.SetAndObserveImageData(extract.GetOutput())
    
    self.nodeArrayMultiVolume = self.createMultiVolumeNumpyArray(self.multiVolumeNode)
    self.nodeArrayPre = self.nodeArrayMultiVolume[:,:,:,0]
    self.nodeArrayFirst = self.nodeArrayMultiVolume[:,:,:,1]
    self.nodeArrayFinal = self.nodeArrayMultiVolume[:,:,:,-1]
  
    
  def setInputScalarVolumeNodes(self, nodePre, nodeFirst, nodeFinal):
    self.nodePre = nodePre
    self.nodeFirst = nodeFirst
    self.nodeFinal = nodeFinal
    self.nodeArrayPre = self.createNumpyArray (self.nodePre)
    self.nodeArrayFirst = self.createNumpyArray (self.nodeFirst)
    self.nodeArrayFinal = self.createNumpyArray (self.nodeFinal)
  
     
  def setAdvancedParameters(self, minimumThreshold=0.75, curve1Minimum=0.2, curve3Maximum=-0.2):
    self.minimumThreshold = minimumThreshold
    self.curve1Minimum = curve1Minimum
    self.curve3Maximum = curve3Maximum
  
    
  def setLabelROI (self, nodeLabel):
    self.ROIOn = True
    self.nodeArrayLabelMapROI = self.createNumpyArray(nodeLabel)   
  
        
  def initializeNodeArrays (self):
    # Computes percentage increase from baseline (pre-contrast) at each voxel for each volume as numpy arrays.
    # Initializes a numpy array of zeroes as numpy.int16 vtkShortArray for the SegmentCAD label map output.
      
    # Initial Rise at each voxel (percentage increase from pre-contrast to first post-contrast)
    self.nodeArrayInitialRise = ((self.nodeArrayFirst).__truediv__(self.nodeArrayPre+1.0))-1.0
    # Compute slope at each voxel from first to fourth volume to determine curve type
    self.slopeArray1_4 = (self.nodeArrayFinal - self.nodeArrayFirst).__truediv__(self.nodeArrayFirst+1.0)
    # Initialize SegmentCAD label map as numpy array
    shape = self.nodeArrayPre.shape
    self.nodeArraySegmentCADLabel = numpy.zeros(shape, dtype=numpy.int16)
  
    
  def arrayProcessing(self):
    # Create Boolean array, target_voxels, with target voxel indices highlighted as True 
    # Assigns color to SegmentCAD Label map index if corresponding slope condition is satisfied where target_voxel is True 
      
    if self.ROIOn:
      target_voxels = (self.nodeArrayLabelMapROI != 0) & (self.nodeArrayInitialRise > self.minimumThreshold) & (self.nodeArrayPre > 100)
    else:
      target_voxels = (self.nodeArrayInitialRise > self.minimumThreshold) & (self.nodeArrayPre > 100)
  
    # yellow (Plateau Slope)
    self.nodeArraySegmentCADLabel[numpy.where( (self.slopeArray1_4 > self.curve3Maximum) & (self.slopeArray1_4 < self.curve1Minimum) & (target_voxels) )] = 291
    
    # blue (slope of curve1 min = 0.2(default), Persistent Slope)
    self.nodeArraySegmentCADLabel[numpy.where((self.slopeArray1_4 > self.curve1Minimum) & (target_voxels))] = 306
    
    # red (slope of curve3 max = -0.2(default), Washout Slope )
    self.nodeArraySegmentCADLabel[numpy.where((self.slopeArray1_4 < self.curve3Maximum) & (target_voxels))] = 32
      
           
  def renderLabelMap(self):
    # Initializes a vtkMRMLScalarVolumeNode for the SegmentCAD Output and copies ijkToRAS matrix and Image data from nodeLabel
    ras2ijk = vtk.vtkMatrix4x4()
    ijk2ras = vtk.vtkMatrix4x4()
    self.nodePre.GetRASToIJKMatrix(ras2ijk)
    self.nodePre.GetIJKToRASMatrix(ijk2ras)
    self.SegmentCADLabelMap.SetRASToIJKMatrix(ras2ijk)
    self.SegmentCADLabelMap.SetIJKToRASMatrix(ijk2ras)
    SegmentCADLabelMapImageData = vtk.vtkImageData()
    SegmentCADLabelMapImageData.DeepCopy(self.nodePre.GetImageData())
    SegmentCADLabelMapPointData = SegmentCADLabelMapImageData.GetPointData()
    # Numpy array is converted from signed int16 to signed vtkShortArray
    scalarArray = vtk.vtkShortArray()
    dims1D = SegmentCADLabelMapPointData.GetScalars().GetSize()
    self.nodeArraySegmentCADLabel = self.nodeArraySegmentCADLabel.reshape(dims1D, order='C') #use a flattening function
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
    
    #red_logic = slicer.app.layoutManager().sliceWidget("Red").sliceLogic()
    #red_logic.GetSliceCompositeNode().SetLabelVolumeID(self.SegmentCADLabelMap.GetID())  
    #yellow_logic = slicer.app.layoutManager().sliceWidget("Yellow").sliceLogic()
    #yellow_logic.GetSliceCompositeNode().SetLabelVolumeID(self.SegmentCADLabelMap.GetID())
    #green_logic = slicer.app.layoutManager().sliceWidget("Green").sliceLogic()
    #green_logic.GetSliceCompositeNode().SetLabelVolumeID(self.SegmentCADLabelMap.GetID())
    
    appLogic = slicer.app.applicationLogic()
    selectionNode = appLogic.GetSelectionNode()
    #selectionNode.SetReferenceActiveVolumeID(self.nodePre.GetID())
    selectionNode.SetReferenceActiveLabelVolumeID(self.SegmentCADLabelMap.GetID())  
    #selectionNode.SetReferenceSecondaryVolumeID(self.node1.GetID())
    appLogic.PropagateVolumeSelection()
    
    
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
     
      
  def createNumpyArray (self, node):
    # Generate Numpy Array from vtkMRMLScalarVolumeNode
    imageData = vtk.vtkImageData()
    imageData = node.GetImageData()
    shapeData = list(imageData.GetDimensions())
    return (vtk.util.numpy_support.vtk_to_numpy(imageData.GetPointData().GetScalars()).reshape(shapeData))
  
  
  def createMultiVolumeNumpyArray (self, node):
    # Generate Numpy Array from vtkMRMLMultiVolumeNode
    imageData = vtk.vtkImageData()
    imageData = node.GetImageData()
    numComponents = imageData.GetNumberOfScalarComponents()
    shapeData = list(imageData.GetDimensions() + (numComponents,))
    return (vtk.util.numpy_support.vtk_to_numpy(imageData.GetPointData().GetScalars()).reshape(shapeData))
