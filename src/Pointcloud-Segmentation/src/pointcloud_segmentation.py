import os
import numpy as np
import open3d as o3d
from scipy.spatial.transform import Rotation as R

from gen_color_pcd import *
from load_calibration import *

def quaternion_to_matrix(x, y, z, qx, qy, qz, qw):
    rotation = R.from_quat([qx, qy, qz, qw])
    T = np.eye(4)
    T[:3, :3] = rotation.as_matrix()
    T[:3, 3] = [x, y, z]
    return T

def load_trajectory(file_path):
    """
    Load trajectory into a dictionary: {frame_id_str: 4x4 pose matrix}
    Format: 000000,-4.318761,0.052684,0.025194,0.0158821,-0.0070746,-0.3031023,0.9527994
    """
    trajectory = {}
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            tokens = line.strip().split(',')
            if len(tokens) != 8:
                continue
            try:
                frame_id, x, y, z, qx, qy, qz, qw = tokens
                T = quaternion_to_matrix(float(x), float(y), float(z),
                                         float(qx), float(qy), float(qz), float(qw))
                trajectory[frame_id] = T
            except ValueError:
                continue
    return trajectory

def extract_frame_id(file_path):
    """Extract frame ID as a zero-padded string (e.g., '000123')"""
    return os.path.splitext(os.path.basename(file_path))[0]

def GenSegAndRegisterPCDs(pointcloud_files, image00_files, cam_id, trajectory_file, register=True):
    trajectory = load_trajectory(trajectory_file)

    TVeloToCam = GetVeloToCam(cam_id=cam_id)
    intrinsics = GetIntrinsics(cam_id)
    TVeloToRect = np.matmul(intrinsics["R_rect"], TVeloToCam)

    big_pcd = o3d.geometry.PointCloud()
    vis = o3d.visualization.Visualizer()

    for pcd_file, image_path in zip(pointcloud_files, image00_files):
        frame_id = extract_frame_id(pcd_file)  # e.g., '000123'
        
        seg_pcd = ColorPCD(image_path, pcd_file, TVeloToRect, intrinsics, segmentation=True)

        if frame_id in trajectory:
            seg_pcd.transform(trajectory[frame_id])
            print(f"Frame {frame_id}: Pose applied")
        else:
            print(f"Frame {frame_id}: Pose not found")

        big_pcd.points.extend(seg_pcd.points)
        big_pcd.colors.extend(seg_pcd.colors)

        if len(big_pcd.points) == len(seg_pcd.points):  # First frame
            vis.create_window()
            vis.add_geometry(big_pcd)
        else:
            vis.update_geometry(big_pcd)

        
        render_option = vis.get_render_option()
        render_option.point_size = 1
        vis.poll_events()
        vis.update_renderer()

    #o3d.visualization.draw_geometries([big_pcd])
    
    vis.run()
    vis.destroy_window()
    return big_pcd

def main():
    pointcloud_files, image00_files = LoadData()
    cam_id = 0
    trajectory_file = os.path.join("data", "poses.csv")
    GenSegAndRegisterPCDs(pointcloud_files, image00_files, cam_id, trajectory_file, register=True)

if __name__ == '__main__':
    main()

