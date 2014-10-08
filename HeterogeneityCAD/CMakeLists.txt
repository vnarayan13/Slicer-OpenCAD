#-----------------------------------------------------------------------------
set(MODULE_NAME HeterogeneityCAD)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  FeatureExtractionLib/__init__
  FeatureExtractionLib/FirstOrderStatistics
  FeatureExtractionLib/GeometricMeasures
  FeatureExtractionLib/MorphologyStatistics
  FeatureExtractionLib/NodeInformation
  FeatureExtractionLib/RenyiDimensions
  FeatureExtractionLib/TextureGLCM
  FeatureExtractionLib/TextureGLRL
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
