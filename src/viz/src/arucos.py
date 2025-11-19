#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
from sensor_msgs.msg import Image
from geometry_msgs.msg import TransformStamped
import tf2_ros
from cv_bridge import CvBridge
import numpy as np
import cv2 as cv
import cv2.aruco as aruco
import os
import threading
import queue
from scipy.spatial.transform import Rotation as R_scipy
from ament_index_python.packages import get_package_share_directory

RESIZE_FACTOR = 0.5

def quaternion_from_matrix(R):
    r = R_scipy.from_matrix(R)
    return r.as_quat()

class ArucoDetectorNode(Node):
    def __init__(self):
        super().__init__('ARUCO_DETECTOR')
        
        self.declare_parameter('MARKER_SIZE_M', 0.05)
        self.declare_parameter('ARUCO_DICT', 'DICT_4X4_100')
        
        sharedDir = get_package_share_directory('viz')
        
        self.get_logger().info(f"Check newcam.npy")
        try:
            self.newcam = np.load(os.path.join(sharedDir, 'newcam.npy'))
        except Exception as e:
            self.get_logger().error(f"{e}")
            raise
        self.get_logger().info(f"file OK")
        
        try:
            self.markerSize = self.get_parameter('MARKER_SIZE_M').get_parameter_value().double_value
            dict_name = self.get_parameter('ARUCO_DICT').get_parameter_value().string_value

            self.dict = aruco.Dictionary_get(getattr(aruco, dict_name))
            self.params = aruco.DetectorParameters_create()

            self.bridge = CvBridge()
            self.transformer = tf2_ros.TransformBroadcaster(self)
            
            topic_name = f'image/aruco'
            self.pub = self.create_publisher(Image, topic_name, 10)
            self.poser = {}
            
            self.frame = queue.Queue(maxsize=1) 
            self.now = True
            self.thread = threading.Thread(target=self.processing_loop)
            self.thread.start()
            
            self.subscription = self.create_subscription(
                Image, '/camera/color/image_raw', self.image_callback, 10
            )
            self.get_logger().info('ARUCO_DETECTOR Node ready. Searching for markers...')
            
        except Exception as e:
            self.get_logger().fatal(f"FATAL ERROR DURING ARUCO SETUP: {e}")
            raise

    def image_callback(self, msg):
        try:
            if self.frame.full():
                self.frame.get_nowait()
            self.frame.put(msg)
        except queue.Empty:
            pass

    def processing_loop(self):
        while self.now:
            msg = None

            try:
                msg = self.frame.get(timeout=0.1) 
            except queue.Empty:
                continue
            except Exception as e:
                self.get_logger().error(f"Unexpected queue error: {e}")
                continue

            if msg:
                try:
                    cap = self.bridge.imgmsg_to_cv2(msg, "bgr8")
                except Exception as e:
                    self.get_logger().error(f"CvBridge error in thread: {e}")
                    continue
            
                if RESIZE_FACTOR != 1.0:
                    width = int(cap.shape[1] * RESIZE_FACTOR)
                    height = int(cap.shape[0] * RESIZE_FACTOR)
                    resized_cap = cv.resize(cap, (width, height), cv.INTER_AREA)
                else:
                    resized_cap = cap

                (corners, ids, rejected) = cv.aruco.detectMarkers(
                    resized_cap,
                    self.dict, 
                    parameters=self.params
                )
            
                if ids is not None:
                    markers = cap.copy()
                
                    if RESIZE_FACTOR != 1.0:
                        corners_orig_res = [c / RESIZE_FACTOR for c in corners] 
                    else:
                        corners_orig_res = corners

                    rvecs, tvecs, _ = cv.aruco.estimatePoseSingleMarkers(
                        corners_orig_res,
                        self.markerSize,
                        self.newcam,
                        np.array([]) 
                    )
                
                    for i in range(len(ids)):
                        cv.aruco.drawDetectedMarkers(markers, corners_orig_res)
                        cv.drawFrameAxes(markers, self.newcam, np.array([]), rvecs[i], tvecs[i], self.markerSize * 0.5)

                        self.pubTF(ids[i][0], rvecs[i], tvecs[i], msg.header)
                
                    self.pubImage(0, markers, msg.header)

    def pubTF(self, marker, rvec, tvec, header):
        t = TransformStamped()
        
        t.header.stamp = header.stamp
        t.header.frame_id = header.frame_id
        t.child_frame_id = f'aruco_{marker}'

        t.transform.translation.x = tvec[0, 0]
        t.transform.translation.y = tvec[0, 1]
        t.transform.translation.z = tvec[0, 2]

        R, _ = cv.Rodrigues(rvec)
        q = quaternion_from_matrix(R) 
        
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]

        self.transformer.sendTransform(t)

    def pubImage(self, marker, image, header):
        img_msg = self.bridge.cv2_to_imgmsg(image, encoding="bgr8")
        img_msg.header = header
        self.pub.publish(img_msg)


    def destroy_node(self):
        self.now = False
        if self.thread.is_alive():
            self.thread.join()
        super().destroy_node()

def create_node():
    return ArucoDetectorNode()

if __name__ == '__main__':
    rclpy.init()
    node = ArucoDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
