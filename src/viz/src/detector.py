#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import TransformStamped
import tf2_ros
from cv_bridge import CvBridge
import numpy as np
import cv2 as cv
import threading
import queue

class RedBallDetectorNode(Node):
    def __init__(self):
        super().__init__('RED_BALL_DETECTOR')
        
        # Parámetros para el color y tamaño
        self.declare_parameter('MARKER_SIZE_PX', 20) # Mínimo tamaño de pelota en píxeles
        self.declare_parameter('CAM_FRAME_ID', 'cam')
        
        self.min_area = self.get_parameter('MARKER_SIZE_PX').get_parameter_value().integer_value
        self.cam_frame = self.get_parameter('CAM_FRAME_ID').get_parameter_value().string_value

        self.bridge = CvBridge()
        self.transformer = tf2_ros.TransformBroadcaster(self)

        # Usamos el patrón de cola para evitar bloqueos
        self.frame_queue = queue.Queue(maxsize=1) 
        self.processing_active = True
        self.process_thread = threading.Thread(target=self.processing_loop)
        self.process_thread.start()
        
        self.image_pub = self.create_publisher(Image, 'image/ball_debug', 10)
        
        # Suscriptor a la imagen CORREGIDA
        self.subscription = self.create_subscription(
            Image, 'image/fixed', self.image_callback, 10
        )
        self.get_logger().info('Red Ball Detector Node ready.')

    # ... (image_callback y destroy_node son idénticos a arucos.py) ...
    def image_callback(self, msg):
        try:
            if self.frame_queue.full():
                self.frame_queue.get_nowait()
            self.frame_queue.put(msg)
        except queue.Empty:
            pass

    def processing_loop(self):
        while self.processing_active:
            msg = None
            try:
                msg = self.frame_queue.get(timeout=0.01) 
            except queue.Empty:
                continue

            try:
                frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            except Exception as e:
                self.get_logger().error(f"CvBridge error in thread: {e}")
                continue
            
            # --- LÓGICA DE DETECCIÓN DE COLOR ---
            center_x, center_y, radius, debug_img = self.detect_red_color(frame)
            
            if radius > self.min_area:
                # La posición Z de la pelota es un placeholder ya que no hay estimación 3D
                # A menos que se use un modelo de cámara (lo cual no tenemos aquí).
                # Usaremos la información de la pose del plano de la cámara (TF).
                self.publish_ball_pose(center_x, center_y, radius, msg.header)

            self.publish_debug_image(debug_img, msg.header)
        
        # ... (Cierre de nodo en destroy_node) ...


    def detect_red_color(self, image):
        """Aplica el filtro HSV y encuentra el contorno más grande."""
        hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
        
        # Rangos de color (para el rojo en ambos lados del círculo cromático)
        lower_red_1 = np.array([0, 100, 50])
        upper_red_1 = np.array([10, 255, 255])
        lower_red_2 = np.array([170, 100, 50])
        upper_red_2 = np.array([180, 255, 255])
        
        # Crear máscaras
        mask1 = cv.inRange(hsv, lower_red_1, upper_red_1)
        mask2 = cv.inRange(hsv, lower_red_2, upper_red_2)
        mask = mask1 + mask2
        
        # Limpieza de ruido (apertura y cierre)
        mask = cv.erode(mask, None, iterations=2)
        mask = cv.dilate(mask, None, iterations=2)

        # Encontrar contornos
        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        
        center_x, center_y, radius = 0, 0, 0
        debug_img = image.copy()

        if contours:
            largest_contour = max(contours, key=cv.contourArea)
            ((center_x_float, center_y_float), radius_float) = cv.minEnclosingCircle(largest_contour)
            
            # Solo si el área es lo suficientemente grande
            if cv.contourArea(largest_contour) > self.min_area:
                center_x = int(center_x_float)
                center_y = int(center_y_float)
                radius = int(radius_float)
                
                # Dibujar el círculo y el centro en la imagen de debug
                cv.circle(debug_img, (center_x, center_y), radius, (0, 255, 255), 2)
                cv.circle(debug_img, (center_x, center_y), 5, (0, 0, 255), -1)

        return center_x, center_y, radius, debug_img

    def publish_ball_pose(self, center_x_px, center_y_px, radius_px, header):
        """Publica la posición (X, Y) del centro de la pelota en el espacio de la cámara."""
        
        # ⚠️ Nota: Este nodo solo calcula la posición 2D (pixeles). 
        # La posición 3D (Z) necesita la matriz de cámara (K) para ser estimada.
        # Por simplicidad, publicaremos solo la coordenada de pixel.
        
        # Usamos una TransformStamped con Z=1.0m como placeholder
        t = TransformStamped()
        t.header.stamp = header.stamp
        t.header.frame_id = self.cam_frame
        t.child_frame_id = 'red_ball'

        # Asumimos que la traslación es proporcional al centro del frame (Normalización)
        # Traslación X (horizontal) y Y (vertical)
        t.transform.translation.x = (center_x_px - header.width / 2.0) * 0.001
        t.transform.translation.y = (center_y_px - header.height / 2.0) * 0.001
        t.transform.translation.z = 1.0 # Placeholder Z = 1 metro
        
        # Orientación nula (es una esfera)
        t.transform.rotation.w = 1.0
        
        self.transformer.sendTransform(t)

    def publish_debug_image(self, image, header):
        img_msg = self.bridge.cv2_to_imgmsg(image, encoding="bgr8")
        img_msg.header = header
        self.image_pub.publish(img_msg)

    # ... (create_node y if __name__ == '__main__': sin cambios) ...
def create_node():
    return RedBallDetectorNode()

if __name__ == '__main__':
    rclpy.init()
    node = RedBallDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
