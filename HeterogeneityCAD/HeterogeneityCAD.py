from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import vtk.util.numpy_support
import math
import decimal
import operator
import collections
import itertools
import FeatureExtractionLib
import FeatureWidgetHelperLib
from decimal import *
from vtk import vtkShortArray

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
    This module applies features to quantify the heterogeneity of tumor images and their parameter maps. 
    Wiki: http://wiki.slicer.org/slicerWiki/index.php/Documentation/Nightly/Modules/HeterogeneityCAD
    """
    parent.acknowledgementText = """
    This file was originally developed by Vivek Narayan and Jayender Jagadeesan (Brigham and Women's Hospital)
    """
    self.parent = parent
    
    #parent.icon = qt.QIcon("%s/ITK.png" % ICON_DIR)
    
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
    
    # use OrderedDict for class-specific dictionary of function calls
    # map feature class to list of features
    self.featureClassKeys = collections.OrderedDict()
    self.featureClassKeys["Node Information"] = ["Node"]
    self.featureClassKeys["First-Order Statistics"] = ["Voxel Count", "Gray Levels", "Energy", "Entropy" , "Minimum Intensity", "Maximum Intensity", "Mean Intensity", "Median Intensity", "Range", "Mean Deviation", "Root Mean Square",  "Standard Deviation", "Skewness", "Kurtosis", "Variance", "Uniformity"]
    self.featureClassKeys["Morphology and Shape"] = ["Volume mm^3", "Volume cc", "Surface Area mm^2", "Surface:Volume Ratio", "Compactness 1", "Compactness 2", "Maximum 3D Diameter", "Spherical Disproportion", "Sphericity"]  
    self.featureClassKeys["Texture: GLCM"] = ["Autocorrelation", "Cluster Prominence", "Cluster Shade", "Cluster Tendency", "Contrast", "Correlation", "Difference Entropy", "Dissimilarity", "Energy (GLCM)", "Entropy(GLCM)", "Homogeneity 1", "Homogeneity 2", "IMC1", "IDMN", "IDN", "Inverse Variance", "Maximum Probability", "Sum Average", "Sum Entropy", "Sum Variance", "Variance (GLCM)"] #IMC2 missing
    self.featureClassKeys["Texture: GLRL"] = ["SRE", "LRE", "GLN", "RLN", "RP", "LGLRE", "HGLRE", "SRLGLE", "SRHGLE", "LRLGLE", "LRHGLE"]   
    self.featureClassKeys["Geometrical Measures"] = ["Extruded Surface Area", "Extruded Volume", "Extruded Surface:Volume Ratio"]
    self.featureClassKeys["Renyi Dimensions"] = ["Box-Counting Dimension", "Information Dimension", "Correlation Dimension"]
    
    # used to map feature class to a list of auto-generated feature checkbox widgets
    self.featureWidgets = collections.OrderedDict()
    for key in self.featureClassKeys.keys():
      self.featureWidgets[key] = list()   
  
  def setup(self):  
    #Instantiate and Connect Widgets 
    #################################################
    #HeterogeneityCAD Inputs Collapsible Button
    
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
    # Use list view here with scroll area widget.
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
        
    # Use Label Map as ROI(segmentation output or user-selected ROI)
    self.inputLabelROIFrame = qt.QFrame(self.inputHeterogeneityCADCollapsibleButton)
    self.inputLabelROIFrame.setLayout(qt.QHBoxLayout())
    self.inputHeterogeneityCADLayout.addRow(self.inputLabelROIFrame)
    # Enable Input Label Map as ROI
    self.inputLabelROI = qt.QLabel("Label Map ROI: ", self.inputLabelROIFrame)
    self.inputLabelROIFrame.layout().addWidget(self.inputLabelROI) 
    # Select Input Label Map as ROI
    self.inputSelectorLabel = slicer.qMRMLNodeComboBox(self.inputLabelROIFrame)
    self.inputSelectorLabel.nodeTypes = ( ("vtkMRMLLabelMapVolumeNode"), "" )
    self.inputSelectorLabel.selectNodeUponCreation = False
    self.inputSelectorLabel.renameEnabled = True
    self.inputSelectorLabel.removeEnabled = False 
    self.inputSelectorLabel.noneEnabled = True
    self.inputSelectorLabel.addEnabled = False
    self.inputSelectorLabel.setMRMLScene( slicer.mrmlScene )    
    self.inputLabelROIFrame.layout().addWidget(self.inputSelectorLabel)

    #End HeterogeneityCAD Inputs Collapsible Button
    #################################################
    #HeterogeneityCAD Features Collapsible Button
    
    self.HeterogeneityCADCollapsibleButton = ctk.ctkCollapsibleButton()
    self.HeterogeneityCADCollapsibleButton.text = "HeterogeneityCAD Features Selection"
    self.layout.addWidget(self.HeterogeneityCADCollapsibleButton)
    self.featuresHeterogeneityCADLayout = qt.QFormLayout(self.HeterogeneityCADCollapsibleButton)

    # auto-generate QTabWidget Tabs and QCheckBoxes (subclassed in FeatureWidgetHelperLib)
    self.tabsFeatureClasses = FeatureWidgetHelperLib.CheckableTabWidget()
    self.featuresHeterogeneityCADLayout.addRow(self.tabsFeatureClasses)
     
    gridWidth, gridHeight = 3, 9
    for featureClass in self.featureClassKeys:    
      # by default, features from the following features classes are checked:
      if featureClass in ["Node Information", "First-Order Statistics", "Morphology and Shape", "Texture: GLCM", "Texture: GLRL"]:
        check = True
      else:
        check = False 
      tabFeatureClass = qt.QWidget()
      tabFeatureClass.setLayout(qt.QGridLayout())         
      #featureList = (feature for feature in self.featureClassKeys[featureClass])
      gridLayoutCoordinates = ((row,col) for col in range(gridWidth) for row in range(gridHeight))
      for featureName in self.featureClassKeys[featureClass]:
        row, col = next(gridLayoutCoordinates, None)
        if featureName is None or row is None or col is None:
          break       
        featureCheckboxWidget = FeatureWidgetHelperLib.FeatureWidget()      
        featureCheckboxWidget.Setup(featureName=featureName, checkStatus=check)
                   
        tabFeatureClass.layout().addWidget(featureCheckboxWidget, row, col)
        self.featureWidgets[featureClass].append(featureCheckboxWidget)       
      self.tabsFeatureClasses.addTab(tabFeatureClass, featureClass, self.featureWidgets[featureClass], checkStatus=check)
      
    self.tabsFeatureClasses.setCurrentIndex(1)
    
    # note: try using itertools list merging with lists of GLRL diagonal    
    self.heterogeneityFeatureWidgets = list(itertools.chain.from_iterable(self.featureWidgets.values()))
    self.classes = list(self.featureWidgets.keys())
    # or reduce(lambda x,y: x+y, self.featureWidgets.values())
    
    ########## Parameter options 
    # add parameters for top-level feature classes
    self.tabsFeatureClasses.addParameter("Geometrical Measures", "Extrusion Parameter 1")
    self.tabsFeatureClasses.addParameter("Texture: GLCM", "GLCM Matrix Parameter 1")
    self.tabsFeatureClasses.addParameter("Texture: GLRL", "GLRL Matrix Parameter 1")
    
    # compile dict of feature classes with parameter names and values
    self.featureClassParametersDict = collections.OrderedDict()
    for featureClassWidget in self.tabsFeatureClasses.getFeatureClassWidgets():      
      featureClassName = featureClassWidget.getName()  
      self.featureClassParametersDict[featureClassName] = collections.OrderedDict()
      self.updateFeatureClassParameterDict(0,featureClassWidget)
      for parameterName in featureClassWidget.widgetMenu.parameters:
        featureClassWidget.getParameterEditWindow(parameterName).connect('intValueChanged(int)', lambda intValue, featureClassWidget=featureClassWidget: self.updateFeatureClassParameterDict(intValue, featureClassWidget))
    
    # add parameters for individual features
    for featureWidget in self.heterogeneityFeatureWidgets:
      if featureWidget.getName() == "Voxel Count":
        featureWidget.addParameter("Example Parameter 1")
        featureWidget.addParameter("Example Parameter 2")
      if featureWidget.getName() == "Gray Levels":
        featureWidget.addParameter("Example Parameter 1-GL")
        featureWidget.addParameter("Example Parameter 2-GL")
    
    # compile dict of features with parameter names and values
    self.featureParametersDict = collections.OrderedDict()
    for featureWidget in self.heterogeneityFeatureWidgets:
      featureName = featureWidget.getName()      
      self.featureParametersDict[featureName] = collections.OrderedDict()
      self.updateFeatureParameterDict(0,featureWidget)
      for parameterName in featureWidget.widgetMenu.parameters:
        featureWidget.getParameterEditWindow(parameterName).connect('intValueChanged(int)', lambda intValue, featureWidget=featureWidget: self.updateFeatureParameterDict(intValue, featureWidget)) #connect intvaluechanged signals to updateParamaterDict function 
    ##########
    
    # Feature Buttons Frame and Layout
    self.featureButtonFrame = qt.QFrame(self.HeterogeneityCADCollapsibleButton)
    self.featureButtonFrame.setLayout(qt.QHBoxLayout()) 
    self.featuresHeterogeneityCADLayout.addRow(self.featureButtonFrame)
       
    # HeterogeneityCAD Apply Button
    self.HeterogeneityCADButton = qt.QPushButton("Apply HeterogeneityCAD", self.featureButtonFrame)
    self.HeterogeneityCADButton.toolTip = "Analyze input volume using selected Heterogeneity Features."
    self.featureButtonFrame.layout().addWidget(self.HeterogeneityCADButton)
    self.HeterogeneityCADButton.connect('clicked()', self.onHeterogeneityCADButtonClicked)
        
    # Save Button
    self.saveButton = qt.QPushButton("Save to File", self.featureButtonFrame)
    self.saveButton.toolTip = "Save analyses to CSV file"
    self.saveButton.enabled = False
    self.featureButtonFrame.layout().addWidget(self.saveButton)
    self.saveButton.connect('clicked()', self.onSave)
    
    #End HeterogeneityCAD Features Collapsible Button
    #################################################
    #Feature Summary Chart

    #Complete chart options, export list of user-selected options identified via connections to labelstatistics module
    self.chartOptions = ("Count", "Volume mm^3", "Volume cc", "Min", "Max", "Mean", "StdDev")
    self.StatisticsChartCollapsibleButton = ctk.ctkCollapsibleButton()
    self.StatisticsChartCollapsibleButton.text = "HeterogeneityCAD Features Summary"
    self.layout.addWidget(self.StatisticsChartCollapsibleButton)
    self.StatisticsChartLayout = qt.QFormLayout(self.StatisticsChartCollapsibleButton)
    self.StatisticsChartCollapsibleButton.collapsed = False
    
    #Table View to display Label statistics
    self.view = qt.QTableView(self.StatisticsChartCollapsibleButton)
    self.view.sortingEnabled = True
    self.StatisticsChartLayout.addWidget(self.view)
    self.view.minimumHeight = 175   

    #End Statistics Chart
    #################################################
    
  def updateFeatureParameterDict(self, intValue, featureWidget):
    featureName = featureWidget.getName() 
    self.featureParametersDict[featureName].update(featureWidget.getParameterDict())
    
  def updateFeatureClassParameterDict(self, intValue, featureClassWidget):
    featureClassName = featureClassWidget.getName() 
    self.featureClassParametersDict[featureClassName].update(featureClassWidget.getParameterDict())
    print self.featureClassParametersDict
             
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
    # self.inputDataNodes contains the input node names in 'Nodes List'
    self.labelNode = self.inputSelectorLabel.currentNode()
    
    self.featureKeys = []
    self.featureClassKeys = set() # no duplicate keys allowed in set()
    
    # initialize a list of feature vectors (one for each input node-ROI node pair)
    # a feature vector is a dictionary object with features as keys and feature values as values 
    self.FeatureVectors = []
    
    # build list of features and feature classes based on what is checked by the user
    for featureClass in self.featureWidgets:
      for widget in self.featureWidgets[featureClass]:
        if widget.checked==True:
          self.featureKeys.append(str(widget.text))
          self.featureClassKeys.add(featureClass)
               
    if (len(self.inputDataNodes) == 0):
      qt.QMessageBox.information(slicer.util.mainWindow(),"HeterogeneityCAD", "Please add data node(s) of class 'vtkMRMLScalarVolumeNode' to the Nodes List")
      return
    if not (self.labelNode):
      qt.QMessageBox.information(slicer.util.mainWindow(),"HeterogeneityCAD", "Please provide a Label Map that specifies a Region-Of-Interest in your image nodes")
      return
    if (len(self.featureKeys) == 0):
      qt.QMessageBox.information(slicer.util.mainWindow(),"HeterogeneityCAD", "Please select at least one feature from the menu to calculate")
      return
    
    for dataNode in self.inputDataNodes:     
      nodeLogic = FeatureExtractionLogic(dataNode, self.labelNode, self.featureParametersDict, self.featureClassParametersDict, self.featureKeys)
      self.FeatureVectors.append(nodeLogic.getFeatureVector())
           
    self.populateStatistics(self.FeatureVectors)  
    self.saveButton.enabled = True
    return
    
  def populateStatistics(self, FeatureVectors):
    if not (FeatureVectors):
      return
      
    self.items = []
    self.model = qt.QStandardItemModel()
    self.view.setModel(self.model)
    self.view.verticalHeader().visible = False
    row = 0
    col = 0
    
    wholeNumberKeys = ['Voxel Count', 'Gray Levels', 'Minimum Intensity', 'Maximum Intensity', 'Median Intensity', 'Range']
    precisionOnlyKeys = ['Entropy', 'Volume mm^3', 'Volume cc', 'Mean Intensity', 'Mean Deviation', 'Root Mean Square', 'Standard Deviation', 'Surface Area mm^3']
    
    for featureVector in FeatureVectors:
      col = 0    
      for feature in featureVector:
        item = qt.QStandardItem()   
        value = featureVector[feature]       
        featureFormatted = value
        # add formatting here
        item.setText(str(featureFormatted))
        item.setToolTip(feature)
        self.model.setItem(row,col,item)
        self.items.append(item)
        col += 1
      row += 1
    
    self.view.setColumnWidth(0,30)
    self.model.setHeaderData(0,1," ")
    
    # set table headers
    col = 0
    for feature in FeatureVectors[0]:
      self.view.setColumnWidth(col,15*len(feature))
      self.model.setHeaderData(col,1,feature)
      col += 1
             
  def onSave(self):
    # todo: include a default filename such as HetergeneityCAD-Date
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
  # create array for all features
  # needs a list of Feature Vectors 
  # print comma separated value file with header keys in quotes
    csv = ""
    header = ""
    
    for feature in self.FeatureVectors[0].keys()[:-1]:
      header += "\"%s\"" % feature + ","
    header += "\"%s\"" % self.FeatureVectors[0].keys()[-1] + "\n"
    csv = header
    
    for featureVector in self.FeatureVectors:
      line = ""
      for feature in featureVector.keys()[:-1]:
        value = featureVector[feature]      
        line += str(value) + ","
        print (value, 'sfd')
      
      endingFeature = featureVector.keys()[-1]   
      line += str(featureVector[endingFeature]) + "\n"
      print (line)    
      csv += line
        
    return csv
    
  def saveStatistics(self,fileName):
    fp = open(fileName, "w")
    fp.write(self.statisticsAsCSV())
    fp.close()
      
class FeatureExtractionLogic:
  def __init__(self, dataNode, labelNode, featureParameterDict, featureClassParametersDict, keys):
    self.dataNode = dataNode
    self.labelNode = labelNode
    self.featureParameterDict = featureParameterDict # ( keys=featureNames,values=dict(keys=parameterNames,values=parameterValues) )
    self.featureClassParametersDict = featureClassParametersDict# ( keys=featureClassNames,values=dict(keys=parameterNames,values=parameterValues) )
    self.keys = keys
  
    # initialize Progress Bar
    self.progressBar = qt.QProgressDialog(slicer.util.mainWindow())
    self.progressBar.minimumDuration = 0
    self.progressBar.show()
    self.progressBar.setValue(0)
    self.progressBar.setMaximum(len(self.keys))
    self.progressBar.labelText = 'Calculating for %s: ' % self.dataNode.GetName()
  
    # create Numpy Arrays 
    self.nodeArrayVolume = self.createNumpyArray(self.dataNode)
    self.nodeArrayLabelMapROI = self.createNumpyArray(self.labelNode)
    
    # extract voxel coordinates (ijk) and values from self.dataNode within the ROI defined by self.labelNode
    self.targetVoxels, self.targetVoxelsCoordinates = self.tumorVoxelsAndCoordinates(self.nodeArrayLabelMapROI, self.nodeArrayVolume)   
    
    # create a padded, rectangular matrix with shape equal to the shape of the tumor
    self.matrix, self.matrixCoordinates = self.paddedTumorMatrixAndCoordinates(self.targetVoxels, self.targetVoxelsCoordinates) 
    
    # get Histogram data
    self.bins, self.grayLevels, self.numGrayLevels = self.getHistogramData(self.targetVoxels)
    
    ########
    # Manage feature classes for Heterogeneity feature calculations and consolidate into self.FeatureVector
    # TODO: create a parent class for all feature classes
    self.FeatureVector = collections.OrderedDict()
        
    # Node Information     
    self.updateProgressBar(self.progressBar, self.dataNode.GetName(), "Node Information", len(self.FeatureVector))         
    self.nodeInformation = FeatureExtractionLib.NodeInformation(self.dataNode, self.labelNode, self.keys)
    self.FeatureVector.update( self.nodeInformation.EvaluateFeatures() )         

    # First Order Statistics    
    self.updateProgressBar(self.progressBar, self.dataNode.GetName(), "First Order Statistics", len(self.FeatureVector))
    self.firstOrderStatistics = FeatureExtractionLib.FirstOrderStatistics(self.targetVoxels, self.bins, self.numGrayLevels, self.keys)
    self.FeatureVector.update( self.firstOrderStatistics.EvaluateFeatures() )
      
    # Shape/Size and Morphological Features)
    self.updateProgressBar(self.progressBar, self.dataNode.GetName(), "Morphology Statistics", len(self.FeatureVector))   
    # extend padding by one row/column for all 6 directions
    maxDimsSA = tuple(map(operator.add, self.matrix.shape, ([2,2,2]))) 
    matrixSA, matrixSACoordinates = self.padMatrix(self.matrix, self.matrixCoordinates, maxDimsSA, self.targetVoxels)      
    self.morphologyStatistics = FeatureExtractionLib.MorphologyStatistics(self.labelNode, matrixSA, matrixSACoordinates, self.targetVoxels, self.keys)
    self.FeatureVector.update( self.morphologyStatistics.EvaluateFeatures() )
     
     # Texture Features(GLCM)
    self.updateProgressBar(self.progressBar, self.dataNode.GetName(), "GLCM Texture Features", len(self.FeatureVector))    
    self.textureFeaturesGLCM = FeatureExtractionLib.TextureGLCM(self.grayLevels, self.numGrayLevels, self.matrix, self.matrixCoordinates, self.targetVoxels, self.keys)
    self.FeatureVector.update( self.textureFeaturesGLCM.EvaluateFeatures() )
      
    # Texture Features(GLRL)  
    self.updateProgressBar(self.progressBar, self.dataNode.GetName(), "GLRL Texture Features", len(self.FeatureVector))
    self.textureFeaturesGLRL = FeatureExtractionLib.TextureGLRL(self.grayLevels, self.numGrayLevels, self.matrix, self.matrixCoordinates, self.targetVoxels, self.keys)
    self.FeatureVector.update( self.textureFeaturesGLRL.EvaluateFeatures() )
     
    # Geometrical Measures    
    # TODO: progress bar does not update to Geometrical Measures while calculating (create separate thread?)
    self.updateProgressBar(self.progressBar, self.dataNode.GetName(), "Geometrical Measures", len(self.FeatureVector))      
    self.geometricalMeasures = FeatureExtractionLib.GeometricalMeasures(self.labelNode, self.matrix, self.matrixCoordinates, self.targetVoxels, self.keys)
    self.FeatureVector.update( self.geometricalMeasures.EvaluateFeatures() )
     
    # Renyi Dimensions            
    self.updateProgressBar(self.progressBar, self.dataNode.GetName(), "Renyi Dimensions", len(self.FeatureVector))   
    # extend padding to dimension lengths equal to next power of 2
    maxDims = tuple( [int(pow(2, math.ceil(numpy.log2(numpy.max(self.matrix.shape)))))] * 3 ) 
    matrixPadded, matrixPaddedCoordinates = self.padMatrix(self.matrix, self.matrixCoordinates, maxDims, self.targetVoxels)      
    self.renyiDimensions = FeatureExtractionLib.RenyiDimensions(matrixPadded, matrixPaddedCoordinates, self.keys)
    self.FeatureVector.update( self.renyiDimensions.EvaluateFeatures() )
    
    # close progress bar
    self.updateProgressBar(self.progressBar, self.dataNode.GetName(), "Populating Summary Table", len(self.FeatureVector))
    self.progressBar.close()
    self.progressBar = None
    
    # filter for user-queried features only
    self.FeatureVector = collections.OrderedDict((k, self.FeatureVector[k]) for k in self.keys) 
    
  def createNumpyArray (self, imageNode):
    # Generate Numpy Array from vtkMRMLScalarVolumeNode 
    imageData = vtk.vtkImageData()
    imageData = imageNode.GetImageData()
    shapeData = list(imageData.GetDimensions())
    shapeData.reverse()
    return (vtk.util.numpy_support.vtk_to_numpy(imageData.GetPointData().GetScalars()).reshape(shapeData))
  
  def tumorVoxelsAndCoordinates(self, arrayROI, arrayDataNode):
    coordinates = numpy.where(arrayROI != 0) # can define specific label values to target or avoid
    values = arrayDataNode[coordinates].astype('int64')
    return(values, coordinates)
    
  def paddedTumorMatrixAndCoordinates(self, targetVoxels, targetVoxelsCoordinates):
    ijkMinBounds = numpy.min(targetVoxelsCoordinates, 1)
    ijkMaxBounds = numpy.max(targetVoxelsCoordinates, 1) 
    matrix = numpy.zeros(ijkMaxBounds - ijkMinBounds + 1)
    matrixCoordinates = tuple(map(operator.sub, targetVoxelsCoordinates, tuple(ijkMinBounds)))
    matrix[matrixCoordinates] = targetVoxels
    return(matrix, matrixCoordinates)
    
  def getHistogramData(self, voxelArray):
    # with np.histogram(), all but the last bin is half-open, so make one extra bin container
    binContainers = numpy.arange(voxelArray.min(), voxelArray.max()+2)
    bins = numpy.histogram(voxelArray, bins=binContainers)[0] # frequencies 
    grayLevels = numpy.unique(voxelArray) # discrete gray levels
    numGrayLevels = grayLevels.size
    return (bins, grayLevels, numGrayLevels)
    
  def padMatrix(self, a, matrixCoordinates, dims, voxelArray):
    # pads matrix 'a' with zeros and resizes 'a' to a cube with dimensions increased to the next greatest power of 2
    # numpy version 1.7 has numpy.pad function
         
    # center coordinates onto padded matrix  # consider padding with NaN or eps = numpy.spacing(1)
    pad = tuple(map(operator.div, tuple(map(operator.sub, dims, a.shape)), ([2,2,2])))
    matrixCoordinatesPadded = tuple(map(operator.add, matrixCoordinates, pad))
    matrix2 = numpy.zeros(dims)
    matrix2[matrixCoordinatesPadded] = voxelArray
    return (matrix2, matrixCoordinatesPadded)
  
  def updateProgressBar(self, progressBar, nodeName, nextFeatureString, totalSteps):
    slicer.app.processEvents()
    progressBar.labelText = 'Calculating %s: %s' % (nodeName, nextFeatureString)
    progressBar.setValue(totalSteps)
           
  def getFeatureVector(self):
    return (self.FeatureVector)
    
