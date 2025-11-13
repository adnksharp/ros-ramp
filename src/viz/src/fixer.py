#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import cv2 as cv
import os
import threading
import queue

class ImageFixerNode(Node):
    def __init__(self):
        super().__init__('IMAGE_FIXER')
        
        self.declare_parameter('CALIB_FILE', 'include/params.yaml')
        
        sharedDir = get_package_share_directory('viz')
        calib_file_path = os.path.join(
            sharedDir, 
            self.get_parameter('CALIB_FILE').get_parameter_value().string_value
        )
        
        self.mtx, self.dist = self.load_calibration_params(calib_file_path)

        self.bridge = CvBridge()
        
        self.original_size = (1920, 1080) 
        
        self.map1, self.map2, self.roi = self.precalculate_remap(self.original_size)

        self.fixed_pub = self.create_publisher(Image, 'image/fixed', 10)
        
        self.frame_queue = queue.Queue(maxsize=1) 
        self.processing_active = True
        
        self.process_thread = threading.Thread(target=self.processing_loop)
        self.process_thread.start()
        
        self.subscription = self.create_subscription(
            Image, 'image/raw', self.image_callback, 10
        )
        
        self.get_logger().info('IMAGE_FIXER Node ready. Publishing to /image/fixed.')


    def load_calibration_params(self, file_path):
        if not os.path.exists(file_path):
            self.get_logger().fatal(f'Calibration file not found: {file_path}')
            raise FileNotFoundError("Calibration file is missing.")
        
        fs = cv.FileStorage(file_path, cv.FileStorage_READ)
        mtx = fs.getNode('K').mat()
        dist = fs.getNode('D').mat()
        fs.release()
        
        if mtx is None or dist is None:
            self.get_logger().fatal('Calibration data (K or D) is invalid.')
            raise ValueError("Invalid calibration data.")
        
        self.get_logger().info('Calibration parameters loaded successfully.')
        return mtx, dist

    
    def precalculate_remap(self, original_size):
        w, h = original_size
        
        newcam, roi = cv.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 1, (w, h))
        
        np.save(os.path.join(get_package_share_directory('viz'), 'newcam.npy'), newcam)
        
        map1, map2 = cv.initUndistortRectifyMap(self.mtx, self.dist, None, newcam, (w, h), cv.CV_16SC2)
        
        self.get_logger().info('Remap maps calculated successfully.')
        return map1, map2, roi
    
    def image_callback(self, msg):
        try:
            if self.frame_queue.full():
                self.frame_queue.get_nowait() 
            self.frame_queue.put(msg)
        except queue.Empty:
            pass

    def processing_loop(self):
        while self.processing_active:
            try:
                msg = self.frame_queue.get(timeout=0.02) 
            except queue.Empty:
                continue

            try:
                cam_img = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            except Exception as e:
                self.get_logger().error(f"CvBridge conversion error in thread: {e}")
                continue
            
            dst_img_full = cv.remap(cam_img, self.map1, self.map2, cv.INTER_LINEAR)

            x, y, w_roi, h_roi = self.roi
            dst_img_full = dst_img_full[y:y+h_roi, x:x+w_roi]
            
            fixed_msg = self.bridge.cv2_to_imgmsg(dst_img_full, encoding="bgr8")
            fixed_msg.header = msg.header
            self.fixed_pub.publish(fixed_msg)

    def destroy_node(self):
        self.processing_active = False
        if self.process_thread.is_alive():
            self.process_thread.join()
        super().destroy_node()

def create_node():
    return ImageFixerNode()

if __name__ == '__main__':
    rclpy.init()
    node = ImageFixerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
