import launch
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    
    # 1. Definición del Contenedor de Componentes
    container = ComposableNodeContainer(
            name='vision_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container',
            composable_node_descriptions=[
                # 2. Definición de los Nodos como Componentes
                
                # A. Publicador de Cámara (Stream)
                ComposableNode(
                    package='viz',
                    plugin='viz::CamNode', # Usar la notación de plugin (necesita ser definido en C++/YAML o un método custom de Python)
                    # Nota: Para Python, esto requiere que el paquete esté correctamente configurado 
                    # para exponer los componentes Python, lo cual puede ser complejo en ament_cmake/python.
                    # Asumiremos que el paquete viz tiene la estructura necesaria.
                    name='osmo_cam'
                ),
                
                # B. Corrector de Imagen (Fixer)
                ComposableNode(
                    package='viz',
                    plugin='viz::ImageFixerNode',
                    name='image_fixer'
                ),
                
                # C. Detector ArUco
                ComposableNode(
                    package='viz',
                    plugin='viz::ArucoDetectorNode',
                    name='aruco_detector'
                ),
                # D. Visualizador (Viz)
                ComposableNode(
                    package='viz',
                    plugin='viz::ArucoVizNode',
                    name='aruco_viz'
                ),
            ],
            output='screen',
    )

    return launch.LaunchDescription([container])
