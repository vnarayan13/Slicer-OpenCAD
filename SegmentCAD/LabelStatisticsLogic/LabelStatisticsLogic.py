from __main__ import vtk, qt, ctk, slicer
import string


class LabelStatisticsLogic:
  """This Logic is copied from the Label Statistics Module -Steve Pieper (Isomics)"""
  """Implement the logic to calculate label statistics.
  Nodes are passed in as arguments.
  Results are stored as 'statistics' instance variable.
  """
  
  def __init__(self, grayscaleNode, labelNode, fileName=None):
    volumeName = grayscaleNode.GetName()
    self.keys = ("Volume", "Curve Type", "Voxel Count", "Volume mm^3", "Volume cc", "Minimum Intensity", "Maximum Intensity", "Mean Intensity", "Standard Deviation")
    cubicMMPerVoxel = reduce(lambda x,y: x*y, labelNode.GetSpacing())
    ccPerCubicMM = 0.001
    
    self.labelStats = {}
    self.labelStats['Labels'] = []
   
    stataccum = vtk.vtkImageAccumulate()
    if vtk.VTK_MAJOR_VERSION <= 5:
      stataccum.SetInput(labelNode.GetImageData())
    else:
      stataccum.SetInputData(labelNode.GetImageData())
    stataccum.Update()
    lo = int(stataccum.GetMin()[0])
    hi = int(stataccum.GetMax()[0])

    for i in xrange(lo,hi+1):
      thresholder = vtk.vtkImageThreshold()
      if vtk.VTK_MAJOR_VERSION <= 5:
        thresholder.SetInput(labelNode.GetImageData())
      else:
        thresholder.SetInputData(labelNode.GetImageData())
      thresholder.SetInValue(1)
      thresholder.SetOutValue(0)
      thresholder.ReplaceOutOn()
      thresholder.ThresholdBetween(i,i)
      thresholder.SetOutputScalarTypeToUnsignedChar()
      thresholder.Update()

      stencil = vtk.vtkImageToImageStencil()
      if vtk.VTK_MAJOR_VERSION <= 5:
        stencil.SetInput(thresholder.GetOutput())
      else:
        stencil.SetInputConnection(thresholder.GetOutputPort())
      stencil.ThresholdBetween(1, 1)
      stencil.Update()

      stat1 = vtk.vtkImageAccumulate()
      if vtk.VTK_MAJOR_VERSION <= 5:
        stat1.SetInput(grayscaleNode.GetImageData())
        stat1.SetStencil(stencil.GetOutput())
      else:
        stat1.SetInputConnection(grayscaleNode.GetImageDataConnection())
        stat1.SetStencilData(stencil.GetOutput())
      stat1.Update()

      curveType = 'Curve Type'
      if i == 32:
        curveType = 'Washout Curve'
      elif i == 306:
        curveType = 'Persistent Curve'
      elif i == 291:
        curveType = 'Plateau Curve'
      elif i == 0:
        curveType = 'Unsegmented Region'
      if stat1.GetVoxelCount() > 0:
        # add an entry to the LabelStats list
        self.labelStats["Labels"].append(i)
        self.labelStats[i,"Volume"] = volumeName
        self.labelStats[i,"Curve Type"] = curveType
        self.labelStats[i,"Voxel Count"] = stat1.GetVoxelCount()
        self.labelStats[i,"Volume mm^3"] = self.labelStats[i,"Voxel Count"] * cubicMMPerVoxel
        self.labelStats[i,"Volume cc"] = self.labelStats[i,"Volume mm^3"] * ccPerCubicMM
        self.labelStats[i,"Minimum Intensity"] = stat1.GetMin()[0]
        self.labelStats[i,"Maximum Intensity"] = stat1.GetMax()[0]
        self.labelStats[i,"Mean Intensity"] = stat1.GetMean()[0]
        self.labelStats[i,"Standard Deviation"] = stat1.GetStandardDeviation()[0]
        
  def createStatsChart(self, labelNode, valueToPlot, ignoreZero=False):
    """Make a MRML chart of the current stats
    """
    layoutNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLLayoutNode')
    layoutNodes.InitTraversal()
    layoutNode = layoutNodes.GetNextItemAsObject()
    layoutNode.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalQuantitativeView)

    chartViewNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLChartViewNode')
    chartViewNodes.InitTraversal()
    chartViewNode = chartViewNodes.GetNextItemAsObject()
 	
    arrayNodeLabel = slicer.mrmlScene.AddNode(slicer.vtkMRMLDoubleArrayNode())
    array = arrayNodeLabel.GetArray()
    samples = len(self.labelStats["Labels"])
    tuples = samples
    if ignoreZero and self.labelStats["Labels"].__contains__(0):
      tuples -= 1

    array.SetNumberOfTuples(tuples)
    tuple = 0

    for i in xrange(samples):
      index = self.labelStats["Labels"][i]
      if not (ignoreZero and index == 0):
        array.SetComponent(tuple, 0, index)
        array.SetComponent(tuple, 1, self.labelStats[index,valueToPlot])
        array.SetComponent(tuple, 2, 0)
        tuple += 1
	
    chartNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLChartNode())
    chartNode.AddArray(valueToPlot, arrayNodeLabel.GetID())
 	
    chartViewNode.SetChartNodeID(chartNode.GetID())
 	
    chartNode.SetProperty('default', 'title', 'OpenCAD Label Statistics')
    chartNode.SetProperty('default', 'xAxisLabel', 'OpenCAD Label')
    chartNode.SetProperty('default', 'yAxisLabel', valueToPlot)
    chartNode.SetProperty('default', 'type', 'Bar');
    chartNode.SetProperty('default', 'xAxisType', 'categorical')
    chartNode.SetProperty('default', 'showLegend', 'off')
 	
    # series level properties
    if labelNode.GetDisplayNode() != None and labelNode.GetDisplayNode().GetColorNode() != None:
      chartNode.SetProperty(valueToPlot, 'lookupTable', labelNode.GetDisplayNode().GetColorNodeID());

  
