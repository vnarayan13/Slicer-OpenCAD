#-----------------------------------------------------------------------------
set(MODULE_NAME SegmentCAD)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  ${MODULE_NAME}Logic/__init__
  ${MODULE_NAME}Logic/${MODULE_NAME}Logic
  LabelStatisticsLogic/__init__
  LabelStatisticsLogic/LabelStatisticsLogic
  )

set(MODULE_PYTHON_RESOURCES
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )
