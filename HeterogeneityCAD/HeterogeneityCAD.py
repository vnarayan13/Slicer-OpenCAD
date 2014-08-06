from __main__ import vtk, qt, ctk, slicer
import string
import numpy
import vtk.util.numpy_support
import math
import decimal
import operator
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
    
    
  def setup(self):
    
    #Instantiate and Connect Widgets
    
    ############################### Reload Button
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "HeterogeneityCAD Reload"
    self.layout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    ###############################
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
  
    self.tabGroupsHeterogeneityMetrics = qt.QTabWidget()
    self.metricsHeterogeneityCADLayout.addRow(self.tabGroupsHeterogeneityMetrics)
       
    ###First Order Statistics Tab
    self.firstOrderHeterogeneityMetrics = []
    self.tabFirstOrderStatistics = qt.QWidget()
    self.LayoutMetricFirstOrderStatistics = qt.QGridLayout()
    self.tabFirstOrderStatistics.setLayout(self.LayoutMetricFirstOrderStatistics)
    self.tabGroupsHeterogeneityMetrics.addTab(self.tabFirstOrderStatistics, "First-Order Statistics")
    
    self.HeterogeneityMetricFirstOrder1 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder1.setText('Voxel Count')
    self.HeterogeneityMetricFirstOrder1.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder1)
     
    self.HeterogeneityMetricFirstOrder2 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder2.setText('Energy')
    self.HeterogeneityMetricFirstOrder2.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder2)

    self.HeterogeneityMetricFirstOrder3 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder3.setText('Entropy')
    self.HeterogeneityMetricFirstOrder3.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder3)  

    self.HeterogeneityMetricFirstOrder4 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder4.setText('Minimum Intensity')
    self.HeterogeneityMetricFirstOrder4.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder4)

    self.HeterogeneityMetricFirstOrder5 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder5.setText('Maximum Intensity')
    self.HeterogeneityMetricFirstOrder5.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder5)

    self.HeterogeneityMetricFirstOrder6 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder6.setText('Mean Intensity')
    self.HeterogeneityMetricFirstOrder6.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder6)

    self.HeterogeneityMetricFirstOrder7 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder7.setText('Median Intensity')
    self.HeterogeneityMetricFirstOrder7.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder7)

    self.HeterogeneityMetricFirstOrder8 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder8.setText('Range')
    self.HeterogeneityMetricFirstOrder8.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder8)

    self.HeterogeneityMetricFirstOrder9 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder9.setText('Mean Deviation')
    self.HeterogeneityMetricFirstOrder9.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder9)

    self.HeterogeneityMetricFirstOrder10 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder10.setText('Root Mean Square')
    self.HeterogeneityMetricFirstOrder10.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder10)
   
    self.HeterogeneityMetricFirstOrder11 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder11.setText('Standard Deviation')
    self.HeterogeneityMetricFirstOrder11.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder11)

    self.HeterogeneityMetricFirstOrder12 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder12.setText('Skewness')
    self.HeterogeneityMetricFirstOrder12.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder12)

    self.HeterogeneityMetricFirstOrder13 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder13.setText('Kurtosis')
    self.HeterogeneityMetricFirstOrder13.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder13)

    self.HeterogeneityMetricFirstOrder14 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder14.setText('Variance')
    self.HeterogeneityMetricFirstOrder14.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder14)

    self.HeterogeneityMetricFirstOrder15 = qt.QCheckBox()  
    self.HeterogeneityMetricFirstOrder15.setText('Uniformity')
    self.HeterogeneityMetricFirstOrder15.checked = True
    self.firstOrderHeterogeneityMetrics.append(self.HeterogeneityMetricFirstOrder15)
 
    
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder1, 0, 0)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder2, 0, 1)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder3, 0, 2)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder4, 1, 0)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder5, 1, 1)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder6, 1, 2)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder7, 2, 0)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder8, 2, 1)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder9, 2, 2)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder10, 3, 0)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder11, 3, 1)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder12, 3, 2)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder13, 4, 0)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder14, 4, 1)
    self.LayoutMetricFirstOrderStatistics.addWidget(self.HeterogeneityMetricFirstOrder15, 4, 2)        
    ####
       
    ####Morphological Statistics Tab
    self.morphologicalHeterogeneityMetrics = []
    self.LayoutMetricMorphologicalStatisticsDimensions = qt.QGridLayout()
    self.tabMorphologicalStatistics = qt.QWidget()
    self.tabMorphologicalStatistics.setLayout(self.LayoutMetricMorphologicalStatisticsDimensions)
    self.tabGroupsHeterogeneityMetrics.addTab(self.tabMorphologicalStatistics, "Morphology and Shape")
    
    self.HeterogeneityMetricMorphologicalStatistics1 = qt.QCheckBox()  
    self.HeterogeneityMetricMorphologicalStatistics1.setText('Volume mm^3')
    self.HeterogeneityMetricMorphologicalStatistics1.checked = True
    self.morphologicalHeterogeneityMetrics.append(self.HeterogeneityMetricMorphologicalStatistics1)
    
    self.HeterogeneityMetricMorphologicalStatistics2 = qt.QCheckBox()  
    self.HeterogeneityMetricMorphologicalStatistics2.setText('Volume cc')
    self.HeterogeneityMetricMorphologicalStatistics2.checked = True
    self.morphologicalHeterogeneityMetrics.append(self.HeterogeneityMetricMorphologicalStatistics2)
    
    self.HeterogeneityMetricMorphologicalStatistics3 = qt.QCheckBox()  
    self.HeterogeneityMetricMorphologicalStatistics3.setText('Surface Area mm^2')
    self.HeterogeneityMetricMorphologicalStatistics3.checked = True
    self.morphologicalHeterogeneityMetrics.append(self.HeterogeneityMetricMorphologicalStatistics3)
    
    self.HeterogeneityMetricMorphologicalStatistics4 = qt.QCheckBox()  
    self.HeterogeneityMetricMorphologicalStatistics4.setText('Surface:Volume Ratio')
    self.HeterogeneityMetricMorphologicalStatistics4.checked = True
    self.morphologicalHeterogeneityMetrics.append(self.HeterogeneityMetricMorphologicalStatistics4)

    self.HeterogeneityMetricMorphologicalStatistics5 = qt.QCheckBox()  
    self.HeterogeneityMetricMorphologicalStatistics5.setText('Compactness 1')
    self.HeterogeneityMetricMorphologicalStatistics5.checked = True
    self.morphologicalHeterogeneityMetrics.append(self.HeterogeneityMetricMorphologicalStatistics5)
    
    self.HeterogeneityMetricMorphologicalStatistics6 = qt.QCheckBox()  
    self.HeterogeneityMetricMorphologicalStatistics6.setText('Compactness 2')
    self.HeterogeneityMetricMorphologicalStatistics6.checked = True
    self.morphologicalHeterogeneityMetrics.append(self.HeterogeneityMetricMorphologicalStatistics6)
    
    self.HeterogeneityMetricMorphologicalStatistics7 = qt.QCheckBox()  
    self.HeterogeneityMetricMorphologicalStatistics7.setText('Maximum 3D Diameter')
    self.HeterogeneityMetricMorphologicalStatistics7.checked = True
    self.morphologicalHeterogeneityMetrics.append(self.HeterogeneityMetricMorphologicalStatistics7)
    
    self.HeterogeneityMetricMorphologicalStatistics8 = qt.QCheckBox()  
    self.HeterogeneityMetricMorphologicalStatistics8.setText('Spherical Disproportion')
    self.HeterogeneityMetricMorphologicalStatistics8.checked = True
    self.morphologicalHeterogeneityMetrics.append(self.HeterogeneityMetricMorphologicalStatistics8)
    
    self.HeterogeneityMetricMorphologicalStatistics9 = qt.QCheckBox()  
    self.HeterogeneityMetricMorphologicalStatistics9.setText('Sphericity')
    self.HeterogeneityMetricMorphologicalStatistics9.checked = True
    self.morphologicalHeterogeneityMetrics.append(self.HeterogeneityMetricMorphologicalStatistics9)
      
   
    self.LayoutMetricMorphologicalStatisticsDimensions.addWidget(self.HeterogeneityMetricMorphologicalStatistics1,0,0)
    self.LayoutMetricMorphologicalStatisticsDimensions.addWidget(self.HeterogeneityMetricMorphologicalStatistics2,0,1)
    self.LayoutMetricMorphologicalStatisticsDimensions.addWidget(self.HeterogeneityMetricMorphologicalStatistics3,0,2)
    self.LayoutMetricMorphologicalStatisticsDimensions.addWidget(self.HeterogeneityMetricMorphologicalStatistics4,1,0)
    self.LayoutMetricMorphologicalStatisticsDimensions.addWidget(self.HeterogeneityMetricMorphologicalStatistics5,1,1)
    self.LayoutMetricMorphologicalStatisticsDimensions.addWidget(self.HeterogeneityMetricMorphologicalStatistics6,1,2)
    self.LayoutMetricMorphologicalStatisticsDimensions.addWidget(self.HeterogeneityMetricMorphologicalStatistics7,2,0)
    self.LayoutMetricMorphologicalStatisticsDimensions.addWidget(self.HeterogeneityMetricMorphologicalStatistics8,2,1)
    self.LayoutMetricMorphologicalStatisticsDimensions.addWidget(self.HeterogeneityMetricMorphologicalStatistics9,2,2)
    ####

   
    ####Renyi Dimensions Tab
    self.renyiHeterogeneityMetrics = []
    self.LayoutMetricRenyiDimensions = qt.QGridLayout()
    self.tabRenyiDimensions = qt.QWidget()
    self.tabRenyiDimensions.setLayout(self.LayoutMetricRenyiDimensions)
    self.tabGroupsHeterogeneityMetrics.addTab(self.tabRenyiDimensions, "Renyi Dimensions")
    
    self.HeterogeneityMetricRenyi1 = qt.QCheckBox()  
    self.HeterogeneityMetricRenyi1.setText('Box-Counting Dimension')
    self.HeterogeneityMetricRenyi1.checked = True
    self.renyiHeterogeneityMetrics.append(self.HeterogeneityMetricRenyi1)
    
    self.HeterogeneityMetricRenyi2 = qt.QCheckBox()  
    self.HeterogeneityMetricRenyi2.setText('Information Dimension')
    self.HeterogeneityMetricRenyi2.checked = True
    self.renyiHeterogeneityMetrics.append(self.HeterogeneityMetricRenyi2)
    
    self.HeterogeneityMetricRenyi3 = qt.QCheckBox()  
    self.HeterogeneityMetricRenyi3.setText('Correlation Dimension')
    self.HeterogeneityMetricRenyi3.checked = True
    self.renyiHeterogeneityMetrics.append(self.HeterogeneityMetricRenyi3)
  
   
    self.LayoutMetricRenyiDimensions.addWidget(self.HeterogeneityMetricRenyi1,0,0)
    self.LayoutMetricRenyiDimensions.addWidget(self.HeterogeneityMetricRenyi2,0,1)
    self.LayoutMetricRenyiDimensions.addWidget(self.HeterogeneityMetricRenyi3,1,0)
    ####
    
    ####Geometrical Measures Tab
    self.geometricalHeterogeneityMetrics = []
    self.LayoutMetricGeometricalMeasures = qt.QGridLayout()
    self.tabGeometricalMeasures = qt.QWidget()
    self.tabGeometricalMeasures.setLayout(self.LayoutMetricGeometricalMeasures)
    self.tabGroupsHeterogeneityMetrics.addTab(self.tabGeometricalMeasures, "Geometrical Measures")
    
    #
    self.HeterogeneityMetricGeometricalExtrusion = qt.QCheckBox()
    self.HeterogeneityMetricGeometricalExtrusion.setFont(boldFont)
    self.HeterogeneityMetricGeometricalExtrusion.setText('Generate 4D Extruded Object')
    self.HeterogeneityMetricGeometricalExtrusion.checked = True
    #
    
    self.HeterogeneityMetricGeometrical1 = qt.QCheckBox()  
    self.HeterogeneityMetricGeometrical1.setText('Extruded Surface Area')
    self.HeterogeneityMetricGeometrical1.checked = True
    self.geometricalHeterogeneityMetrics.append(self.HeterogeneityMetricGeometrical1)
    
    self.HeterogeneityMetricGeometrical2 = qt.QCheckBox()  
    self.HeterogeneityMetricGeometrical2.setText('Extruded Volume')
    self.HeterogeneityMetricGeometrical2.checked = True
    self.geometricalHeterogeneityMetrics.append(self.HeterogeneityMetricGeometrical2)
    
    self.HeterogeneityMetricGeometrical3 = qt.QCheckBox()  
    self.HeterogeneityMetricGeometrical3.setText('Extruded Surface:Volume Ratio')
    self.HeterogeneityMetricGeometrical3.checked = True
    self.geometricalHeterogeneityMetrics.append(self.HeterogeneityMetricGeometrical3)
    
    self.LayoutMetricGeometricalMeasures.addWidget(self.HeterogeneityMetricGeometricalExtrusion,0,0)   
    self.LayoutMetricGeometricalMeasures.addWidget(self.HeterogeneityMetricGeometrical1,1,0)
    self.LayoutMetricGeometricalMeasures.addWidget(self.HeterogeneityMetricGeometrical2,1,1)
    self.LayoutMetricGeometricalMeasures.addWidget(self.HeterogeneityMetricGeometrical3,2,0)
    ####
    
    
    #### Texture-GLCM Tab
    self.textureGLCMHeterogeneityMetrics = []
    self.LayoutMetricGLCM = qt.QGridLayout()
    self.tabGLCM = qt.QWidget()
    self.tabGLCM.setLayout(self.LayoutMetricGLCM)
    self.tabGroupsHeterogeneityMetrics.addTab(self.tabGLCM, "Texture: GLCM")
    
    #
    self.HeterogeneityMetricGLCMMatrix = qt.QCheckBox()  
    self.HeterogeneityMetricGLCMMatrix.setFont(boldFont)
    self.HeterogeneityMetricGLCMMatrix.setText('Generate Gray-Level Co-occurrence Matrix')   
    self.HeterogeneityMetricGLCMMatrix.checked = True
    #
    
    self.HeterogeneityMetricGLCM1 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM1.setText('Autocorrelation')
    self.HeterogeneityMetricGLCM1.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM1)
    
    self.HeterogeneityMetricGLCM2 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM2.setText('Cluster Prominence')
    self.HeterogeneityMetricGLCM2.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM2)
    
    self.HeterogeneityMetricGLCM3 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM3.setText('Cluster Shade')
    self.HeterogeneityMetricGLCM3.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM3)
    
    self.HeterogeneityMetricGLCM4 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM4.setText('Cluster Tendency')
    self.HeterogeneityMetricGLCM4.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM4)
    
    self.HeterogeneityMetricGLCM5 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM5.setText('Contrast')
    self.HeterogeneityMetricGLCM5.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM5)
    
    self.HeterogeneityMetricGLCM6 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM6.setText('Correlation')
    self.HeterogeneityMetricGLCM6.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM6)
    
    self.HeterogeneityMetricGLCM7 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM7.setText('Difference Entropy')
    self.HeterogeneityMetricGLCM7.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM7)
    
    self.HeterogeneityMetricGLCM8 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM8.setText('Dissimilarity')
    self.HeterogeneityMetricGLCM8.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM8)
    
    self.HeterogeneityMetricGLCM9 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM9.setText('Energy (GLCM)')
    self.HeterogeneityMetricGLCM9.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM9)
    
    self.HeterogeneityMetricGLCM10 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM10.setText('Entropy(GLCM)')
    self.HeterogeneityMetricGLCM10.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM10)
    
    self.HeterogeneityMetricGLCM11 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM11.setText('Homogeneity 1')
    self.HeterogeneityMetricGLCM11.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM11)
    
    self.HeterogeneityMetricGLCM12 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM12.setText('Homogeneity 2')
    self.HeterogeneityMetricGLCM12.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM12)
    
    self.HeterogeneityMetricGLCM13 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM13.setText('IMC1')
    self.HeterogeneityMetricGLCM13.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM13)
    self.HeterogeneityMetricGLCM13.setToolTip('Informational Measure of Correlation 1 (IMC1)')
    
    # disabled, error in calculations
    self.HeterogeneityMetricGLCM14 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM14.setText('IMC2')
    self.HeterogeneityMetricGLCM14.checked = False #True
    self.HeterogeneityMetricGLCM14.enabled = False
    #self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM14)
    self.HeterogeneityMetricGLCM14.setToolTip('Informational Measure of Correlation 2 (IMC2)')
  
    self.HeterogeneityMetricGLCM15 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM15.setText('IDMN') 
    self.HeterogeneityMetricGLCM15.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM15)
    self.HeterogeneityMetricGLCM15.setToolTip('Inverse Difference Moment Normalized (IDMN)')

    self.HeterogeneityMetricGLCM16 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM16.setText('IDN')    
    self.HeterogeneityMetricGLCM16.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM16)
    self.HeterogeneityMetricGLCM16.setToolTip('Inverse Difference Normalized (IDN)')
 
    self.HeterogeneityMetricGLCM17 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM17.setText('Inverse Variance')
    self.HeterogeneityMetricGLCM17.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM17)
    
    self.HeterogeneityMetricGLCM18 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM18.setText('Maximum Probability')
    self.HeterogeneityMetricGLCM18.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM18)
    
    self.HeterogeneityMetricGLCM19 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM19.setText('Sum Average')
    self.HeterogeneityMetricGLCM19.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM19)
    
    self.HeterogeneityMetricGLCM20 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM20.setText('Sum Entropy')
    self.HeterogeneityMetricGLCM20.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM20)
    
    self.HeterogeneityMetricGLCM21 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM21.setText('Sum Variance')
    self.HeterogeneityMetricGLCM21.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM21)
    
    self.HeterogeneityMetricGLCM22 = qt.QCheckBox()  
    self.HeterogeneityMetricGLCM22.setText('Variance (GLCM)')
    self.HeterogeneityMetricGLCM22.checked = True
    self.textureGLCMHeterogeneityMetrics.append(self.HeterogeneityMetricGLCM22)
    
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCMMatrix, 0, 0)
    
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM1, 1, 0)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM2, 1, 1)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM3, 1, 2)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM4, 2, 0)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM5, 2, 1)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM6, 2, 2)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM7, 3, 0)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM8, 3, 1)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM9, 3, 2)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM10, 4, 0)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM11, 4, 1)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM12, 4, 2)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM13, 5, 0)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM14, 5, 1)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM15, 5, 2)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM16, 6, 0)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM17, 6, 1)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM18, 6, 2)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM19, 7, 0)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM20, 7, 1)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM21, 7, 2)
    self.LayoutMetricGLCM.addWidget(self.HeterogeneityMetricGLCM22, 8, 0)
    ####
        
    
    #### Texture-GLRL Tab
    self.textureGLRLHeterogeneityMetrics = []
    self.LayoutMetricGLRL = qt.QGridLayout()
    self.tabGLRL = qt.QWidget()
    self.tabGLRL.setLayout(self.LayoutMetricGLRL)
    self.tabGroupsHeterogeneityMetrics.addTab(self.tabGLRL, "Texture: GLRL")
    
    #
    self.HeterogeneityMetricGLRLMatrix = qt.QCheckBox()
    self.HeterogeneityMetricGLRLMatrix.setFont(boldFont)
    self.HeterogeneityMetricGLRLMatrix.setText('Generate Gray-Level Run Length Matrix')
    self.HeterogeneityMetricGLRLMatrix.checked = True
    #
 
    self.HeterogeneityMetricGLRL1 = qt.QCheckBox()  
    self.HeterogeneityMetricGLRL1.setText('SRE')
    self.HeterogeneityMetricGLRL1.checked = True
    self.textureGLRLHeterogeneityMetrics.append(self.HeterogeneityMetricGLRL1)
    self.HeterogeneityMetricGLRL1.setToolTip('Short Run Emphasis (SRE)')

    self.HeterogeneityMetricGLRL2 = qt.QCheckBox()  
    self.HeterogeneityMetricGLRL2.setText('LRE')
    self.HeterogeneityMetricGLRL2.checked = True
    self.textureGLRLHeterogeneityMetrics.append(self.HeterogeneityMetricGLRL2)
    self.HeterogeneityMetricGLRL2.setToolTip('Long Run Emphasis (LRE)')
    
    self.HeterogeneityMetricGLRL3 = qt.QCheckBox()  
    self.HeterogeneityMetricGLRL3.setText('GLN')
    self.HeterogeneityMetricGLRL3.checked = True
    self.textureGLRLHeterogeneityMetrics.append(self.HeterogeneityMetricGLRL3)
    self.HeterogeneityMetricGLRL3.setToolTip('Gray Level Non-Uniformity (GLN)')
    
    self.HeterogeneityMetricGLRL4 = qt.QCheckBox()  
    self.HeterogeneityMetricGLRL4.setText('RLN')
    self.HeterogeneityMetricGLRL4.checked = True
    self.textureGLRLHeterogeneityMetrics.append(self.HeterogeneityMetricGLRL4)
    self.HeterogeneityMetricGLRL4.setToolTip('Run Length Non-Uniformity (RLN)')
    
    self.HeterogeneityMetricGLRL5 = qt.QCheckBox()  
    self.HeterogeneityMetricGLRL5.setText('RP')
    self.HeterogeneityMetricGLRL5.checked = True
    self.textureGLRLHeterogeneityMetrics.append(self.HeterogeneityMetricGLRL5)
    self.HeterogeneityMetricGLRL5.setToolTip('Run Percentage (RP)')
    
    self.HeterogeneityMetricGLRL6 = qt.QCheckBox()  
    self.HeterogeneityMetricGLRL6.setText('LGLRE')
    self.HeterogeneityMetricGLRL6.checked = True
    self.textureGLRLHeterogeneityMetrics.append(self.HeterogeneityMetricGLRL6)
    self.HeterogeneityMetricGLRL6.setToolTip('Low Gray Level Run Emphasis (LGLRE)')
    
    self.HeterogeneityMetricGLRL7 = qt.QCheckBox()  
    self.HeterogeneityMetricGLRL7.setText('HGLRE')
    self.HeterogeneityMetricGLRL7.checked = True
    self.textureGLRLHeterogeneityMetrics.append(self.HeterogeneityMetricGLRL7)
    self.HeterogeneityMetricGLRL7.setToolTip('High Gray Level Run Emphasis (HGLRE)')
    
    self.HeterogeneityMetricGLRL8 = qt.QCheckBox()  
    self.HeterogeneityMetricGLRL8.setText('SRLGLE')
    self.HeterogeneityMetricGLRL8.checked = True
    self.textureGLRLHeterogeneityMetrics.append(self.HeterogeneityMetricGLRL8)
    self.HeterogeneityMetricGLRL8.setToolTip('Short Run Low Gray Level Emphasis (SRLGLE)')
    
    self.HeterogeneityMetricGLRL9 = qt.QCheckBox()  
    self.HeterogeneityMetricGLRL9.setText('SRHGLE')
    self.HeterogeneityMetricGLRL9.checked = True
    self.textureGLRLHeterogeneityMetrics.append(self.HeterogeneityMetricGLRL9)
    self.HeterogeneityMetricGLRL9.setToolTip('Short Run High Gray Level Emphasis (SRHGLE)')
    
    self.HeterogeneityMetricGLRL10 = qt.QCheckBox()  
    self.HeterogeneityMetricGLRL10.setText('LRLGLE')
    self.HeterogeneityMetricGLRL10.checked = True
    self.textureGLRLHeterogeneityMetrics.append(self.HeterogeneityMetricGLRL10)
    self.HeterogeneityMetricGLRL10.setToolTip('Long Run Low Gray Level Emphasis (LRLGLE)')

    self.HeterogeneityMetricGLRL11 = qt.QCheckBox()  
    self.HeterogeneityMetricGLRL11.setText('LRHGLE')
    self.HeterogeneityMetricGLRL11.checked = True
    self.textureGLRLHeterogeneityMetrics.append(self.HeterogeneityMetricGLRL11)
    self.HeterogeneityMetricGLRL11.setToolTip('Long Run High Gray Level Emphasis (LRHGLE)')
    
    
    self.LayoutMetricGLRL.addWidget(self.HeterogeneityMetricGLRLMatrix, 0, 0)
    
    self.LayoutMetricGLRL.addWidget(self.HeterogeneityMetricGLRL1, 1, 0)
    self.LayoutMetricGLRL.addWidget(self.HeterogeneityMetricGLRL2, 1, 1)
    self.LayoutMetricGLRL.addWidget(self.HeterogeneityMetricGLRL3, 1, 2)
    self.LayoutMetricGLRL.addWidget(self.HeterogeneityMetricGLRL4, 2, 0)
    self.LayoutMetricGLRL.addWidget(self.HeterogeneityMetricGLRL5, 2, 1)
    self.LayoutMetricGLRL.addWidget(self.HeterogeneityMetricGLRL6, 2, 2)
    self.LayoutMetricGLRL.addWidget(self.HeterogeneityMetricGLRL7, 3, 0)
    self.LayoutMetricGLRL.addWidget(self.HeterogeneityMetricGLRL8, 3, 1)
    self.LayoutMetricGLRL.addWidget(self.HeterogeneityMetricGLRL9, 3, 2)
    self.LayoutMetricGLRL.addWidget(self.HeterogeneityMetricGLRL10, 4, 0)
    self.LayoutMetricGLRL.addWidget(self.HeterogeneityMetricGLRL11, 4, 1)
    ####
    
    self.heterogeneityMetricWidgets = (self.firstOrderHeterogeneityMetrics + self.morphologicalHeterogeneityMetrics
                                      + self.renyiHeterogeneityMetrics + self.geometricalHeterogeneityMetrics 
                                      + self.textureGLCMHeterogeneityMetrics + self.textureGLRLHeterogeneityMetrics)
    
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
    self.createContextMenus()
    
    self.HeterogeneityMetricGeometricalExtrusion.connect('clicked(bool)', self.onGeometricalExtrusionToggled)
    self.HeterogeneityMetricGLCMMatrix.connect('clicked(bool)', self.onGLCMMatrixToggled)
    self.HeterogeneityMetricGLRLMatrix.connect('clicked(bool)', self.onGLRLMatrixToggled)
    
    self.HeterogeneityCADButton.connect('clicked()', self.onHeterogeneityCADButtonClicked)
    self.saveButton.connect('clicked()', self.onSave)
    ####################
    #End Connections
    ####################
  
  #Checkbox Toggles  
  def onGeometricalExtrusionToggled(self, checked):
    if checked:
      for metricWidget in self.geometricalHeterogeneityMetrics:
        metricWidget.enabled = True
        metricWidget.checked = True
    else:
      for metricWidget in self.geometricalHeterogeneityMetrics:
        metricWidget.enabled = False
        metricWidget.checked = False
          
  def onGLCMMatrixToggled(self, checked):
    if checked:
      for metricWidget in self.textureGLCMHeterogeneityMetrics:
        metricWidget.enabled = True
        metricWidget.checked = True
    else:
      for metricWidget in self.textureGLCMHeterogeneityMetrics:
        metricWidget.enabled = False
        metricWidget.checked = False
  
  def onGLRLMatrixToggled(self, checked):
    if checked:
      for metricWidget in self.textureGLRLHeterogeneityMetrics:
        metricWidget.enabled = True
        metricWidget.checked = True
    else:
      for metricWidget in self.textureGLRLHeterogeneityMetrics:
        metricWidget.enabled = False
        metricWidget.checked = False
  
  #Context menu generation  
  def createContextMenus(self):
    for metricWidget in self.heterogeneityMetricWidgets:
      metricWidget.setContextMenuPolicy(3)
      metricName = metricWidget.text
      descriptionLabel = MetricWidgetHelperLib.MetricDescriptionLabel(metricWidget).getDescription()    
      self.metricContextMenus[metricName] = MetricWidgetHelperLib.ContextMenu(metricWidget, descriptionLabel)           
      metricWidget.customContextMenuRequested.connect(lambda point, metricName=metricName: self.metricContextMenus[metricName].connectAndMap(point))
    
    #Non Metric Context Menu Assignments(i.e. feature-class specific precalculations like GLCM matrices         
    self.HeterogeneityMetricGeometricalExtrusion.setContextMenuPolicy(3)
    descriptionLabelExtrusion = MetricWidgetHelperLib.MetricDescriptionLabel(self.HeterogeneityMetricGeometricalExtrusion).getDescription()    
    self.metricContextMenus['Generate 4D Extruded Object'] = MetricWidgetHelperLib.ContextMenu(self.HeterogeneityMetricGeometricalExtrusion, descriptionLabelExtrusion)
    self.HeterogeneityMetricGeometricalExtrusion.customContextMenuRequested.connect(self.metricContextMenus['Generate 4D Extruded Object'].connectAndMap)
    self.metricContextMenus['Generate 4D Extruded Object'].addParameterEditWindow(self.HeterogeneityCADCollapsibleButton, "<parameter name>") 
    
    self.HeterogeneityMetricGLCMMatrix.setContextMenuPolicy(3)
    descriptionLabelGLCMMatrix = MetricWidgetHelperLib.MetricDescriptionLabel(self.HeterogeneityMetricGLCMMatrix).getDescription()
    self.metricContextMenus['Gray-Level Co-occurrence Matrix'] = MetricWidgetHelperLib.ContextMenu(self.HeterogeneityMetricGLCMMatrix, descriptionLabelGLCMMatrix)
    self.HeterogeneityMetricGLCMMatrix.customContextMenuRequested.connect(self.metricContextMenus['Gray-Level Co-occurrence Matrix'].connectAndMap)
    self.metricContextMenus['Gray-Level Co-occurrence Matrix'].addParameterEditWindow(self.HeterogeneityCADCollapsibleButton, "<parameter name>") 
       
    self.HeterogeneityMetricGLRLMatrix.setContextMenuPolicy(3)
    descriptionLabelGLRLMatrix = MetricWidgetHelperLib.MetricDescriptionLabel(self.HeterogeneityMetricGLRLMatrix).getDescription()
    self.metricContextMenus['Gray-Level Run Length Matrix'] = MetricWidgetHelperLib.ContextMenu(self.HeterogeneityMetricGLRLMatrix, descriptionLabelGLRLMatrix)
    self.HeterogeneityMetricGLRLMatrix.customContextMenuRequested.connect(self.metricContextMenus['Gray-Level Run Length Matrix'].connectAndMap)
    self.metricContextMenus['Gray-Level Run Length Matrix'].addParameterEditWindow(self.HeterogeneityCADCollapsibleButton, "<parameter name>") 
    
    #Use this line to add new edit parameter options in the context menu for individual metrics:
    #self.metricContextMenus[<metric name>].addParameterEditWindow(self.HeterogeneityCADCollapsibleButton, "<parameter name>") 
    
    #Add dictionary to relate metrics to a list of their parameters+values (as arguments to supply to metric functions)  

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
    bins, arrayDiscreteValues, numDiscreteValues = self.histogramData(self.targetVoxels)
    
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
    
  def histogramData(self, voxelArray):
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
