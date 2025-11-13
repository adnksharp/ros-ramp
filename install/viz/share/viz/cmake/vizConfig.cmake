# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_viz_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED viz_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(viz_FOUND FALSE)
  elseif(NOT viz_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(viz_FOUND FALSE)
  endif()
  return()
endif()
set(_viz_CONFIG_INCLUDED TRUE)

# output package information
if(NOT viz_FIND_QUIETLY)
  message(STATUS "Found viz: 0.0.0 (${viz_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'viz' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT viz_DEPRECATED_QUIET)
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(viz_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${viz_DIR}/${_extra}")
endforeach()
