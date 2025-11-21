#!/usr/bin/env python

import rclpy, logging
from rclpy.node import Node
from std_msgs.msg import Float64  # -12.0 a 12.0
import threading
from flask import Flask, jsonify
import time

FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_ROUTE = '/enc_status'

class MotorWebServerNode(Node):
    def __init__(self):
        super().__init__('FLASK_SOCKET')
        
        self.motor_voltage = 0.0
        self.lock = threading.Lock()

        self.subscription = self.create_subscription(
            Float64,
            '/motor_voltaje',
            self.listener_callback,
            10)
        self.get_logger().info('ROS2 Topic OK')

    def listener_callback(self, msg):
        with self.lock:
            self.motor_voltage = msg.data

app = Flask(__name__)
ros_node = None

@app.route(FLASK_ROUTE, methods=['POST'])
def enc_status():
    if ros_node is None:
        return jsonify({"error": "ROS Node not initialized"}), 500
    with ros_node.lock:
        current_voltage = ros_node.motor_voltage
    return jsonify({"voltage": current_voltage}), 200

def run_flask_server():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)

def main(args=None):
    global ros_node
    rclpy.init(args=args)

    ros_node = MotorWebServerNode()

    flask_thread = threading.Thread(target=run_flask_server)
    flask_thread.daemon = True
    flask_thread.start()
    ros_node.get_logger().info(f'http://{FLASK_HOST}:{FLASK_PORT}{FLASK_ROUTE} OK')

    try:
        rclpy.spin(ros_node) 
    except KeyboardInterrupt:
        ros_node.get_logger().info("Nodo ROS 2 detenido por usuario.")
    except Exception as e:
        ros_node.get_logger().error(f"Error durante el spinning de ROS 2: {e}")
    finally:
        if ros_node:
            ros_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
