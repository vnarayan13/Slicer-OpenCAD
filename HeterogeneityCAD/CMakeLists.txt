#-----------------------------------------------------------------------------
set(MODULE_NAME HeterogeneityCAD)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  FeatureExtractionLib/__init__
  FeatureExtractionLib/NodeInformation
  FeatureExtractionLib/FirstOrderStatistics
  FeatureExtractionLib/MorphologyStatistics
  FeatureExtractionLib/TextureGLCM
  FeatureExtractionLib/TextureGLRL
  FeatureExtractionLib/RenyiDimensions
  FeatureExtractionLib/GeometricalMeasures
  FeatureWidgetHelperLib/__init__
  FeatureWidgetHelperLib/FeatureDescriptionLabel
  FeatureWidgetHelperLib/FeatureWidgets
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
