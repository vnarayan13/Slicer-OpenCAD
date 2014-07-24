from __main__ import vtk, qt, ctk, slicer
import string

  #place class definitions for metric checkbox, context menus, and parameter edit dialogs in another file
class ContextMenu(object):
  def __init__(self, metricWidget, descriptionLabel):
    self.metricWidget = metricWidget 
    self.descriptionLabel = descriptionLabel
      
    self.contextMenu = qt.QMenu(self.metricWidget)
    self.parameterEditWindows = {}
    self.parameterActions = {}
      
    self.descriptionAction = qt.QWidgetAction(self.contextMenu)
    self.descriptionAction.setDefaultWidget(self.descriptionLabel)
    self.closeAction = qt.QAction("Close", self.contextMenu)
   
    self.reloadActions()
    
     
  def connectAndMap(self, pos):
    self.contextMenu.popup(self.metricWidget.mapToGlobal(pos))
  
    
  def reloadActions(self):
    #does adding an action that exists in the menu just replace that action slot?
    self.contextMenu.addAction(self.descriptionAction)    
    for action in self.parameterActions.values():
      self.contextMenu.addAction(action)          
    self.contextMenu.addAction(self.closeAction)
  
  def addParameterEditWindow(self, parent, parameter):
    self.parameterActions[parameter] = qt.QAction(('Edit %s' %parameter), self.contextMenu) 
    self.reloadActions()
    
    helpString = "Edit " + parameter + " for " + self.metricWidget.text
    
    self.parameterEditWindows[parameter] = self.ParameterEditWindow(parent, self.metricWidget, helpString)
    self.parameterActions[parameter].connect('triggered()', lambda parameter=parameter: self.parameterEditWindows[parameter].showWindow())
 
 
  class ParameterEditWindow(object):  
    def __init__(self, parent, metric, helpString = ""): 
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
