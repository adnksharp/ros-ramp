#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import TransformStamped
import tf2_ros
import os
from ament_index_python.packages import get_package_share_directory
import rclpy.duration

# NOTA: Asegúrate de que tengas instalado 'scipy' para la conversión de rotación en arucos.py

class ArucoVizNode(Node):
    def __init__(self):
        super().__init__('ARUCO_VIZ')
        
        # ----------------- Parámetros -----------------
        self.declare_parameter('MARKER_SIZE_M', 0.05)
        # Asumiendo que el detector solo publica IDs específicos o la lista completa es grande:
        self.declare_parameter('ARUCO_IDS', list(range(10))) 
        
        self.marker_size = self.get_parameter('MARKER_SIZE_M').get_parameter_value().double_value
        self.expected_ids = self.get_parameter('ARUCO_IDS').get_parameter_value().integer_array_value
        
        # OBTENER RUTA BASE DE LOS MODELOS DAE
        self.share_dir = get_package_share_directory('viz')
        # La ruta en el sistema de paquetes ROS2 para los modelos
        self.model_base_uri = 'package://viz/models' 
        
        # ----------------- Setup de TF Listener (Inicialización Retrasada) -----------------
        # Solo inicializamos el buffer; el listener se inicializa en init_tf_listener()
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = None 
        self.tf_initialized = False # Bandera para controlar el estado
        
        # ----------------- Publicadores -----------------
        self.marker_array_pub = self.create_publisher(
            MarkerArray, 
            'visualization/aruco_array', 
            10
        )
        
        # ----------------- Temporizadores -----------------
        # Timer para intentar publicar los Markers (20 Hz)
        self.timer = self.create_timer(0.05, self.timer_callback) 

        # Temporizador de un solo disparo para iniciar el listener después de un breve retraso
        # Esto evita el fallo de inicialización que estábamos viendo.
        self.one_shot_timer = self.create_timer(1.0, self.init_tf_listener) 
        
        self.get_logger().info('ARUCO_VIZ Node ready. Waiting for TF init.')


    def init_tf_listener(self):
        """Inicializa el TransformListener después de que el nodo esté activo."""
        # Detener y destruir este temporizador de un solo disparo
        self.one_shot_timer.cancel()
        
        try:
            # Inicializar el TransformListener
            self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
            self.tf_initialized = True 
            self.get_logger().info('TF Listener successfully initialized.')
            
        except Exception as e:
            self.get_logger().fatal(f"FATAL ERROR initializing TF Listener: {e}")
            # Si falla, cerramos el nodo
            rclpy.shutdown()


    def timer_callback(self):
        """Consulta la pose de TF y publica el MarkerArray."""
        
        # Solo ejecutar si el listener ha sido inicializado correctamente
        if not self.tf_initialized:
            return

        marker_array_msg = MarkerArray()
        
        for marker_id in self.expected_ids:
            try:
                target_frame = f'aruco_{marker_id}'
                source_frame = 'cam' 
                
                # 1. Query the TF2 Transformation (T_cam->aruco)
                # Usamos tiempo 0 para la pose más reciente
                transform = self.tf_buffer.lookup_transform(
                    source_frame, 
                    target_frame, 
                    rclpy.time.Time(), 
                    # Agregamos un timeout corto para la búsqueda
                    timeout=rclpy.duration.Duration(seconds=0.1) 
                )
                
                # 2. Crear el mensaje Marker (MESH_RESOURCE)
                marker = self.create_aruco_marker(marker_id, transform)
                marker_array_msg.markers.append(marker)

            except tf2_ros.LookupException:
                # El marcador no ha sido detectado o está fuera del buffer
                self.get_logger().debug(f"TF lookup failed for aruco_{marker_id}.")
                continue
            except tf2_ros.ExtrapolationException:
                # TF data is too old
                continue
            except Exception as e:
                # Otros errores (ej. tf2_ros.ConnectivityException)
                self.get_logger().debug(f"Unexpected error getting transform for aruco_{marker_id}: {e}")
                continue
        
        # Publicar el array solo si hay marcadores para dibujar
        if marker_array_msg.markers:
            self.marker_array_pub.publish(marker_array_msg)


    def create_aruco_marker(self, marker_id, transform):
        """Genera un mensaje Marker (MESH_RESOURCE) basado en la TransformStamped."""
        
        marker = Marker()
        
        marker.header.frame_id = transform.header.frame_id  
        marker.header.stamp = self.get_clock().now().to_msg()
        
        marker.ns = "aruco_objects"
        marker.id = marker_id
        marker.action = Marker.ADD

        # 1. TIPO DE RECURSO: MESH
        marker.type = Marker.MESH_RESOURCE 
        
        # 2. RUTA DEL MESH: package://viz/include/aruco_patterns/aruco_0008.dae
        marker_id_str = f"{marker_id:04d}"
        marker.mesh_resource = f'{self.model_base_uri}/{marker_id_str}.dae'

        # 3. Asignación de Pose (Posición y Orientación)
        # No se necesita el ajuste de 90 grados si el modelo DAE fue creado plano en XY
        
        # Posición
        marker.pose.position.x = transform.transform.translation.x
        marker.pose.position.y = transform.transform.translation.y
        marker.pose.position.z = transform.transform.translation.z
        
        # Orientación (Asignación explícita para evitar errores de tipo)
        marker.pose.orientation.x = transform.transform.rotation.x
        marker.pose.orientation.y = transform.transform.rotation.y
        marker.pose.orientation.z = transform.transform.rotation.z
        marker.pose.orientation.w = transform.transform.rotation.w

        # 4. Escala: 1.0 para mantener el tamaño real del modelo DAE (0.05m)
        marker.scale.x = 1.0 
        marker.scale.y = 1.0
        marker.scale.z = 1.0 
        
        # 5. Color (solo visible si la textura DAE falla)
        marker.color.a = 1.0 
        marker.color.r = 1.0 if marker_id % 3 == 0 else 0.0
        marker.color.g = 1.0 if marker_id % 3 == 1 else 0.0
        marker.color.b = 1.0 if marker_id % 3 == 2 else 0.0
        
        marker.lifetime.sec = 0
        
        return marker

def create_node():
    return ArucoVizNode()

if __name__ == '__main__':
    rclpy.init()
    node = ArucoVizNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
