import os
import inspect
from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import LabelStatisticsLogic
import SegmentCADLogic

#
# SegmentCAD
#

class SegmentCAD:
  def __init__(self, parent):
    parent.title = "SegmentCAD"
    parent.categories = ["Segmentation"]
    parent.dependencies = []
    parent.contributors = ["Vivek Narayan, Jayender Jagadeesan (BWH)"] 
    parent.helpText = """
    This Module applies SegmentCAD segmentation to input DCE-MRI Volumes and generates a label map. A label map and a label number can be provided to restrict segmentation to an ROI.
    """
    parent.acknowledgementText = """
    This file was originally developed by Vivek Narayan and Jayender Jagadeesan (Brigham and Women's Hospital)
    """
   
    MODULE_PATH = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))
    ICON_PATH = os.path.join(MODULE_PATH, 'Resources', 'Icons', 'OpenCAD.png').replace("\\","/")
    parent.icon = qt.QIcon(ICON_PATH)
    
    self.parent = parent

#
# qSegmentCADWidget
#

class SegmentCADWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()
      
  def setup(self):
    # reload button
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "HeterogeneityCAD Reload"
    self.layout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    
    
    # Tumor Segmentation Collapsible Button
    self.TumorSegmentationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.TumorSegmentationCollapsibleButton.text = "SegmentCAD Segmentation"
    self.layout.addWidget(self.TumorSegmentationCollapsibleButton)
    self.TumorSegmentationLayout = qt.QFormLayout(self.TumorSegmentationCollapsibleButton)
       
    # Select Volumes Collapsible Button
    self.selectionsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.selectionsCollapsibleButton.text = "Select DCE-MRI Volumes for Segmentation"
    self.TumorSegmentationLayout.addWidget(self.selectionsCollapsibleButton)
    # Layout within the collapsible button
    self.volumesLayout = qt.QFormLayout(self.selectionsCollapsibleButton)
    
    # Use Multivolume Node as input
    self.enableMultiVolume = qt.QCheckBox(self.selectionsCollapsibleButton)
    self.enableMultiVolume.setText('Input Multi-Volume Node')
    self.enableMultiVolume.checked = True
    self.enableMultiVolume.setToolTip('Use Multi-Volume Node, with volumes imported in the correct order')
    self.inputSelectorMultiVolume = slicer.qMRMLNodeComboBox(self.selectionsCollapsibleButton)
    self.inputSelectorMultiVolume.nodeTypes = ( ("vtkMRMLMultiVolumeNode"), "" )
    self.inputSelectorMultiVolume.selectNodeUponCreation = False
    self.inputSelectorMultiVolume.renameEnabled = True
    self.inputSelectorMultiVolume.removeEnabled = False
    self.inputSelectorMultiVolume.noneEnabled = True
    self.inputSelectorMultiVolume.addEnabled = False
    self.inputSelectorMultiVolume.setMRMLScene(slicer.mrmlScene)
    self.inputSelectorMultiVolume.setToolTip('Use Multi-Volume Node, with volumes imported in the correct order')
       
    self.volumesLayout.addRow (self.enableMultiVolume, self.inputSelectorMultiVolume)
    
    self.nodeInputFrame = ctk.ctkCollapsibleGroupBox(self.selectionsCollapsibleButton)
    self.nodeInputFrame.title = "Input Scalar Volume Nodes"
    self.nodeInputFrame.collapsed = True
    self.nodeInputFrame.enabled = False
    self.nodeInputFrame.setLayout(qt.QFormLayout())
    self.volumesLayout.addRow(self.nodeInputFrame)
    
    # Select Pre Node
    self.inputPre = qt.QLabel("Pre-contrast Volume", self.nodeInputFrame)
    self.inputPre.setToolTip('Select the initial pre-contrast volume node.')
    self.inputSelectorPre = slicer.qMRMLNodeComboBox(self.nodeInputFrame)
    self.inputSelectorPre.nodeTypes = (("vtkMRMLScalarVolumeNode"), "")
    self.inputSelectorPre.addAttribute(("vtkMRMLScalarVolumeNode"), "LabelMap", "0")
    self.inputSelectorPre.selectNodeUponCreation = False
    self.inputSelectorPre.addEnabled = False
    self.inputSelectorPre.removeEnabled = False
    self.inputSelectorPre.noneEnabled = True
    self.inputSelectorPre.noneDisplay = 'Please Select Volume'
    self.inputSelectorPre.setMRMLScene(slicer.mrmlScene)
    self.inputSelectorPre.setToolTip('Select the initial pre-contrast volume node.')
    #self.volumesLayout.addRow(self.inputPre, self.inputSelectorPre)
    self.nodeInputFrame.layout().addRow(self.inputPre, self.inputSelectorPre)
    
    # Select First Node
    self.inputFirst = qt.QLabel("First Post-contrast Volume", self.nodeInputFrame)
    self.inputFirst.setToolTip('Select the first post-contrast volume node to calculate intitial enhancement and curve type.')
    self.inputSelectorFirst = slicer.qMRMLNodeComboBox(self.nodeInputFrame)
    self.inputSelectorFirst.nodeTypes = (("vtkMRMLScalarVolumeNode"), "")
    self.inputSelectorFirst.addAttribute(("vtkMRMLScalarVolumeNode"), "LabelMap", "0")
    self.inputSelectorFirst.selectNodeUponCreation = False
    self.inputSelectorFirst.addEnabled = False
    self.inputSelectorFirst.removeEnabled = False
    self.inputSelectorFirst.noneEnabled = True
    self.inputSelectorFirst.noneDisplay = 'Please Select Volume'
    self.inputSelectorFirst.setMRMLScene(slicer.mrmlScene)
    self.inputSelectorFirst.setToolTip('Select the first post-contrast volume node to calculate intitial enhancement and curve type.')
    #self.volumesLayout.addRow(self.inputFirst, self.inputSelectorFirst)
    self.nodeInputFrame.layout().addRow(self.inputFirst, self.inputSelectorFirst)
    
    # Select Second Node
    self.inputSecond = qt.QLabel("Second Post-contrast Volume", self.nodeInputFrame)
    self.inputSecond.setToolTip('Select a second post-contrast volume node (not required).')
    self.inputSelectorSecond = slicer.qMRMLNodeComboBox(self.nodeInputFrame)
    self.inputSelectorSecond.nodeTypes = (("vtkMRMLScalarVolumeNode"), "")
    self.inputSelectorSecond.addAttribute(("vtkMRMLScalarVolumeNode"), "LabelMap", "0")
    self.inputSelectorSecond.selectNodeUponCreation = False
    self.inputSelectorSecond.addEnabled = False
    self.inputSelectorSecond.removeEnabled = False
    self.inputSelectorSecond.noneEnabled = True
    self.inputSelectorSecond.noneDisplay = 'Please Select Volume'
    self.inputSelectorSecond.setMRMLScene(slicer.mrmlScene)
    self.inputSelectorSecond.setToolTip('Select a second post-contrast volume node (not required).')
    #self.volumesLayout.addRow(self.inputSecond, self.inputSelectorSecond)
    self.nodeInputFrame.layout().addRow(self.inputSecond, self.inputSelectorSecond)
    
    # Select Third Node 
    self.inputThird = qt.QLabel("Third Post-contrast Volume", self.nodeInputFrame)
    self.inputThird.setToolTip('Select a third post-contrast volume node (not required).')
    self.inputSelectorThird = slicer.qMRMLNodeComboBox(self.nodeInputFrame)
    self.inputSelectorThird.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputSelectorThird.addAttribute( ("vtkMRMLScalarVolumeNode"), "LabelMap", "0")
    self.inputSelectorThird.selectNodeUponCreation = False
    self.inputSelectorThird.addEnabled = False
    self.inputSelectorThird.removeEnabled = False
    self.inputSelectorThird.noneEnabled = True
    self.inputSelectorThird.noneDisplay = 'Please Select Volume'
    self.inputSelectorThird.setMRMLScene(slicer.mrmlScene)
    self.inputSelectorThird.setToolTip('Select a third post-contrast volume node (not required).')
    #self.volumesLayout.addRow(self.inputThird, self.inputSelectorThird)
    self.nodeInputFrame.layout().addRow(self.inputThird, self.inputSelectorThird)
    
    # Select Fourth Node  
    self.inputFourth = qt.QLabel("Fourth Post-contrast Volume", self.nodeInputFrame)
    self.inputFourth.setToolTip('Select the fourth or final post-contrast volume node to calculate curve type based on the delayed curve slope.')
    self.inputSelectorFourth = slicer.qMRMLNodeComboBox(self.nodeInputFrame)
    self.inputSelectorFourth.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputSelectorFourth.addAttribute( ("vtkMRMLScalarVolumeNode"), "LabelMap", "0")
    self.inputSelectorFourth.selectNodeUponCreation = False
    self.inputSelectorFourth.addEnabled = False
    self.inputSelectorFourth.removeEnabled = False
    self.inputSelectorFourth.noneEnabled = True
    self.inputSelectorFourth.noneDisplay = 'Please Select Volume'
    self.inputSelectorFourth.setMRMLScene(slicer.mrmlScene)
    self.inputSelectorFourth.setToolTip('Select the fourth or final post-contrast volume node to calculate curve type based on the delayed curve slope.')
    #self.volumesLayout.addRow(self.inputFourth, self.inputSelectorFourth)
    self.nodeInputFrame.layout().addRow(self.inputFourth, self.inputSelectorFourth)
    
    # Enable and Select Input Label Map as ROI
    self.enableLabel = qt.QCheckBox(self.selectionsCollapsibleButton)
    self.enableLabel.setText('Use Label Map as ROI')
    self.enableLabel.checked = True
    self.enableLabel.setToolTip('Select and identify a custom label map node to define an ROI over the input volumes for faster segmentation.')
    self.inputSelectorLabel = slicer.qMRMLNodeComboBox(self.selectionsCollapsibleButton)
    self.inputSelectorLabel.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputSelectorLabel.addAttribute( ("vtkMRMLScalarVolumeNode"), "LabelMap", "1")
    self.inputSelectorLabel.selectNodeUponCreation = False
    self.inputSelectorLabel.renameEnabled = True
    self.inputSelectorLabel.removeEnabled = False
    self.inputSelectorLabel.noneEnabled = True
    self.inputSelectorLabel.addEnabled = False
    self.inputSelectorLabel.setMRMLScene(slicer.mrmlScene)
    self.inputSelectorLabel.setToolTip('Select and identify a custom label map node to define an ROI over the input volumes for faster segmentation.')
    self.volumesLayout.addRow (self.enableLabel, self.inputSelectorLabel)
    
    # Select output SegmentCAD Label collapsible button
    self.outlabelCollapsibleButton = ctk.ctkCollapsibleButton()
    self.outlabelCollapsibleButton.text = "Select or Create Output SegmentCAD Label Map"
    self.TumorSegmentationLayout.addWidget(self.outlabelCollapsibleButton)
    # Layout within the collapsible button
    self.outlabelLayout = qt.QFormLayout(self.outlabelCollapsibleButton)
    # Select or create output SegmentCAD Label Map
    self.outputLabel = qt.QLabel("Output SegmentCAD Label Map", self.outlabelCollapsibleButton)
    self.outputLabel.setToolTip('Select or create a label map volume node as the SegmentCAD segmentation output.')
    self.outputSelectorLabel = slicer.qMRMLNodeComboBox(self.outlabelCollapsibleButton)
    self.outputSelectorLabel.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.outputSelectorLabel.addAttribute( ("vtkMRMLScalarVolumeNode"), "LabelMap", "1")
    self.outputSelectorLabel.baseName = "SegmentCAD Label Map"
    self.outputSelectorLabel.selectNodeUponCreation = True
    self.outputSelectorLabel.renameEnabled = True
    self.outputSelectorLabel.removeEnabled = True
    self.outputSelectorLabel.noneEnabled = False
    self.outputSelectorLabel.addEnabled = True
    self.outputSelectorLabel.setMRMLScene(slicer.mrmlScene)
    self.outputSelectorLabel.setToolTip('Select or create a label map volume node as the SegmentCAD segmentation output.')
    self.outlabelLayout.addRow(self.outputLabel, self.outputSelectorLabel)
    # SegmentCAD Label Map Legend
    self.outputLegend = qt.QLabel("| Type I Persistent: Blue | Type II Plateau: Yellow | Type III Washout: Red |", self.outlabelCollapsibleButton)
    self.outputLegend.setToolTip('SegmentCAD Label Map Legend  | Blue: Type I Persistent curve  |  Yellow: Type II Plateau curve  |  Red: Type III Washout curve  |')
    self.outlabelLayout.addRow(self.outputLegend)
    # Enable Volume Rendering of the SegmentCAD label map
    self.enableVolumeRendering = qt.QCheckBox(self.selectionsCollapsibleButton)
    self.enableVolumeRendering.setText('Display Volume Rendering')
    self.enableVolumeRendering.checked = True
    self.enableVolumeRendering.setToolTip('Display volume rendering of the SegmentCAD Label Map in the 3D View')
    self.outlabelLayout.addRow (self.enableVolumeRendering)
    # Enable Label Statistics Table and Data 
    self.enableStats = qt.QCheckBox(self.selectionsCollapsibleButton)
    self.enableStats.setText('Calculate SegmentCAD Label statistics')
    self.enableStats.checked = False
    self.enableStats.setToolTip('Use logic from Label Statistics Module to calculate statistics for first post-contrast voxels within the SegmentCAD Label Map.')
    self.outlabelLayout.addRow (self.enableStats)
  
    # Set Advanced Parameters Collapsible Button
    self.parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    self.parametersCollapsibleButton.text = "Set Advanced Segmentation Parameters"
    self.TumorSegmentationLayout.addWidget(self.parametersCollapsibleButton)
    self.parametersCollapsibleButton.collapsed = True
    # Layout within the collapsible button
    self.parametersLayout = qt.QFormLayout(self.parametersCollapsibleButton)
    # Set Minimum Threshold of Percentage Increase to First Post-Contrast Image
    self.inputMinimumThreshold = qt.QLabel("Minimum Threshold of Increase", self.parametersCollapsibleButton)
    self.inputMinimumThreshold.setToolTip('Minimum Threshold of Percentage Increase (Pre- to First Post-contrast (Range: 10% to 150%)')
    self.inputSelectorMinimumThreshold = qt.QDoubleSpinBox(self.parametersCollapsibleButton)
    self.inputSelectorMinimumThreshold.setSuffix("%")
    self.inputSelectorMinimumThreshold.singleStep = (1)
    self.inputSelectorMinimumThreshold.minimum = (10)
    self.inputSelectorMinimumThreshold.maximum = (150)
    self.inputSelectorMinimumThreshold.value = (75)
    self.inputSelectorMinimumThreshold.setToolTip('Minimum Threshold of Percentage Increase (Pre- to First Post-contrast (Range: 10% to 150%)')
    self.parametersLayout.addRow(self.inputMinimumThreshold, self.inputSelectorMinimumThreshold)
    # Curve 1 Type Parameters (Slopes from First to Fourth Post-Contrast Images)
    self.inputCurve1 = qt.QLabel("Type 1 (Persistent) Curve Minimum Slope", self.parametersCollapsibleButton)
    self.inputCurve1.setToolTip('Minimum Slope of Delayed Curve to classify as Persistent (Range: 0.02 to 0.3)')
    self.inputSelectorCurve1 = qt.QDoubleSpinBox(self.parametersCollapsibleButton)
    self.inputSelectorCurve1.singleStep = (0.02)
    self.inputSelectorCurve1.minimum = (0.02)
    self.inputSelectorCurve1.maximum = (0.3)
    self.inputSelectorCurve1.value = (0.20)
    self.inputSelectorCurve1.setToolTip('Minimum Slope of Delayed Curve to classify as Persistent (Range: 0.02 to 0.3)')
    self.parametersLayout.addRow(self.inputCurve1, self.inputSelectorCurve1)
    # Curve 3 Type Parameters (Slopes from First to Fourth Post-Contrast Images)
    self.inputCurve3 = qt.QLabel("Type 3 (Washout) Curve Maximum Slope", self.parametersCollapsibleButton)
    self.inputCurve3.setToolTip('Maximum Slope of Delayed Curve to classify as Washout (Range: -0.02 to -0.3)')
    self.inputSelectorCurve3 = qt.QDoubleSpinBox(self.parametersCollapsibleButton)
    self.inputSelectorCurve3.singleStep = (0.02)
    self.inputSelectorCurve3.setPrefix("-")
    self.inputSelectorCurve3.minimum = (0.02)
    self.inputSelectorCurve3.maximum = (0.30)
    self.inputSelectorCurve3.value = (0.20)
    self.inputSelectorCurve3.setToolTip('Maximum Slope of Delayed Curve to classify as Washout (Range: -0.02 to -0.3)')
    self.parametersLayout.addRow(self.inputCurve3, self.inputSelectorCurve3)
    # Apply Tumor Adaptive Segmentation button
    self.SegmentCADButton = qt.QPushButton("Apply SegmentCAD")
    self.SegmentCADButton.toolTip = "Apply SegmentCAD segmentation to selected volumes."
    self.TumorSegmentationLayout.addWidget(self.SegmentCADButton)
    
    # LabelStatistics Table Collapsible Button
    self.labelstatisticsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.labelstatisticsCollapsibleButton.text = "SegmentCAD Label Statistics"
    self.layout.addWidget(self.labelstatisticsCollapsibleButton)
    self.labelstatisticsCollapsibleButton.collapsed = True
    # Layout within the collapsible button
    self.labelstatisticsLayout = qt.QFormLayout(self.labelstatisticsCollapsibleButton)
    # Table View to display Label statistics
    self.labelStatisticsTableView = qt.QTableView()
    self.labelStatisticsTableView.sortingEnabled = True
    self.labelstatisticsLayout.addWidget(self.labelStatisticsTableView)
    self.labelStatisticsTableView.minimumHeight = 200
    # Charting Statistics Button
    self.chartOptions = ("Volume", "Curve Type", "Voxel Count", "Volume mm^3", "Volume cc", "Minimum Intensity", "Maximum Intensity", "Mean Intensity", "Standard Deviation")
    self.chartFrame = qt.QFrame()
    self.chartFrame.setLayout(qt.QHBoxLayout())
    self.labelstatisticsLayout.addWidget(self.chartFrame)
    self.chartButton = qt.QPushButton("Chart Statistics", self.labelstatisticsCollapsibleButton)
    self.chartButton.toolTip = "Make a chart from the current statistics."
    self.chartFrame.layout().addWidget(self.chartButton)
    self.chartOption = qt.QComboBox(self.labelstatisticsCollapsibleButton)
    self.chartOption.addItems(self.chartOptions)
    self.chartFrame.layout().addWidget(self.chartOption)
    self.chartIgnoreZero = qt.QCheckBox(self.labelstatisticsCollapsibleButton)
    self.chartIgnoreZero.setText('Ignore Zero Label')
    self.chartIgnoreZero.checked = False
    self.chartIgnoreZero.setToolTip('Do not include the zero index in the chart to avoid dwarfing other bars')
    self.chartFrame.layout().addWidget(self.chartIgnoreZero)
    self.chartButton.enabled = False
    
    # Interactive Charting Settings Collapsible Button
    self.iChartingCollapsibleButton = ctk.ctkCollapsibleButton()
    self.iChartingCollapsibleButton.text = "Interactive Charting Settings"
    self.iChartingCollapsibleButton.collapsed = True
    self.layout.addWidget(self.iChartingCollapsibleButton)
    # Layout within the collapsible button
    self.iChartingLayout = qt.QFormLayout(self.iChartingCollapsibleButton)
    # iCharting toggle button
    self.iCharting = qt.QPushButton("Enable Interactive Charting")
    self.iCharting.checkable = True
    self.iCharting.setChecked(False)
    self.iCharting.enabled = False
    self.iCharting.toolTip = "Toggle the real-time charting of the %increase from baseline of the selected voxel from each input volume."
    self.iChartingLayout.addRow(self.iCharting)
    
    # Initialize slice observers (from DataProbe.py)
    # Keep list of pairs: [observee,tag] so they can be removed easily
    self.styleObserverTags = []
    # Keep a map of interactor styles to sliceWidgets so we can easily get sliceLogic
    self.sliceWidgetsPerStyle = {}
    self.refreshObservers()
    
    # Connections
    self.SegmentCADButton.connect('clicked()', self.onSegmentCADButtonClicked)
    self.enableLabel.connect('stateChanged(int)', self.onEnableLabel)
    self.enableMultiVolume.connect('stateChanged(int)', self.onEnableMultiVolume)
    self.chartButton.connect('clicked()', self.onChart)
    self.iCharting.connect('toggled(bool)', self.onInteractiveChartingChanged)
    
  def removeObservers(self):
    # Remove observers and reset
    for observee,tag in self.styleObserverTags:
      observee.RemoveObserver(tag)
    self.styleObserverTags = []
    self.sliceWidgetsPerStyle = {}

  def refreshObservers(self):
    # When the layout changes, drop the observers from all the old widgets and create new observers for the newly created widgets
    self.removeObservers()
    # Get new slice nodes
    layoutManager = slicer.app.layoutManager()
    sliceNodeCount = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSliceNode')
    for nodeIndex in xrange(sliceNodeCount):
      # Find the widget for each node in scene
      sliceNode = slicer.mrmlScene.GetNthNodeByClass(nodeIndex, 'vtkMRMLSliceNode')
      sliceWidget = layoutManager.sliceWidget(sliceNode.GetLayoutName())
      if sliceWidget:
        # Add obserservers and keep track of tags
        style = sliceWidget.sliceView().interactorStyle()
        self.sliceWidgetsPerStyle[style] = sliceWidget
        events = ("MouseMoveEvent", "EnterEvent", "LeaveEvent")
        for event in events:
          tag = style.AddObserver(event, self.interactiveCharting)
          self.styleObserverTags.append([style,tag])

  def onInteractiveChartingChanged(self, checked):
    if checked:
      self.iCharting.text = 'Disable Interactive Charting'
    else:
      self.iCharting.text = 'Enable Interactive Charting'
      
  def initializeCharting(self):
    # Enable iCharting Settings
    self.iCharting.setChecked(True)
    self.iCharting.enabled = True
    self.iChartingCollapsibleButton.collapsed = False
    # Initialize image data (pre-contrast node at index '0')
    self.nComponents = len(self.volumeNodes)
    self.nodeImageData = []
    for node in xrange (self.nComponents):
      self.nodeImageData.append(self.volumeNodes[node].GetImageData())
    self.extent = self.nodeImageData[0].GetExtent()
    # Change active volume nodes in scene
    appLogic = slicer.app.applicationLogic()
    selectionNode = appLogic.GetSelectionNode()
    selectionNode.SetReferenceActiveVolumeID(self.nodePre.GetID())
    selectionNode.SetReferenceActiveLabelVolumeID(self.nodeSegmentCAD.GetID())
    selectionNode.SetReferenceSecondaryVolumeID(self.node1.GetID())
    appLogic.PropagateVolumeSelection()
    # Change scene layout to conventional quantitative view
    layoutNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLLayoutNode')
    layoutNodes.InitTraversal()
    layoutNode = layoutNodes.GetNextItemAsObject()
    layoutNode.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalQuantitativeView)
    # Set up chart within the scene
    self.chartViewNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLChartViewNode')
    self.chartViewNodes.InitTraversal()
    self.chartViewNode = self.chartViewNodes.GetNextItemAsObject()
    self.arrayNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLDoubleArrayNode())
    self.chartNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLChartNode())
    self.chartNode.AddArray('voxelijk', self.arrayNode.GetID())
    self.chartNode.SetProperty('default', 'title', 'Interactive Charting')
    self.chartNode.SetProperty('default', 'xAxisLabel', 'DCE-MRI Volumes')
    self.chartNode.SetProperty('default', 'yAxisLabel', 'Percentage Increase from Baseline')
    self.chartNode.SetProperty('default', 'type', 'Line')
    self.chartNode.SetProperty('default', 'xAxisType', 'quantitative')
    self.chartNode.SetProperty('default', 'showGrid', 'on')
    self.chartNode.SetProperty('default', 'showLegend', 'on')
    self.chartNode.SetProperty('default', 'showMarkers', 'on')
    self.chartNode.SetProperty('default', 'xAxisPad', '1')
    self.chartViewNode.SetChartNodeID(self.chartNode.GetID())

  def interactiveCharting(self, observee, event):
    """This Logic is derived from the Multi-Volume Explorer Module -Steve Pieper (Isomics)"""
    # iCharting Events
    if not self.iCharting.checked:
      return
    for node in xrange(self.nComponents):
      if not self.volumeNodes[node]:
        return
    # TODO: Use a timer to delay calculation and compress events
    if event == 'LeaveEvent':
      self.chartNode.ClearArrays()
      # Reset all the readouts/labels
      return
    if not self.sliceWidgetsPerStyle.has_key(observee):
      return
    # Extract coordinate and node data from mouse pointer position
    sliceWidget = self.sliceWidgetsPerStyle[observee]
    sliceLogic = sliceWidget.sliceLogic()
    interactor = observee.GetInteractor()
    xy = interactor.GetEventPosition()
    xyz = sliceWidget.sliceView().convertDeviceToXYZ(xy);
    ras = sliceWidget.sliceView().convertXYZToRAS(xyz)
    bgLayer = sliceLogic.GetBackgroundLayer()
    volumeNode = bgLayer.GetVolumeNode()
    if volumeNode not in self.volumeNodes:
      return
    # Get the vector of values at IJK
    nameLabel = volumeNode.GetName()
    xyToIJK = bgLayer.GetXYToIJKTransform()
    ijkFloat = xyToIJK.TransformDoublePoint(xyz)
    ijk = []
    for element in ijkFloat:
      try:
        index = int(round(element))
      except ValueError:
        index = 0
      ijk.append(index)
    # Check if pixel is outside the valid extent
    if not (ijk[0]>=self.extent[0] and ijk[0]<=self.extent[1] and \
       ijk[1]>=self.extent[2] and ijk[1]<=self.extent[3] and \
       ijk[2]>=self.extent[4] and ijk[2]<=self.extent[5]):
      return
    # Set Up Scene Layout and get chart array
    self.chartNode.ClearArrays()
    array = self.arrayNode.GetArray()
    array.SetNumberOfTuples(self.nComponents)
    # Percentage of baseline calculations (baselineSignal = Pre-Contrast Signal)
    baselineSignal = self.nodeImageData[0].GetScalarComponentAsDouble(ijk[0], ijk[1], ijk[2], 0)
    baselinePercentages = []
    volumeIntensities = []
    curveType = 'Curve Type'
    if (baselineSignal != 0):
      for c in xrange(self.nComponents):
        volumeIntensities.append(self.nodeImageData[c].GetScalarComponentAsDouble(ijk[0],ijk[1],ijk[2], 0))
        baselinePercentages.append((volumeIntensities[c]).__truediv__(baselineSignal))
        array.SetComponent(c, 0, c)
        array.SetComponent(c, 1, ((baselinePercentages[c]-1.0)*100.))
        array.SetComponent(c, 2, 0)
    else:
      for c in xrange(self.nComponents):
        array.SetComponent(c, 0, c)
        array.SetComponent(c, 1, 0)
        array.SetComponent(c, 2, 0)
    # Slope Calculations
    if (baselineSignal != 0) and (baselinePercentages[1] != 0):
      slope1_4 = (volumeIntensities[self.nComponents-1] - volumeIntensities[1]).__truediv__(volumeIntensities[1])
      if (slope1_4 > self.curve1Minimum):
        curveType = 'Type 1: Persistent'
      elif (slope1_4 < self.curve3Maximum):
        curveType = 'Type 3: Washout'
      else:
        curveType = 'Type 2: Plateau'
    self.chartNode.AddArray(curveType, self.arrayNode.GetID())
  
  def onEnableLabel(self):
    # Enable the use of an input label map as an ROI
    if self.enableLabel.isChecked():
      self.inputSelectorLabel.enabled = True
    else:
      self.inputSelectorLabel.enabled = False
      
  def onEnableMultiVolume(self):
    # Toggle between single MultiVolume Node input or multiple Scalar Volume inputs
    if self.enableMultiVolume.isChecked():
      self.nodeInputFrame.collapsed = True
      self.nodeInputFrame.enabled = False
      self.inputSelectorMultiVolume.enabled = True
      self.enableMultiVolume.setStyleSheet('color: black')
    else:     
      self.nodeInputFrame.collapsed = False
      self.nodeInputFrame.enabled = True 
      self.inputSelectorMultiVolume.enabled = False
      self.inputSelectorMultiVolume.setCurrentNode(None)
      self.enableMultiVolume.setStyleSheet('color: gray')
          
  def onChart(self):
    """This Logic is copied from the Label Statistics Module -Steve Pieper (Isomics)"""
    # Create a bar chart of SegmentCAD label statistics data
    valueToPlot = self.chartOptions[self.chartOption.currentIndex]
    ignoreZero = self.chartIgnoreZero.checked
    self.statisticsLogic.createStatsChart(self.nodeSegmentCAD,valueToPlot,ignoreZero)
    
  def populateStats(self):
    """This Logic is copied from the Label Statistics Module -Steve Pieper (Isomics)"""
    # Populate the table with SegmentCAD label map statistics
    if not (self.logic and self.statisticsLogic):
      return
    displayNode = self.nodeSegmentCAD.GetDisplayNode()
    colorNode = displayNode.GetColorNode()
    lut = colorNode.GetLookupTable()
    self.items = []
    self.model = qt.QStandardItemModel()
    self.labelStatisticsTableView.setModel(self.model)
    self.labelStatisticsTableView.verticalHeader().visible = False
    row = 0
    for i in self.statisticsLogic.labelStats["Labels"]:
      color = qt.QColor()
      rgb = lut.GetTableValue(i)
      color.setRgb(rgb[0]*255,rgb[1]*255,rgb[2]*255)
      item = qt.QStandardItem()
      item.setData(color,1)
      item.setToolTip(colorNode.GetColorName(i))
      self.model.setItem(row,0,item)
      self.items.append(item)
      col = 1
      for k in self.statisticsLogic.keys:
        item = qt.QStandardItem()
        item.setText(str(self.statisticsLogic.labelStats[i,k]))
        item.setToolTip(colorNode.GetColorName(i))
        self.model.setItem(row,col,item)
        self.items.append(item)
        col += 1
      row += 1

    self.labelStatisticsTableView.setColumnWidth(0,30)
    self.model.setHeaderData(0,1," ")
    col = 1
    for k in self.statisticsLogic.keys:
      self.labelStatisticsTableView.setColumnWidth(col,15*len(k))
      self.model.setHeaderData(col,1,k)
      col += 1
      
  def onSegmentCADButtonClicked(self):
    self.SegmentCADButton.text = "Processing..."
    slicer.app.processEvents()
    
    enabledMultiVolume = self.enableMultiVolume.isChecked()
    enabledROI = self.enableLabel.isChecked()
    enabledVolumeRendering = self.enableVolumeRendering.isChecked()
    
    if enabledMultiVolume:
      self.nodeMultiVolume = self.inputSelectorMultiVolume.currentNode()
    else:     
      self.nodePre = self.inputSelectorPre.currentNode()
      self.node1 = self.inputSelectorFirst.currentNode()
      self.node2 = self.inputSelectorSecond.currentNode()
      self.node3 = self.inputSelectorThird.currentNode()
      self.node4 = self.inputSelectorFourth.currentNode()
    
    if enabledROI:    
      self.nodeLabel = self.inputSelectorLabel.currentNode()    
    
    self.nodeSegmentCAD = self.outputSelectorLabel.currentNode()
    
    self.minimumThreshold = (self.inputSelectorMinimumThreshold.value)/(100)
    self.curve3Maximum = -1 * (self.inputSelectorCurve3.value)
    self.curve1Minimum = self.inputSelectorCurve1.value
    
    # Check if input Volumes and ROI are provided
    if enabledMultiVolume and (not (self.nodeMultiVolume)):
      qt.QMessageBox.critical(slicer.util.mainWindow(),'SegmentCAD', 'Please select a Multi-Volume Node representing a DCE-MRI time series')
      self.SegmentCADButton.text = "Apply SegmentCAD"
      return
    if (not (enabledMultiVolume)) and (not (self.nodePre and self.node1 and self.node4)):
      qt.QMessageBox.critical(slicer.util.mainWindow(),'SegmentCAD', 'Please select one pre-contrast volume and at least two post-contrast volumes')
      self.SegmentCADButton.text = "Apply SegmentCAD"
      return
    if not (self.nodeSegmentCAD):
      qt.QMessageBox.critical(slicer.util.mainWindow(),'SegmentCAD', 'Please create or select an output label map volume.')
      self.SegmentCADButton.text = "Apply SegmentCAD"
      return
    if enabledROI and (not (self.nodeLabel)):
      qt.QMessageBox.critical(slicer.util.mainWindow(),'SegmentCAD', 'Please provide an input label map to use as ROI')
      self.SegmentCADButton.text = "Apply SegmentCAD"
      return
      
    # Generate list of valid volume nodes for charting
    if (not (enabledMultiVolume)):  
      self.volumeNodes = [self.nodePre, self.node1, self.node4]
      if self.node2:
        self.volumeNodes.insert(2, self.node2)
      if self.node3:
        self.volumeNodes.insert(3, self.node3)

    # Initialize segmentation inputs and parameters
    self.SegmentCADButton.text = "Converting Volumes to Arrays"
    slicer.app.processEvents()
    self.logic = SegmentCADLogic.SegmentCADLogic(self.nodeSegmentCAD)#, self.nodePre, self.node1, self.node4)
    
    if enabledMultiVolume:
      self.logic.setInputMultiVolumeNode(self.nodeMultiVolume)
    else:
      self.logic.setInputScalarVolumeNodes(self.nodePre, self.node1, self.node4)  
      
    if enabledROI:
      self.logic.setLabelROI(self.nodeLabel)
    self.logic.setAdvancedParameters(self.minimumThreshold, self.curve1Minimum, self.curve3Maximum)
    self.logic.initializeNodeArrays()

    # Segment and generate SegmentCAD label map
    self.SegmentCADButton.text = "Computing and Rendering SegmentCAD Label Map..."
    slicer.app.processEvents()
    self.logic.arrayProcessing()
    self.logic.renderLabelMap()
    if enabledVolumeRendering:
      self.logic.renderVolume()

    # Generate statistics table for SegmentCAD label map
    self.SegmentCADButton.text = "Populating SegmentCAD Label Statistics Data"
    slicer.app.processEvents()
    if (not (enabledMultiVolume)) and self.enableStats.isChecked():
      self.statisticsLogic = LabelStatisticsLogic.LabelStatisticsLogic(self.node1, self.nodeSegmentCAD)
      self.populateStats()
      self.chartButton.enabled = True
      self.labelstatisticsCollapsibleButton.collapsed = False
      
    self.SegmentCADButton.text = "Apply SegmentCAD"
    
    if (not (enabledMultiVolume)):
      self.initializeCharting()
    return

  def onReload(self, moduleName="SegmentCAD"):
    #Generic reload method for any scripted module.
    #ModuleWizard will subsitute correct default moduleName.
    
    import imp, sys, os, slicer
    
    widgetName = moduleName + "Widget"

    # reload the source code
    # - set source file path
    # - load the module to the global space
    filePath = eval('slicer.modules.%s.path' % moduleName.lower())
    p = os.path.dirname(filePath)
    if not sys.path.__contains__(p):
      sys.path.insert(0,p)
    fp = open(filePath, "r")
    globals()[moduleName] = imp.load_module(
        moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
    fp.close()

    # rebuild the widget
    # - find and hide the existing widget
    # - create a new widget in the existing parent
    # parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent()
    parent = self.parent
    for child in parent.children():
      try:
        child.hide()
      except AttributeError:
        pass
    globals()[widgetName.lower()] = eval(
        'globals()["%s"].%s(parent)' % (moduleName, widgetName))
    globals()[widgetName.lower()].setup()
