#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
from sensor_msgs.msg import CameraInfo
import cv2 as cv
import numpy as np
import os
import time

class CameraInfoPublisherNode(Node):
    def __init__(self):
        super().__init__('CAMERA_INFO_PUBLISHER')
        
        self.declare_parameter('CALIB_FILE', 'include/params.yaml')
        self.declare_parameter('IMG_WIDTH', 1920)
        self.declare_parameter('IMG_HEIGHT', 1080)
        self.declare_parameter('FPS', 30.0)
        self.declare_parameter('FRAME_ID', 'cam')
        
        sharedDir = get_package_share_directory('viz') # Asumiendo que tu paquete se llama 'viz'
        calib_file_path = os.path.join(
            sharedDir, 
            self.get_parameter('CALIB_FILE').get_parameter_value().string_value
        )
        
        self.width = self.get_parameter('IMG_WIDTH').get_parameter_value().integer_value
        self.height = self.get_parameter('IMG_HEIGHT').get_parameter_value().integer_value
        self.frame_id = self.get_parameter('FRAME_ID').get_parameter_value().string_value
        fps = self.get_parameter('FPS').get_parameter_value().double_value

        self.info_msg = self.load_calibration_and_create_msg(calib_file_path)

        # El tópico de CameraInfo debe ser <tópico_imagen_cruda>/camera_info
        self.publisher_ = self.create_publisher(CameraInfo, 'image/camera_info', 10)
        
        self.hz = 1.0 / fps 
        self.timer = self.create_timer(self.hz, self.timer_callback)
        
        self.get_logger().info('CAMERA_INFO_PUBLISHER Node ready. Publishing to /image/camera_info.')


    def load_calibration_and_create_msg(self, file_path):
        """Carga los parámetros de calibración desde el YAML de OpenCV y crea el mensaje CameraInfo."""
        
        if not os.path.exists(file_path):
            self.get_logger().fatal(f'Calibration file not found: {file_path}')
            raise FileNotFoundError("Calibration file is missing.")
        
        # --- 1. Cargar K y D desde YAML ---
        fs = cv.FileStorage(file_path, cv.FileStorage_READ)
        K = fs.getNode('K').mat()
        D = fs.getNode('D').mat()
        fs.release()
        
        if K is None or D is None:
            self.get_logger().fatal('Calibration data (K or D) is invalid.')
            raise ValueError("Invalid calibration data.")
        
        self.get_logger().info('Calibration parameters loaded successfully.')
        
        # --- 2. Calcular R y P para la rectificación óptima ---
        # R (Matriz de Rectificación): Identidad para single camera.
        # P (Matriz de Proyección): Es la matriz de cámara corregida (newcam matrix).
        
        # Usamos los parámetros de la imagen cruda que definiste en OSMO
        img_size = (self.width, self.height)
        
        # La función getOptimalNewCameraMatrix de OpenCV es clave aquí:
        # Alpha=1 devuelve la nueva matriz de cámara (P) y el ROI que recorta los bordes negros.
        # Es lo mismo que se hacía en tu nodo anterior (IMAGE_FIXER) para obtener newcam.
        newcam_matrix, roi = cv.getOptimalNewCameraMatrix(K, D, img_size, 1, img_size)
        
        R = np.identity(3, dtype=np.float64) # Matriz de rotación (3x3)
        P = np.zeros((3, 4), dtype=np.float64) # Matriz de proyección (3x4)
        P[:3, :3] = newcam_matrix # K' se coloca en las primeras 3x3 posiciones

        # --- 3. Crear el mensaje CameraInfo ---
        msg = CameraInfo()
        msg.header.frame_id = self.frame_id
        msg.width = self.width
        msg.height = self.height
        
        # K (Matriz de Cámara 3x3)
        msg.k = K.flatten().tolist()
        
        # D (Coeficientes de Distorsión)
        # Asegurarse de que sea una lista 
        msg.d = D.flatten().tolist()
        
        # R (Matriz de Rectificación 3x3)
        msg.r = R.flatten().tolist()
        
        # P (Matriz de Proyección/NewCamera 3x4)
        msg.p = P.flatten().tolist()
        
        return msg

    def timer_callback(self):
        """Publica el mensaje CameraInfo a la misma frecuencia que la imagen."""
        
        # Actualizar el timestamp (marca de tiempo)
        self.info_msg.header.stamp = self.get_clock().now().to_msg()
        
        # Publicar
        self.publisher_.publish(self.info_msg)

def create_node():
    return CameraInfoPublisherNode()

if __name__ == '__main__':
    rclpy.init()
    node = CameraInfoPublisherNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
