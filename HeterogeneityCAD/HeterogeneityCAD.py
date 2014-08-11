from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import vtk.util.numpy_support
import math
import decimal
import operator
import collections
import itertools
from decimal import*

from vtk import vtkShortArray

import StatisticsLib
import MetricWidgetHelperLib


#
# HeterogeneityCAD
#

class HeterogeneityCAD:
  def __init__(self, parent):
    parent.title = "HeterogeneityCAD"
    parent.categories = ["Quantification"]
    parent.dependencies = []
    parent.contributors = ["Vivek Narayan, Jayender Jagadeesan (BWH)"] 
    parent.helpText = """
    This module applies metrics to quantify the heterogeneity of tumor images and their parameter maps. 
    Wiki: http://wiki.slicer.org/slicerWiki/index.php/Documentation/Nightly/Modules/HeterogeneityCAD
    """
    parent.acknowledgementText = """
    This file was originally developed by Vivek Narayan and Jayender Jagadeesan (Brigham and Women's Hospital)
    """
    self.parent = parent
    
    
#
# qHeterogeneityCADWidget
#

class HeterogeneityCADWidget:

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
    
    self.fileDialog = None
    
    # Initialize Data Nodes List
    self.inputDataNodes = []
    
    # Initialize dictionary of containers for descriptive context menus and parameter edit windows
    self.metricContextMenus = {}
    
    # use OrderedDict for class-specific dictionary of function calls
    # map feature class to list of features
    self.featureClassKeys = collections.OrderedDict()
    self.featureClassKeys["First-Order Statistics"] = ["Voxel Count", "Energy", "Entropy" , "Minimum Intensity", "Maximum Intensity", "Mean Intensity", "Median Intensity", "Range", "Mean Deviation", "Root Mean Square",  "Standard Deviation", "Skewness", "Kurtosis", "Variance", "Uniformity"]
    self.featureClassKeys["Morphology and Shape"] = ["Volume mm^3", "Volume cc", "Surface Area mm^2", "Surface:Volume Ratio", "Compactness 1", "Compactness 2", "Maximum 3D Diameter", "Spherical Disproportion", "Sphericity"]  
    self.featureClassKeys["Texture: GLCM"] = ["Autocorrelation", "Cluster Prominence", "Cluster Shade", "Cluster Tendency", "Contrast", "Correlation", "Difference Entropy", "Dissimilarity", "Energy (GLCM)", "Entropy(GLCM)", "Homogeneity 1", "Homogeneity 2", "IMC1", "IDMN", "IDN", "Inverse Variance", "Maximum Probability", "Sum Average", "Sum Entropy", "Sum Variance", "Variance (GLCM)"] #IMC2 missing
    self.featureClassKeys["Texture: GLRL"] = ["SRE", "LRE", "GLN", "RLN", "RP", "LGLRE", "HGLRE", "SRLGLE", "SRHGLE", "LRLGLE", "LRHGLE"]
    self.featureClassKeys["Renyi Dimensions"] = ["Box-Counting Dimension", "Information Dimension", "Correlation Dimension"]
    self.featureClassKeys["Geometrical Measures"] = ["Extruded Surface Area", "Extruded Volume", "Extruded Surface:Volume Ratio"]
    
    # map feature class to list of feature checkbox widgets
    self.featureWidgets = collections.OrderedDict()
    for key in self.featureClassKeys.keys():
      self.featureWidgets[key] = list()   
 
 
  def setup(self):
    
    #Instantiate and Connect Widgets
    
    ############################### Reload Button
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "HeterogeneityCAD Reload"
    self.layout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    ###############################
    
    # Bold font style
    boldFont = qt.QFont()
    boldFont.setBold(True)
    
    #################################################
    #HeterogeneityCAD Inputs Collapsible Button
    #################################################
    self.inputHeterogeneityCADCollapsibleButton = ctk.ctkCollapsibleButton()
    self.inputHeterogeneityCADCollapsibleButton.text = "HeterogeneityCAD Input"
    self.layout.addWidget(self.inputHeterogeneityCADCollapsibleButton)
    self.inputHeterogeneityCADLayout = qt.QFormLayout(self.inputHeterogeneityCADCollapsibleButton)
             
    ##Input Volume as a PET/CT/MRI image or parameter map converted to a volume
    self.inputVolHetFrame = qt.QFrame(self.inputHeterogeneityCADCollapsibleButton)
    self.inputVolHetFrame.setLayout(qt.QHBoxLayout())
    
    self.inputHeterogeneityCADLayout.addRow(self.inputVolHetFrame)     
    # label for selecting individual node
    self.inputVolHet = qt.QLabel("Input Node: ", self.inputVolHetFrame)
    self.inputVolHetFrame.layout().addWidget(self.inputVolHet)    
    # select individual nodes
    self.inputSelectorVolHet = slicer.qMRMLNodeComboBox(self.inputVolHetFrame)
    self.inputSelectorVolHet.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    #self.inputSelectorVolHet.addAttribute( ("vtkMRMLScalarVolumeNode"), "LabelMap", "0")
    self.inputSelectorVolHet.selectNodeUponCreation = False 
    self.inputSelectorVolHet.addEnabled = False
    self.inputSelectorVolHet.removeEnabled = False
    self.inputSelectorVolHet.setMRMLScene( slicer.mrmlScene )
    self.inputVolHetFrame.layout().addWidget(self.inputSelectorVolHet)
    # add Data Node button
    self.addDataNodeButton = qt.QPushButton("Add Node", self.inputVolHetFrame)
    self.addDataNodeButton.objectName = 'AddDataNodeButton'
    self.addDataNodeButton.setToolTip( "Add a Node to Queue" )
    self.addDataNodeButton.connect('clicked()', self.onAddDataNodeButtonClicked)
    self.inputVolHetFrame.layout().addWidget(self.addDataNodeButton)
    
    
    ## data nodes Frame
    self.dataNodesFrame = ctk.ctkCollapsibleGroupBox(self.inputHeterogeneityCADCollapsibleButton)
    self.dataNodesFrame.title = "Nodes List"
    self.dataNodesFrame.collapsed = False
    self.dataNodesFrame.setLayout(qt.QVBoxLayout())    
    # all buttons frame
    self.allButtonsFrame = qt.QFrame(self.inputHeterogeneityCADCollapsibleButton)
    self.allButtonsFrame.objectName = 'AllButtonsFrameButton'
    self.allButtonsFrame.setLayout(qt.QVBoxLayout())
    
    self.inputHeterogeneityCADLayout.addRow(self.dataNodesFrame, self.allButtonsFrame)
    # Data Nodes view
    #Use list view here with scrollarea widget.
    self.dataScrollArea = qt.QScrollArea()  
    self.dataNodesListWidget = qt.QListWidget()
    self.dataNodesListWidget.name = 'dataNodesListWidget'
    self.dataScrollArea.setWidget(self.dataNodesListWidget)
    self.dataNodesListWidget.resize(350,100)
    self.dataNodesFrame.layout().addWidget(self.dataScrollArea)
    #self.listWidget.setProperty('SH_ItemView_ActivateItemOnSingleClick', 1)
    #self.listWidget.connect('activated(QModelIndex)', self.onActivated)       
    # add all Data Nodes from scene button
    self.addAllDataNodesButton = qt.QPushButton("Add All Nodes From Scene", self.allButtonsFrame)
    self.addAllDataNodesButton.objectName = 'AddAllDataNodesButton'
    self.addAllDataNodesButton.setToolTip( "Add all Nodes from the Scene to Queue" )
    self.addAllDataNodesButton.connect('clicked()', self.onAddAllDataNodesButtonClicked)
    self.allButtonsFrame.layout().addWidget(self.addAllDataNodesButton)
    # remove single Data Node
    self.removeDataNodeButton = qt.QPushButton("Remove Node", self.allButtonsFrame)
    self.removeDataNodeButton.objectName = 'RemoveDataNodeButton'
    self.removeDataNodeButton.setToolTip( "Removes Selected Node from the Queue." )
    self.removeDataNodeButton.connect('clicked()', self.onRemoveDataNodeButtonClicked)
    self.allButtonsFrame.layout().addWidget(self.removeDataNodeButton)   
    # remove all Data Nodes button
    self.removeAllDataNodesButton = qt.QPushButton("Remove All Nodes", self.allButtonsFrame)
    self.removeAllDataNodesButton.objectName = 'RemoveAllDataNodesButton'
    self.removeAllDataNodesButton.setToolTip( "Removes All Nodes from the Queue." )
    self.removeAllDataNodesButton.connect('clicked()', self.onRemoveAllDataNodesButtonClicked)
    self.allButtonsFrame.layout().addWidget(self.removeAllDataNodesButton)
    
     
    ##Use Label Map as ROI(segmentation output or user-selected ROI)
    self.inputLabelROIFrame = qt.QFrame(self.inputHeterogeneityCADCollapsibleButton)
    self.inputLabelROIFrame.setLayout(qt.QHBoxLayout())
    
    self.inputHeterogeneityCADLayout.addRow(self.inputLabelROIFrame)
    # Enable Input Label Map as ROI
    self.inputLabelROI = qt.QLabel("Label Map ROI: ", self.inputLabelROIFrame)
    self.inputLabelROIFrame.layout().addWidget(self.inputLabelROI) 
    # Select Input Label Map as ROI
    self.inputSelectorLabel = slicer.qMRMLNodeComboBox(self.inputLabelROIFrame)
    self.inputSelectorLabel.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputSelectorLabel.addAttribute( ("vtkMRMLScalarVolumeNode"), "LabelMap", "1")
    self.inputSelectorLabel.selectNodeUponCreation = False
    self.inputSelectorLabel.renameEnabled = True
    self.inputSelectorLabel.removeEnabled = False 
    self.inputSelectorLabel.noneEnabled = True
    self.inputSelectorLabel.addEnabled = False
    self.inputSelectorLabel.setMRMLScene( slicer.mrmlScene )    
    self.inputLabelROIFrame.layout().addWidget(self.inputSelectorLabel)
    #################################################
    #End HeterogeneityCAD Inputs Collapsible Button
    #################################################

    
    #################################################
    #HeterogeneityCAD Metrics Collapsible Button
    #################################################
    self.HeterogeneityCADCollapsibleButton = ctk.ctkCollapsibleButton()
    self.HeterogeneityCADCollapsibleButton.text = "HeterogeneityCAD Metrics Selection"
    self.layout.addWidget(self.HeterogeneityCADCollapsibleButton)
    self.metricsHeterogeneityCADLayout = qt.QFormLayout(self.HeterogeneityCADCollapsibleButton)
      
    #################################################################################################
    self.tabGroupsHeterogeneityMetrics = MetricWidgetHelperLib.CheckableTabWidget()
    self.metricsHeterogeneityCADLayout.addRow(self.tabGroupsHeterogeneityMetrics)
     
    gridWidth = 3
    gridHeight = 9
    for featureClass in self.featureClassKeys:
      if featureClass == "First-Order Statistics" or featureClass == "Morphology and Shape":
        check = True
      else:
        check = False
    
      tabFeatureClass = qt.QWidget()
      tabFeatureClass.setLayout(qt.QGridLayout())
          
      featureList = (feature for feature in self.featureClassKeys[featureClass])
      gridLayoutCoordinates = ((row,col) for col in range(gridWidth) for row in range(gridHeight))
            
      while True:
        feature = next(featureList, None)
        row, col = next(gridLayoutCoordinates, None)
        if feature is None or row is None or col is None:
          break
        
        description = MetricWidgetHelperLib.MetricDescriptionLabel(feature).getDescription() # migrate to helper
        checkbox = MetricWidgetHelperLib.FeatureWidget()
        
        checkbox.Setup(feature, description, checkStatus=check)
            
        self.featureWidgets[featureClass].append(checkbox)
        tabFeatureClass.layout().addWidget(checkbox, row, col)
             
      self.tabGroupsHeterogeneityMetrics.addTab(tabFeatureClass, featureClass, self.featureWidgets[featureClass], checkStatus=check)
    
    # top-level feature class parameters
    self.tabGroupsHeterogeneityMetrics.addParameter("Geometrical Measures", "Extrusion Parameters")
    self.tabGroupsHeterogeneityMetrics.addParameter("Texture: GLCM", "GLCM Matrix Parameters")
    self.tabGroupsHeterogeneityMetrics.addParameter("Texture: GLRL", "GLRL Matrix Parameters")
    # add capabilities for invidual metric parameters
    
    # note: try using itertools list merging with lists of GLRL diagonal    
    self.heterogeneityMetricWidgets = list(itertools.chain.from_iterable(self.featureWidgets.values())) 
    # or reduce(lambda x,y: x+y, self.featureWidgets.values())

    # Metric Buttons Frame and Layout
    self.metricButtonFrame = qt.QFrame(self.HeterogeneityCADCollapsibleButton)
    self.metricButtonFrame.setLayout(qt.QHBoxLayout())
    
    self.metricsHeterogeneityCADLayout.addRow(self.metricButtonFrame)
       
    ####HeterogeneityCAD Apply Button
    self.HeterogeneityCADButton = qt.QPushButton("Apply HeterogeneityCAD", self.metricButtonFrame)
    self.HeterogeneityCADButton.toolTip = "Analyze input volume using selected Heterogeneity Metrics."
    self.metricButtonFrame.layout().addWidget(self.HeterogeneityCADButton)    
    ####Save Button
    self.saveButton = qt.QPushButton("Save to File", self.metricButtonFrame)
    self.saveButton.toolTip = "Save analyses to CSV file"
    self.saveButton.enabled = False
    self.metricButtonFrame.layout().addWidget(self.saveButton)
    
    #################################################
    #End HeterogeneityCAD Metrics Collapsible Button
    #################################################
    
    
    #############
    #Statistics Chart
    #############
    #Complete chart options, export list of user-selected options identified via connections to labelstatistics module
    self.chartOptions = ("Count", "Volume mm^3", "Volume cc", "Min", "Max", "Mean", "StdDev")
    self.StatisticsChartCollapsibleButton = ctk.ctkCollapsibleButton()
    self.StatisticsChartCollapsibleButton.text = "HeterogeneityCAD Metrics Summary"
    self.layout.addWidget(self.StatisticsChartCollapsibleButton)
    self.StatisticsChartLayout = qt.QFormLayout(self.StatisticsChartCollapsibleButton)
    self.StatisticsChartCollapsibleButton.collapsed = False
    
    #Table View to display Label statistics
    self.view = qt.QTableView(self.StatisticsChartCollapsibleButton)
    self.view.sortingEnabled = True
    self.StatisticsChartLayout.addWidget(self.view)
    self.view.minimumHeight = 175   
    ########
    #End Statistics Chart
    ########
    
        
    ####################
    #Connections
    ####################     
    self.HeterogeneityCADButton.connect('clicked()', self.onHeterogeneityCADButtonClicked)
    self.saveButton.connect('clicked()', self.onSave)
    ####################
    #End Connections
    ####################
  

  ##########LOGIC##########            
  def onAddDataNodeButtonClicked(self):
    self.inputDataNodes.append(self.inputSelectorVolHet.currentNode())
    self.dataNodesListWidget.addItem(self.inputSelectorVolHet.currentNode().GetName())
  
    
  def onAddAllDataNodesButtonClicked(self):
    sceneDataNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLScalarVolumeNode')
    sceneDataNodes.UnRegister(slicer.mrmlScene)
    sceneDataNodes.InitTraversal()
    sceneDataNode = sceneDataNodes.GetNextItemAsObject()
    while sceneDataNode:
      self.inputDataNodes.append(sceneDataNode)
      self.dataNodesListWidget.addItem(sceneDataNode.GetName())
      sceneDataNode = sceneDataNodes.GetNextItemAsObject()
  
      
  def onRemoveDataNodeButtonClicked(self):
    selectedItems = self.dataNodesListWidget.selectedItems()
    for item in selectedItems:
      self.dataNodesListWidget.takeItem(self.dataNodesListWidget.row(item))
      for node in self.inputDataNodes:
        if node.GetName() == item.text():
          self.inputDataNodes.remove(node)
          break
  
    
  def onRemoveAllDataNodesButtonClicked(self):
    self.dataNodesListWidget.clear()
    self.inputDataNodes[:] = []
  
  
  def onHeterogeneityCADButtonClicked(self):
    # raise Warning if label map is not supplied
    self.ROINode = self.inputSelectorLabel.currentNode()
    self.keys = ["Node"] + [str(widget.text) for widget in self.heterogeneityMetricWidgets if widget.checked==True]    
    self.statisticsLogic = []
    
    if (len(self.inputDataNodes) == 0):
      qt.QMessageBox.information(slicer.util.mainWindow(),"HeterogeneityCAD", "Please add data node(s) of class 'vtkMRMLScalarVolumeNode' to the Nodes List")
      return
    if not (self.ROINode):
      qt.QMessageBox.information(slicer.util.mainWindow(),"HeterogeneityCAD", "Please provide a Label Map that specifies a Region-Of-Interest in your image nodes")
      return
    if (len(self.keys) == 0):
      qt.QMessageBox.information(slicer.util.mainWindow(),"HeterogeneityCAD", "Please select at least one metric from the menu to calculate")
      return
    
    for dataNode in self.inputDataNodes:     
      nodeLogic = FeatureExtractionLogic(dataNode, self.ROINode, self.keys)
      self.statisticsLogic.append(nodeLogic)
          
    self.populateStatistics()  
    self.saveButton.enabled = True
    return
  
  
  def populateStatistics(self):
    # move into FeatureExtractionLogic Class
    if not (self.statisticsLogic):
      return
      
    self.items = []
    self.model = qt.QStandardItemModel()
    self.view.setModel(self.model)
    self.view.verticalHeader().visible = False
    row = 0
    col = 0
    
    wholeNumberKeys = ['Voxel Count', 'Minimum Intensity', 'Maximum Intensity', 'Median Intensity', 'Range']
    precisionOnlyKeys = ['Entropy', 'Volume mm^3', 'Volume cc', 'Mean Intensity', 'Mean Deviation', 'Root Mean Square', 'Standard Deviation', 'Surface Area mm^3']
    
    for dataNodeStatistics in self.statisticsLogic:
      col = 0
      
      for k in self.keys:
        item = qt.QStandardItem()
       
        value = dataNodeStatistics.radiomicsSignature[k]
        
        if isinstance(value, basestring):
          metricFormatted = value
        elif isinstance(value, decimal.Decimal):
          metricFormatted = str(value)
        elif k in wholeNumberKeys:
          metricFormatted = int(value)
        elif (k in precisionOnlyKeys) or (abs(value) > .01 and abs(value) < 1000):
          metricFormatted = '{:.2f}'.format(value)
        else:
          metricFormatted = '{:10.4e}'.format(value)
        
        item.setText(str(metricFormatted))
        item.setToolTip(k)
        self.model.setItem(row,col,item)
        self.items.append(item)
        col += 1
      row += 1
    
    self.view.setColumnWidth(0,30)
    self.model.setHeaderData(0,1," ")
    
    col = 0
    for k in self.keys:
      self.view.setColumnWidth(col,15*len(k))
      self.model.setHeaderData(col,1,k)
      col += 1
      
      
  def onSave(self):
    #include default filename as HetergeneityCAD-Date or something
    #make it set the default file name as 
    if not self.fileDialog:
      self.fileDialog = qt.QFileDialog(self.parent)
      self.fileDialog.options = self.fileDialog.DontUseNativeDialog
      self.fileDialog.acceptMode = self.fileDialog.AcceptSave
      self.fileDialog.defaultSuffix = "csv"
      self.fileDialog.setNameFilter("Comma Separated Values (*.csv)")
      self.fileDialog.connect("fileSelected(QString)", self.onFileSelected)
      self.fileDialog.selectFile("HeterogeneityCAD")
    self.fileDialog.show()
  
   
  def onFileSelected(self,fileName):
    self.saveStatistics(fileName)
  
    
  def statisticsAsCSV(self):
  #create array for all metrics
  #supposed to be inside the labelstatistics class
    """print comma separated value file with header keys in quotes"""
    csv = ""
    header = ""
    
    for k in self.keys[:-1]:
      header += "\"%s\"" % k + ","
    header += "\"%s\"" % self.keys[-1] + "\n"
    csv = header
    
    for dataNodeStatistics in self.statisticsLogic:
      line = ""
      for k in self.keys[:-1]:       
        line += str(dataNodeStatistics.radiomicsSignature[k]) + ","
        print (k, dataNodeStatistics.radiomicsSignature[k])  
      line += str(dataNodeStatistics.radiomicsSignature[self.keys[-1]]) + "\n"
      print (line)    
      csv += line
        
    return csv
  
  
  def saveStatistics(self,fileName):
    fp = open(fileName, "w")
    fp.write(self.statisticsAsCSV())
    fp.close()
    
  
  def onReload(self, moduleName="HeterogeneityCAD"):
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


class FeatureExtractionLogic:
 
  def __init__(self, dataNode, labelNode, keys):
    # Initialize Progress Bar
    self.progressBar = qt.QProgressDialog(slicer.util.mainWindow())
    self.progressBar.modal = True
    self.progressBar.minimumDuration = 0
    self.progressBar.show()
    self.progressBar.setValue(0)
    self.progressBar.setMaximum(len(keys))
    self.progressBar.labelText = 'Calculating %s: ' % dataNode.GetName()
    self.step = 0
  
    # Create Numpy Arrays and extract voxel coordinates (ijk) and values from dataNode within the ROI defined by labelNode
    self.nodeArrayVolume = self.createNumpyArray(dataNode)
    self.nodeArrayLabelMapROI = self.createNumpyArray(labelNode)    
    self.targetVoxels, self.targetVoxelsCoordinates = self.voxelValuesAndCoordinates(self.nodeArrayLabelMapROI, self.nodeArrayVolume)   
    
    # Create a padded, rectangular matrix with shape equal to the shape of the tumor 
    ijkMinBounds = numpy.min(self.targetVoxelsCoordinates, 1)
    ijkMaxBounds = numpy.max(self.targetVoxelsCoordinates, 1) 
    self.matrix = numpy.zeros(ijkMaxBounds - ijkMinBounds + 1)
    matrixCoordinates = tuple(map(operator.sub, self.targetVoxelsCoordinates, tuple(ijkMinBounds)))
    self.matrix[matrixCoordinates] = self.targetVoxels
    
    # Get Histogram data
    bins, arrayDiscreteValues, numDiscreteValues = self.getHistogramData(self.targetVoxels)
    
    ### Manage feature classes for Heterogeneity metric calculations     
    # Node Information
    #slicer.app.processEvents()      
    self.step = self.updateProgressBar(self.progressBar, dataNode.GetName(), "Node Information", self.step, 0)         
    self.nodeInformation = StatisticsLib.NodeInformation(dataNode, labelNode, keys).EvaluateFeatures()         

    # First Order Statistics    
    self.step = self.updateProgressBar(self.progressBar, dataNode.GetName(), "First Order Statistics", self.step, len(self.nodeInformation))
    self.distributionStatistics = StatisticsLib.FirstOrderStatistics(self.targetVoxels, bins, keys).EvaluateFeatures()
       
    # Shape/Size and Morphological Features)
    self.step = self.updateProgressBar(self.progressBar, dataNode.GetName(), "Morphology Statistics", self.step, len(self.distributionStatistics))     
    maxDimsSA = tuple(map(operator.add, self.matrix.shape, ([2,2,2]))) # extend padding by one row/column for all 6 directions
    matrixSA, matrixSACoordinates = self.padMatrix(self.matrix, matrixCoordinates, maxDimsSA, self.targetVoxels)   
    self.morphologyStatistics = StatisticsLib.MorphologyStatistics(labelNode, matrixSA, matrixSACoordinates, self.targetVoxels, keys).EvaluateFeatures()
    
    # Renyi Dimensions            
    self.step = self.updateProgressBar(self.progressBar, dataNode.GetName(), "Renyi Dimensions", self.step, len(self.morphologyStatistics))        
    maxDims = tuple( [int(pow(2, math.ceil(numpy.log2(numpy.max(self.matrix.shape)))))] * 3 )
    matrixPadded, matrixPaddedCoordinates = self.padMatrix(self.matrix, matrixCoordinates, maxDims, self.targetVoxels)   
    self.renyiDimensions = StatisticsLib.RenyiDimensions(matrixPadded, matrixPaddedCoordinates, keys).EvaluateFeatures()
               
    # Geometrical Measures
    self.step = self.updateProgressBar(self.progressBar, dataNode.GetName(), "Geometrical Measures", self.step, len(self.renyiDimensions))        
    self.geometricalMeasures = StatisticsLib.GeometricalMeasures(labelNode, self.matrix, matrixCoordinates, self.targetVoxels, keys).EvaluateFeatures()
   
    # Texture Features(GLCM)
    self.step = self.updateProgressBar(self.progressBar, dataNode.GetName(), "GLCM Texture Features", self.step, len(self.geometricalMeasures))    
    self.textureFeaturesGLCM = StatisticsLib.TextureGLCM(arrayDiscreteValues, self.matrix, matrixCoordinates, self.targetVoxels, numDiscreteValues, keys).EvaluateFeatures()
    
    # Texture Features(GLRL)  
    self.step = self.updateProgressBar(self.progressBar, dataNode.GetName(), "GLRL Texture Features", self.step, len(self.textureFeaturesGLCM))
    self.textureFeaturesGLRL = StatisticsLib.TextureGLRL(arrayDiscreteValues, self.matrix, matrixCoordinates, self.targetVoxels, numDiscreteValues, keys).EvaluateFeatures()
        
    # Concatenate all groups of metrics into one 
    self.radiomicsSignature = dict(self.nodeInformation.items() + self.distributionStatistics.items() + self.morphologyStatistics.items() + self.renyiDimensions.items() + self.geometricalMeasures.items() + self.textureFeaturesGLCM.items() + self.textureFeaturesGLRL.items())
    
    self.progressBar.close()
    self.progressBar = None
    
  def createNumpyArray (self, imageNode):
    # Generate Numpy Array from vtkMRMLScalarVolumeNode 
    imageData = vtk.vtkImageData()
    imageData = imageNode.GetImageData()
    shapeData = list(imageData.GetDimensions())
    shapeData.reverse()
    return (vtk.util.numpy_support.vtk_to_numpy(imageData.GetPointData().GetScalars()).reshape(shapeData))
  
  def voxelValuesAndCoordinates(self, arrayROI, arrayDataNode):
    coordinates = numpy.where(arrayROI != 0) # can define specific label values to target or avoid
    values = arrayDataNode[coordinates].astype('int64')
    return(values, coordinates)
    
  def getHistogramData(self, voxelArray):
    # with np.histogram(), all but the last bin is half-open, so make one extra bin container
    binContainers = numpy.arange(voxelArray.min(), voxelArray.max()+2)
    bins = numpy.histogram(voxelArray, bins=binContainers)[0] # frequencies 
    ii = numpy.unique(voxelArray) # discrete gray levels
    grayLevels = ii.size
    return (bins, ii, grayLevels)
    
  def padMatrix(self, a, matrixCoordinates, dims, voxelArray):
    # pads matrix 'a' with zeros and resizes 'a' to a cube with dimensions increased to the next greatest power of 2
    # numpy version 1.7 has numpy.pad function
         
    # center coordinates onto padded matrix  # consider padding with NaN or eps = numpy.spacing(1)
    pad = tuple(map(operator.div, tuple(map(operator.sub, dims, a.shape)), ([2,2,2])))
    matrixCoordinatesPadded = tuple(map(operator.add, matrixCoordinates, pad))
    matrix2 = numpy.zeros(dims)
    matrix2[matrixCoordinatesPadded] = voxelArray
    return (matrix2, matrixCoordinatesPadded)
  
  def updateProgressBar(self, progressBar, nodeName, nextFeatureString, step, previousFeatureStep):
    progressBar.labelText = 'Calculating %s: %s' % (nodeName, nextFeatureString)
    step += previousFeatureStep
    progressBar.setValue(step)
    return (step)
