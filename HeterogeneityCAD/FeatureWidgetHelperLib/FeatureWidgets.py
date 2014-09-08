from __main__ import vtk, qt, ctk, slicer
import string
import collections
import FeatureWidgetHelperLib


class CheckableTabWidget(qt.QTabWidget):

  def __init__(self, parent=None):
    super(CheckableTabWidget, self).__init__(parent)
    self.checkBoxList = collections.OrderedDict()
    
    # hack ( QTabWidget.setTabBar() and tabBar() are protected )
    self.tab_bar = self.findChildren(qt.QTabBar)[0]
    
    # Bold font style
    self.boldFont = qt.QFont()
    self.boldFont.setBold(True)
    
    self.tab_bar.setFont(self.boldFont)
    self.tab_bar.setContextMenuPolicy(3)
    self.tab_bar.installEventFilter(self)
        
  def addTab(self, widget, featureClass, featureWidgets, checkStatus=True):
    qt.QTabWidget.addTab(self, widget, featureClass)
    
    featureClassDescriptionLabel =  FeatureWidgetHelperLib.FeatureClassDescriptionLabel()
    featureClassDescriptionLabel.setDescription(featureClass)
    checkBox = FeatureWidgetHelperLib.FeatureWidget()       
    checkBox.Setup(descriptionLabel = featureClassDescriptionLabel, checkStatus=checkStatus)
    self.checkBoxList[featureClass] = checkBox
    
    self.tab_bar.setTabButton(self.tab_bar.count-1, qt.QTabBar.LeftSide, checkBox)
    self.connect(checkBox, qt.SIGNAL('stateChanged(int)'), lambda checkState: self.stateChanged(checkBox, checkState, featureWidgets))
    
  def isChecked(self, index):
    return self.tab_bar.tabButton(index, qt.QTabBar.LeftSide).checkState() != 0

  def setCheckState(self, index, checkState):
    self.tab_bar.tabButton(index, qt.QTabBar.LeftSide).setCheckState(checkState)

  def stateChanged(self, checkBox, checkState, featureWidgets):
    # uncheck all checkboxes in QObject # may not need to pass list?
    index = self.checkBoxList.values().index(checkBox)
    if checkState == 0:
      for widget in featureWidgets:
        widget.checked = False
    elif checkState == 2:
      for widget in featureWidgets:
        widget.checked = True
        
  def eventFilter(self, object, event):
    # context menu request (right-click) on QTabBar is forwarded to the QCheckBox (FeatureWidget) 
    if object == self.tab_bar and event.type() == qt.QEvent.ContextMenu:
      tabIndex = object.tabAt(event.pos())
      
      pos = self.checkBoxList.values()[tabIndex].mapFrom(self.tab_bar, event.pos())
           
      if tabIndex > -1:
        qt.QCoreApplication.sendEvent(self.checkBoxList.values()[tabIndex], qt.QContextMenuEvent(0, pos))
                    
      return True               
    return False
    
  def addParameter(self, featureClass, parameter):
    self.checkBoxList[featureClass].addParameter(parameter)
  
  
class FeatureWidget(qt.QCheckBox):
  def __init__(self, parent=None):
    super(FeatureWidget, self).__init__(parent)
        
  def Setup(self, featureName="", descriptionLabel=None, checkStatus=True):
    self.featureName = featureName
    self.checkStatus = checkStatus
    if descriptionLabel:
      self.descriptionLabel = descriptionLabel 
    else:
      self.descriptionLabel = FeatureWidgetHelperLib.FeatureDescriptionLabel()
      self.descriptionLabel.setDescription(self.featureName)
      
    self.setText(self.featureName)
    self.checked = self.checkStatus

    self.setContextMenuPolicy(3)
    self.widgetMenu = ContextMenu(self)
    self.widgetMenu.Setup(self.featureName, self.descriptionLabel) 
    self.customContextMenuRequested.connect(lambda point: self.connectMenu(point))
       
  def connectMenu(self, pos):
    self.widgetMenu.popup(self.mapToGlobal(pos))
      
  def addParameter(self, parameter):
    self.widgetMenu.addParameter(self, parameter) 
  
  
class ContextMenu(qt.QMenu):
  def __init__(self, parent=None):
    super(ContextMenu, self).__init__(parent)
   
  def Setup(self, featureName, descriptionLabel="Description:"):
    self.featureName = featureName
    self.descriptionLabel = descriptionLabel   
    self.parameters = collections.OrderedDict()
           
    self.descriptionAction = qt.QWidgetAction(self)
    self.descriptionAction.setDefaultWidget(self.descriptionLabel)
    self.closeAction = qt.QAction("Close", self)     
    self.reloadActions()
      
  def reloadActions(self):
    #does adding an action that exists in the menu just replace that action slot?
    self.addAction(self.descriptionAction)    
    for parameter in self.parameters:
      self.addAction(self.parameters[parameter]['Action'])               
    self.addAction(self.closeAction)
      
  def addParameter(self, parent, parameterName):
    helpString = "Edit " + parameterName + " (" + self.featureName + ")"
      
    self.parameters[parameterName] = {}
    self.parameters[parameterName]['Action'] = qt.QAction(('Edit %s' %parameterName), self)
    self.parameters[parameterName]['EditWindow'] = self.ParameterEditWindow(parent, self.featureName, helpString)
            
    self.parameters[parameterName]['Action'].connect('triggered()', lambda parameterName=parameterName: self.parameters[parameterName]['EditWindow'].showWindow())
    self.reloadActions()
    
  #class ParameterEditWindow(qt.QInputDialog):
    #def __init__(self, parent=None):
      #super(FeatureWidget.ContextMenu, self).__init__(parent)
            
  class ParameterEditWindow(object):  
    def __init__(self, parent, featureName, helpString = ""): 
      self.helpString = helpString
      windowTitle = "Edit Parameter Window"
      self.editWindow = qt.QInputDialog(parent)
      self.editWindow.setLabelText(self.helpString + " (Current Value = " + str(self.editWindow.intValue()) + "): ")
      self.editWindow.setInputMode(1) #make this modifiable

    def showWindow(self):
      self.resetLabel()     
      self.editWindow.open()
      
    def resetLabel(self):
      self.editWindow.setLabelText(self.helpString + " (Current Value = " + str(self.editWindow.intValue()) + "): ")  
          
