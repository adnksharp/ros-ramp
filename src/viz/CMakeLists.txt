cmake_minimum_required(VERSION 3.8)
project(viz)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies

find_package(OpenCV 4 QUIET)
if (NOT OpenCV_FOUND)
  find_package(OpenCV REQUIRED)
endif ()
message(STATUS "Found OpenCV version ${OpenCV_VERSION}")
install(DIRECTORY
    include
    DESTINATION include
)

install(DIRECTORY
    include/aruco_patterns/
    DESTINATION share/${PROJECT_NAME}/models
    FILES_MATCHING
    PATTERN "*.dae"
    PATTERN "*.png"
)

install(DIRECTORY
	launch include
	DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
	src/stream.py
	src/save.py
	src/calib.py
	src/arucos.py
	#src/info.py
	#src/fixer.py
	##############
	src/detector.py
	src/kinematics.py
	#src/poser.py
	DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
