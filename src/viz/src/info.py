#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo
from ament_index_python.packages import get_package_share_directory
import numpy as np
import os
import yaml

class CameraInfoPublisherNode(Node):
    def __init__(self):
        super().__init__('camera_info_publisher')
        
        self.declare_parameter('CALIB_FILE', 'params.yaml')
        self.declare_parameter('TOPIC_NAME', 'camera_info')
        
        # --- Load Calibration Data ---
        self.info_msg = self.load_camera_info()

        # --- Publisher Setup ---
        topic = self.get_parameter('TOPIC_NAME').get_parameter_value().string_value
        self.publisher_ = self.create_publisher(CameraInfo, topic, 10)
        
        # Publish at 1 Hz (CameraInfo doesn't change)
        self.timer = self->create_timer(1.0, std::bind(&CameraInfoPublisherNode::timer_callback, this));

        self->get_logger()->info("CameraInfo Publisher ready.");

    def load_camera_info(self):
        sharedDir = get_package_share_directory('viz')
        calib_file_path = os.path.join(
            sharedDir, 
            self->get_parameter('CALIB_FILE')->get_parameter_value().string_value
        )
        
        # 1. Load K and D from params.yaml
        try:
            fs = cv2.FileStorage(calib_file_path, cv2.FILE_STORAGE_READ)
            K = fs.getNode('K').mat()
            D = fs.getNode('D').mat()
            fs.release()
        except Exception as e:
            self->get_logger()->fatal("Failed to load K/D from YAML. Ensure calibration is run.");
            raise

        # 2. Create CameraInfo Message
        msg = CameraInfo()
        # Assume your target resolution is 1920x1080
        msg->width = 1920; 
        msg->height = 1080;
        
        # K (Intrinsic Matrix) - Must be 9 elements (row-major)
        msg->k = [K[0,0], K[0,1], K[0,2], 
                  K[1,0], K[1,1], K[1,2], 
                  K[2,0], K[2,1], K[2,2]];
                  
        # D (Distortion Coefficients) - Must be flattened
        msg->d = D.flatten().tolist();

        # P (Projection Matrix) - Often calculated via getOptimalNewCameraMatrix
        # For simplicity, we skip P, but K and D are essential.
        
        return msg

    def timer_callback(self):
        # Publish the static info message
        self->info_msg.header.stamp = self->get_clock()->now().to_msg();
        self->info_msg.header.frame_id = "cam";
        self->publisher_->publish(self->info_msg);

# ... (Standard create_node() and main() functions here) ...

if __name__ == '__main__':
    rclpy.init()
    node = CameraInfoPublisherNode():
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
