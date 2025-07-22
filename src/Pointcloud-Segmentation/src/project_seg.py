import numpy as np
import struct
import open3d as o3d
import os
import copy
import time
from load_calibration import *
import matplotlib.pyplot as plt
from PIL import Image
from scipy.ndimage import gaussian_filter
import cv2
from segment_image import generate_segmentated_img  # Your segmentation module

def main():
    projectVeloToImage()

def projectVeloToImage(cam_id=0, kitti360Path="data"):
    # Load calibration data
    fileCameraToVelo = os.path.join(kitti360Path, 'calibration', 'calib_cam_to_velo.txt')
    fileCameraToPose = os.path.join(kitti360Path, 'calibration', 'calib_cam_to_pose.txt')
    filePersIntrinsic = os.path.join(kitti360Path, 'calibration', 'perspective.txt')
    
    TrCam0ToVelo = loadCalibrationRigid(fileCameraToVelo)
    TrCamToPose = loadCalibrationCameraToPose(fileCameraToPose)
    TrVeloToCam = {}
    
    for k, v in TrCamToPose.items():
        TrCamkToCam0 = TrCamToPose['image_00'] @ np.linalg.inv(TrCamToPose[k])
        TrCamToVelo = TrCamkToCam0 @ TrCam0ToVelo
        TrVeloToCam[k] = np.linalg.inv(TrCamToVelo)
        TrVeloToCam[k] = loadCalibrationRigid(fileCameraToVelo)

    intrinsics = get_intrinsics(filePersIntrinsic, cam_id=cam_id)
    
    if cam_id == 0 or cam_id == 1:
        TrVeloToRect = np.matmul(intrinsics['R_rect'], TrVeloToCam['image_%02d' % cam_id])
    else:
        TrVeloToRect = TrVeloToCam['image_%02d' % cam_id]

    # Data directories
    data_dir_name = "good_data"
    pcd_dir = os.path.join("data/velodyne_points", data_dir_name)
    imgs_dir = os.path.join("data/image_00", data_dir_name)
    
    for file_name in os.listdir(pcd_dir):
        frame, _ = os.path.splitext(file_name)
        frame = int(frame)
        
        # Load point cloud
        points = loadVelodyneData(pcd_dir, frame)
        points[:, 3] = 1  # Homogeneous coordinates

        # Project to camera
        pointsCam = np.matmul(TrVeloToRect, points.T).T
        pointsCam = pointsCam[:, :3]
        u, v, depth = cam2image(pointsCam.T, intrinsics)
        u = u.astype(np.int64)
        v = v.astype(np.int64)

        # Create masks
        mask = np.logical_and(
            np.logical_and(np.logical_and(u >= 0, u < intrinsics["width"]), v >= 0),
            v < intrinsics["height"])
        mask = np.logical_and(np.logical_and(mask, depth > 0), depth < 30)

        # Load and process images
        imagePath = os.path.join(imgs_dir, '%06d.png' % frame)
        if not os.path.isfile(imagePath):
            raise RuntimeError('Image file %s does not exist!' % imagePath)
            
        colorImage = np.array(Image.open(imagePath)) / 255.
        seg_image = generate_segmentated_img(imagePath) / 255.  # Get segmentation colors

        # Create visualization
        fig, axs = plt.subplots(1, 3, figsize=(24, 8))
        
        # 1. Original image with depth points
        depth_map = np.zeros((intrinsics["height"], intrinsics["width"]))
        depth_map[v[mask], u[mask]] = depth[mask]
        depth_map = gaussian_filter(depth_map, sigma=5)
        
        axs[0].imshow(colorImage)
        axs[0].scatter(u[mask], v[mask], c=depth[mask], cmap='inferno', 
                      s=2, alpha=0.7, marker='o')
        axs[0].set_title('Original Image with Depth')
        axs[0].axis('off')
        
        # 2. Segmentation map
        axs[1].imshow(seg_image)
        axs[1].set_title('Semantic Segmentation')
        axs[1].axis('off')
        
        # 3. Segmented depth projection
        seg_depth = np.zeros((intrinsics["height"], intrinsics["width"], 3))
        for i in np.where(mask)[0]:
            seg_depth[v[i], u[i]] = seg_image[v[i], u[i]]
        
        # Smooth segmentation colors
        for c in range(3):
            seg_depth[:, :, c] = gaussian_filter(seg_depth[:, :, c], sigma=3)
        
        axs[2].imshow(colorImage)
        axs[2].imshow(seg_depth, alpha=0.6)
        axs[2].scatter(u[mask], v[mask], c=seg_image[v[mask], u[mask]], 
                      s=2, alpha=0.8, marker='o')
        axs[2].set_title('Segmented Depth Projection')
        axs[2].axis('off')
        
        plt.suptitle(f'Camera {cam_id:02d}, Frame {frame:06d}')
        plt.tight_layout()
        plt.show()

        # Create colored point cloud
        colored_points = []
        colors = []
        for i in np.where(mask)[0]:
            colored_points.append(points[i, :3])
            colors.append(seg_image[v[i], u[i]])
        
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.array(colored_points))
        pcd.colors = o3d.utility.Vector3dVector(np.array(colors))
        
        # Visualize point cloud
        print("Showing segmented point cloud...")
        o3d.visualization.draw_geometries([pcd])

# ... [Keep all other existing helper functions unchanged] ...

def loadVelodyneData(raw3DPcdPath,frame=0):
    pcdFile = os.path.join(raw3DPcdPath, '%06d.bin' % frame)
    if not os.path.isfile(pcdFile):
        raise RuntimeError('%s does not exist!' % pcdFile)
    pcd = np.fromfile(pcdFile, dtype=np.float32)
    pcd = np.reshape(pcd,[-1,6])
    #pcd = np.reshape(pcd,[-1,4])
    return pcd[:,:4]

def cam2image(points, intrinsics):
        ndim = points.ndim
        if ndim == 2:
            points = np.expand_dims(points, 0)
        points_proj = np.matmul(intrinsics["K"][:3,:3].reshape([1,3,3]), points)
        print('K= ', intrinsics["K"][:3,:3])
        depth = points_proj[:,2,:]
        depth[depth==0] = -1e-6
        u = np.round(points_proj[:,0,:]/np.abs(depth)).astype(np.int64)
        v = np.round(points_proj[:,1,:]/np.abs(depth)).astype(np.int64)

        if ndim==2:
            u = u[0]; v=v[0]; depth=depth[0]
        return u, v, depth

def get_intrinsics(intrinsic_file,cam_id = 0):
        ''' load perspective intrinsics '''
        
        intrinsics_dict = {}
        intrinsic_loaded = False
        width = -1
        height = -1
        with open(intrinsic_file) as f:
            intrinsics = f.read().splitlines()
        for line in intrinsics:
            line = line.split(' ')
            if line[0] == 'P_rect_%02d:' % cam_id:
                K = [float(x) for x in line[1:]]
                K = np.reshape(K, [3,4])
                intrinsic_loaded = True
            elif line[0] == 'R_rect_%02d:' % cam_id:
                R_rect = np.eye(4) 
                R_rect[:3,:3] = np.array([float(x) for x in line[1:]]).reshape(3,3)
            elif line[0] == "S_rect_%02d:" % cam_id:
                width = int(float(line[1]))
                height = int(float(line[2]))
        assert(intrinsic_loaded==True)
        assert(width>0 and height>0)
    
        intrinsics_dict["K"] = K
        intrinsics_dict["width"], intrinsics_dict["height"] = width, height
        intrinsics_dict["R_rect"] = R_rect
        return intrinsics_dict

if __name__ == '__main__':
    main()