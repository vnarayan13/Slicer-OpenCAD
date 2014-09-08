cmake_minimum_required(VERSION 2.8.9)

project(OpenCAD)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_NAME "OpenCAD")
set(EXTENSION_HOMEPAGE "http://www.slicer.org/slicerWiki/index.php/Documentation/4.3/Extensions/OpenCAD")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Vivek Narayan, Jayender Jagadeesan (BWH)")
set(EXTENSION_DESCRIPTION "This Module applies OpenCAD segmentation to input DCE-MRI Volumes and generates a label map")
set(EXTENSION_ICONURL "http://www.slicer.org/slicerWiki/images/2/2e/OpenCAD.PNG")
set(EXTENSION_SCREENSHOTURLS "http://www.slicer.org/slicerWiki/images/e/ef/SegmentCAD-Output.png")

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(SegmentCAD)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
