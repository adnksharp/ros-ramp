#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Vector3Stamped, PoseStamped, TransformStamped
import tf2_ros
import numpy as np
from collections import deque
import time

SIMULATED_DECELERATION_Y = 9.81

class BallKinematicsNode(Node):
    def __init__(self):
        super().__init__('BALL_KINEMATICS')
        
        self.declare_parameter('REFERENCE_FRAME', 'aruco_0')
        self.declare_parameter('TARGET_FRAME', 'red_ball')
        self.declare_parameter('PREDICTION_TIME', 0.5)
        self.declare_parameter('HISTORY_SIZE', 5)

        self.ref = self.get_parameter('REFERENCE_FRAME').get_parameter_value().string_value
        self.fball = self.get_parameter('TARGET_FRAME').get_parameter_value().string_value
        self.future = self.get_parameter('PREDICTION_TIME').get_parameter_value().double_value
        self.histories = self.get_parameter('HISTORY_SIZE').get_parameter_value().integer_value

        self.buff = tf2_ros.Buffer()
        self.calls = tf2_ros.TransformListener(self.buff, self)
        
        self.pcalls = deque(maxlen=self.histories)

        self.velPub = self.create_publisher(Vector3Stamped, '/ball/velocity_vector', 10)
        self.posePub = self.create_publisher(PoseStamped, '/ball/predicted_pose', 10)

        self.timer = self.create_timer(0.02, self.timer_callback) 
        
        self.get_logger().info('Ball Kinematics Node ready.')

    def timer_callback(self):
        try:
            transform = self.buff.lookup_transform(
                self.ref,
                self.fball,
                rclpy.time.Time()
            )
            
            t = self.get_clock().now().nanoseconds / 1e9
            
            x = transform.transform.translation.x
            y = transform.transform.translation.y
            z = transform.transform.translation.z
            
            self.pcalls.append((t, x, y, z))
            
            if len(self.pcalls) < 2:
                return
            
            vel_x, vel_y, vel_z = self.calculate_average_velocity()
            
            self.publish_velocity(vel_x, vel_y, vel_z, transform.header.stamp)

            self.predict_position(x, y, z, vel_x, vel_y, vel_z, transform.header.stamp)

        except tf2_ros.LookupException:
            self.get_logger().debug("Ball pose not available in TF buffer.")
            pass
        except Exception as e:
            self.get_logger().warn(f"Kinematics error: {e}")

    def calculate_average_velocity(self):
        t_new, x_new, y_new, z_new = self.pcalls[-1]
        t_old, x_old, y_old, z_old = self.pcalls[0]
        
        dt = t_new - t_old
        
        if dt < 1e-6:
            return 0.0, 0.0, 0.0

        vx = (x_new - x_old) / dt
        vy = (y_new - y_old) / dt
        vz = (z_new - z_old) / dt
        
        return vx, vy, vz
    
    def publish_velocity(self, vx, vy, vz, timestamp):
        msg = Vector3Stamped()
        msg.header.stamp = timestamp
        msg.header.frame_id = self.ref
        
        msg.vector.x = vx
        msg.vector.y = vy
        msg.vector.z = vz
        
        self.velPub.publish(msg)

    def predict_position(self, current_x, current_y, current_z, vx, vy, vz, timestamp):
        T = self.future
        A_y = SIMULATED_DECELERATION_Y
        
        predicted_x = current_x + (vx * T)
        
        predicted_y = current_y + (vy * T) - (0.5 * A_y * T * T)
        
        predicted_z = current_z + (vz * T) 

        msg = PoseStamped()
        msg.header.stamp = timestamp
        msg.header.frame_id = self.ref
        
        msg.pose.position.x = predicted_x
        msg.pose.position.y = predicted_y
        msg.pose.position.z = predicted_z
        
        msg.pose.orientation.w = 1.0 
        
        self.posePub.publish(msg)


def create_node():
    return BallKinematicsNode()

if __name__ == '__main__':
    rclpy.init()
    node = BallKinematicsNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
