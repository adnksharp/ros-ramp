cmake_minimum_required(VERSION 3.8)
project(viz)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
install(DIRECTORY
    include
    DESTINATION include
)

# 2. INSTALACIÓN DE MODELOS 3D Y TEXTURAS (CORRECCIÓN CLAVE)
# Mueve los archivos generados a una carpeta de recursos dedicada (ej: 'models')
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
	#src/info.py
	src/fixer.py
	##############
	src/arucos.py
	src/poser.py
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
