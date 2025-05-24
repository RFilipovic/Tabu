#----------------------------------------------------------------
# Generated CMake target import file for configuration "Debug".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Simulator::Simulator" for configuration "Debug"
set_property(TARGET Simulator::Simulator APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBUG)
set_target_properties(Simulator::Simulator PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_DEBUG "CXX"
  IMPORTED_LOCATION_DEBUG "${_IMPORT_PREFIX}/lib/libSimulator.a"
  )

list(APPEND _cmake_import_check_targets Simulator::Simulator )
list(APPEND _cmake_import_check_files_for_Simulator::Simulator "${_IMPORT_PREFIX}/lib/libSimulator.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
