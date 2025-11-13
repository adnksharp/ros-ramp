#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
import numpy as np
import cv2 as cv
import glob, os, yaml
from progress.bar import IncrementalBar
import time

class CalibratorNode(Node):
    def __init__(self):
        super().__init__('CALIBRATOR')
        
        self.declare_parameter('RAW_DIR', 'include/raw')
        self.declare_parameter('OUT_DIR', 'include/calib')
        self.declare_parameter('OUT_FILE', 'include/params.yaml')
        self.declare_parameter('BOARD_SIZE_W', 27)
        self.declare_parameter('BOARD_SIZE_H', 18)
        self.declare_parameter('SQUARE_SIZE', 7.0)
        
        sharedDir = get_package_share_directory('viz')
        
        rawDir = os.path.join(
            sharedDir,
            self.get_parameter('RAW_DIR').get_parameter_value().string_value
        )
        self.outDir = os.path.join(
            sharedDir, 
            self.get_parameter('OUT_DIR').get_parameter_value().string_value
        )
        self.file = os.path.join(
            sharedDir, 
            self.get_parameter('OUT_FILE').get_parameter_value().string_value
        )
        os.makedirs(self.outDir, exist_ok=True)

        self.get_logger().info('INIT')
        self.run_calibration(rawDir)
        self.get_logger().info('COMPLETE')
        rclpy.shutdown()

    def run_calibration(self, img_dir):
        squareSize = self.get_parameter('SQUARE_SIZE').get_parameter_value().double_value
        
        criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 80, 0.001)
        boardSize = (
            self.get_parameter('BOARD_SIZE_W').get_parameter_value().integer_value,
            self.get_parameter('BOARD_SIZE_H').get_parameter_value().integer_value
        )
        objPoints, imgPoints = [], []
        objP = np.zeros((boardSize[1] * boardSize[0], 3), np.float32)
        objP[:, :2] = np.mgrid[0:boardSize[0], 0:boardSize[1]].T.reshape(-1, 2) * squareSize

        rawDir = glob.glob(os.path.join(img_dir, '*.jpg'))
        
        if not rawDir:
            raise RuntimeError('No images')

        imgSize = None
        bar = IncrementalBar(f'[INFO] [{time.time()}] [CALIBRATOR]:', max=len(rawDir))
        for _ in rawDir:
            img = cv.imread(_)
            if img is None:
                self.get_logger().error(f"{_} NOT READED")
                continue

            imgGray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            imgSize = (imgGray.shape[1], imgGray.shape[0])
            ret, corners = cv.findChessboardCorners(imgGray, boardSize, None)

            if not ret:
                try:
                    os.remove(_)
                except:
                    continue
            else:
                corners2 = cv.cornerSubPix(imgGray, corners, (11, 11), (-1, -1), criteria)
                imgPoints.append(corners2)
                objPoints.append(objP)
                cv.drawChessboardCorners(img, boardSize, corners2, ret)
                cv.imwrite(os.path.join(self.outDir, os.path.basename(_)), img)
            bar.next()
        bar.finish()

        self.get_logger().warn(f"CALIBRATING...")
        rms, K, D, rvecs, tvecs = cv.calibrateCamera(objPoints, imgPoints, imgSize, None, None)
        self.save_calibration_to_yaml(rms, K, D, rvecs, tvecs)
        self.get_logger().info(f'CALIBRATION SUCCESSFUL.')
        self.get_logger().warn(f'RMS ERR: {rms:.4f}.')
        self.get_logger().info(f'{self.file.split("/")[-1]} CREATED')


    def save_calibration_to_yaml(self, rms, K, D, rvecs, tvecs):
        self.get_logger().warn(f'{self.file.split("/")[-1]} INIT')
        fs = cv.FileStorage(self.file, cv.FILE_STORAGE_WRITE)
        fs.write('rms', rms)
        fs.write('K', K)
        fs.write('D', D)
        fs.write('rvecs', np.concatenate(rvecs, axis=1))
        fs.write('tvecs', np.concatenate(tvecs, axis=1))
        fs.release()
        
def create_node():
    return CalibratorNode()

if __name__ == '__main__':
    rclpy.init()
    node = CalibratorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
