#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import TransformStamped
import tf2_ros
import os
from ament_index_python.packages import get_package_share_directory
import rclpy.duration

class ArucoVizNode(Node):
    def __init__(self):
        super().__init__('ARUCO_VIZ')
        
        self.declare_parameter('MARKER_SIZE_M', 0.05)
        self.declare_parameter('ARUCO_IDS', list(range(10))) 
        
        self.MZ = self.get_parameter('MARKER_SIZE_M').get_parameter_value().double_value
        self.IDS = self.get_parameter('ARUCO_IDS').get_parameter_value().integer_array_value
        
        self.share = get_package_share_directory('viz')
        self.uri = 'package://viz/models' 
        
        self.buff = tf2_ros.Buffer()
        self.threads = None 
        self.run = False
        
        self.pub = self.create_publisher(
            MarkerArray, 
            'visualization/aruco_array', 
            10
        )
        
        self.timer = self.create_timer(0.05, self.TimerCallback) 

        self.ONS = self.create_timer(1.0, self.TFCallback) 
        
        self.get_logger().info('ARUCO_VIZ Node ready. Waiting for TF init.')


    def TFCallback(self):
        self.ONS.cancel()
        
        try:
            self.threads = tf2_ros.TransformListener(self.buff, self)
            self.run = True 
            self.get_logger().info('TF Listener successfully initialized.')
            
        except Exception as e:
            self.get_logger().fatal(f"FATAL ERROR initializing TF Listener: {e}")
            rclpy.shutdown()


    def TimerCallback(self):
        if not self.run:
            return

        msg = MarkerArray()
        
        for mid in self.IDS:
            try:
                TFrame = f'aruco_{mid}'
                SFrame = 'cam' 
                
                transform = self.buff.lookup_transform(
                    SFrame, 
                    TFrame, 
                    rclpy.time.Time(), 
                    timeout=rclpy.duration.Duration(seconds=0.1) 
                )
                
                marker = self.markers(mid, transform)
                msg.markers.append(marker)

            except tf2_ros.LookupException:
                self.get_logger().debug(f"TF lookup failed for aruco_{mid}.")
                continue
            except tf2_ros.ExtrapolationException:
                continue
            except Exception as e:
                self.get_logger().debug(f"Unexpected error getting transform for aruco_{mid}: {e}")
                continue
        
        if msg.markers:
            self.pub.publish(msg)


    def markers(self, mid, transform):
        marker = Marker()
        
        marker.header.frame_id = transform.header.frame_id  
        marker.header.stamp = self.get_clock().now().to_msg()
        
        marker.ns = "aruco_objects"
        marker.id = mid
        marker.action = Marker.ADD

        marker.type = Marker.MESH_RESOURCE 
        
        mid_str = f"{mid:04d}"
        marker.mesh_resource = f'{self.uri}/{mid_str}.dae'

        marker.pose.position.x = transform.transform.translation.x
        marker.pose.position.y = transform.transform.translation.y
        marker.pose.position.z = transform.transform.translation.z
        
        marker.pose.orientation.x = transform.transform.rotation.x
        marker.pose.orientation.y = transform.transform.rotation.y
        marker.pose.orientation.z = transform.transform.rotation.z
        marker.pose.orientation.w = transform.transform.rotation.w

        marker.scale.x = 1.0 
        marker.scale.y = 1.0
        marker.scale.z = 1.0 
        
        marker.color.a = 1.0 
        marker.color.r = 1.0 if mid % 3 == 0 else 0.0
        marker.color.g = 1.0 if mid % 3 == 1 else 0.0
        marker.color.b = 1.0 if mid % 3 == 2 else 0.0
        
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
