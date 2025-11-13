#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from ament_index_python.packages import get_package_share_directory
from cv_bridge import CvBridge
import cv2 as cv
import os
from datetime import datetime
import threading
import time

class ImageSaverNode(Node):
    def __init__(self):
        super().__init__('SAVER')
        
        self.declare_parameter('IMG_DIR', 'include')
        self.declare_parameter('SAVE_FREQ', 10.0)
        
        self.path = self.get_parameter('IMG_DIR').get_parameter_value().string_value
        self.path = os.path.join(get_package_share_directory('viz'), self.path)
        self.freq = 1.0 / self.get_parameter('SAVE_FREQ').get_parameter_value().double_value

        self.bridge = CvBridge()
        self.millis = time.time()
        self.buff = None
        
        self.subscription = self.create_subscription(
            Image,
            'image/raw',
            self.image_callback,
            10
        )
        self.subscription

        self.save_timer = self.create_timer(self.freq, self.save_timer_callback)
        
        self.get_logger().info(f'{self.path} @ {1/self.freq:.2f}Hz')


    def image_callback(self, msg):
        self.buff = msg


    def save_timer_callback(self):
        if self.buff is None:
            self.get_logger().warn("IMG NOT FOUND")
            return

        try:
            img = self.bridge.imgmsg_to_cv2(self.buff, "bgr8")
            now = datetime.now()
            filename = now.strftime("%Y%m%d%H%M%S") + now.strftime("%f")[:3]
            path = os.path.join(self.path, 'raw')
            os.makedirs(path, exist_ok=True)
            path = os.path.join(path, f"{filename}.jpg")
            cv.imwrite(path, img)
        except Exception as e:
            self.get_logger().error(f"SAVE {e}")

def create_node():
    return ImageSaverNode()

if __name__ == '__main__':
    rclpy.init()
    node = ImageSaverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
