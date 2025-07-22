import numpy as np
import os
import cv2
from load_calibration import *
from segment_image import *
from tqdm import tqdm
import open3d as o3d

def main():
    pointcloud_files, image00_files = LoadData()
    cam_id = 0
    TVeloToCam = GetVeloToCam(cam_id=cam_id)
    GenerateLabelsOnly(pointcloud_files, image00_files, TVeloToCam, cam_id)
    return


def dsor_filter(points, mean_k=8, std_mul=1.0, range_mul=0.1):
    """
    Dynamic Statistical Outlier Removal filter (Python version)
    
    Args:
        points (np.ndarray): Nx3 array of xyz points.
        mean_k (int): Number of nearest neighbors to analyze.
        std_mul (float): Standard deviation multiplier for threshold.
        range_mul (float): Multiplier to scale threshold based on point range.
        
    Returns:
        filtered_points (np.ndarray): Filtered Nx3 points after DSOR.
    """
    # Build KDTree for nearest neighbor search
    pcd_o3d = o3d.geometry.PointCloud()
    pcd_o3d.points = o3d.utility.Vector3dVector(points)
    kdtree = o3d.geometry.KDTreeFlann(pcd_o3d)

    mean_distances = []

    # Compute mean distance to k neighbors for each point
    for i in range(len(points)):
        [_, idx, dists] = kdtree.search_knn_vector_3d(points[i], mean_k)
        # skip the first neighbor (the point itself)
        if len(dists) < mean_k:
            mean_distances.append(0)
        else:
            mean_distance = np.mean(np.sqrt(dists[1:]))
            mean_distances.append(mean_distance)
    mean_distances = np.array(mean_distances)

    # Calculate mean and stddev of mean distances
    mean = np.mean(mean_distances)
    stddev = np.std(mean_distances)

    # Base threshold
    distance_threshold = mean + std_mul * stddev

    filtered_indices = []
    for i, point in enumerate(points):
        range_dist = np.linalg.norm(point)
        dynamic_threshold = distance_threshold * range_mul * range_dist
        if mean_distances[i] < dynamic_threshold:
            filtered_indices.append(i)

    filtered_points = points[filtered_indices]
    return filtered_points
def LoadData():
    data_dir = "/media/litis/T5 EVO2/sequences/"
    image00_dir = os.path.join(data_dir, "120113/image_2")
    pointcloud_dir = os.path.join(data_dir, "120113/velodyne")
    
    image00_files = [os.path.join(image00_dir, f) for f in os.listdir(image00_dir)]
    pointcloud_files = [os.path.join(pointcloud_dir, f) for f in os.listdir(pointcloud_dir)]

    image00_files.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
    pointcloud_files.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
    
    return pointcloud_files, image00_files

def GetVeloToCam(cam_id):
    TCam0ToVelo, TCam_kToIMU = LoadTransformations()
    TVeloToCam = TransformVeloToCam(cam_id, TCam0ToVelo, TCam_kToIMU)

    kitti360Path = "data"
    fileCameraToVelo = os.path.join(kitti360Path, 'calibration', 'calib_cam_to_velo.txt')
    TVeloToCam = loadCalibrationRigid(fileCameraToVelo)
    return TVeloToCam

def GenerateLabelsOnly(pointcloud_files, image00_files, TVeloToCam, cam_id):
    intrinsics = GetIntrinsics(cam_id)
    TVeloToRect = np.matmul(intrinsics["R_rect"], TVeloToCam)
    label_save_dir = "/media/litis/T5 EVO2/sequences/120113/labels"
    seg_save_dir = "/media/litis/T5 EVO2/sequences/120113/seg"
    os.makedirs(seg_save_dir, exist_ok=True)

    for pcd_file in tqdm(pointcloud_files, desc="Processing Point Clouds"):
        file_name = os.path.splitext(os.path.basename(pcd_file))[0]
        label_file_path = os.path.join(label_save_dir, file_name + ".label")

        if os.path.exists(label_file_path):
            print(f"Label file already exists for {file_name}, skipping.")
            continue

        image_path = os.path.join("/media/litis/T5 EVO2/sequences/120113/image_2", file_name + ".png")
        seg_img = generate_segmentated_img(image_path)

        # Save segmentation image
        seg_img_path = os.path.join(seg_save_dir, file_name + ".png")
        cv2.imwrite(seg_img_path, seg_img)

        # Load points Nx4
        points = loadVelodyneData(pcd_file)

        # --- Apply DSOR filter here ---
        #points = dsor_filter(points, mean_k=5, std_mul=0.01, range_mul=0.05)

        # Project to image and save labels
        u, v, depth = ProjectToImage(points, intrinsics, TVeloToRect)
        u = u.astype(np.int32)
        v = v.astype(np.int32)
        SaveLabels(label_save_dir, pcd_file, seg_img, u, v, depth, intrinsics)
        
def SaveLabels(label_save_dir, pcd_file, seg_img, u, v, depth, intrinsics):
    os.makedirs(label_save_dir, exist_ok=True)
    file_name = os.path.splitext(os.path.basename(pcd_file))[0]
    label_file_path = os.path.join(label_save_dir, file_name + ".label")

    width = intrinsics["width"]
    height = intrinsics["height"]
    labels = np.zeros((len(depth),), dtype=np.uint32)

    for i in range(len(depth)):
        if 0 <= u[i] < width and 0 <= v[i] < height and 0 < depth[i] < 100:
            color = tuple(seg_img[v[i], u[i], :])
            labels[i] = map_color_to_label_id(color)

    labels.tofile(label_file_path)
    print(f"Saved labels to {label_file_path}")
def map_color_to_label_id(color):
    # 1) Your metainfo:
    classes = (
        'Bird','Ground Animal','Curb','Fence','Guard Rail','Barrier','Wall',
        'Bike Lane','Crosswalk - Plain','Curb Cut','Parking','Pedestrian Area',
        'Rail Track','Road','Service Lane','Sidewalk','Bridge','Building','Tunnel',
        'Person','Bicyclist','Motorcyclist','Other Rider','Lane Marking - Crosswalk',
        'Lane Marking - General','Mountain','Sand','Sky','Snow','Terrain',
        'Vegetation','Water','Banner','Bench','Bike Rack','Billboard','Catch Basin',
        'CCTV Camera','Fire Hydrant','Junction Box','Mailbox','Manhole','Phone Booth',
        'Pothole','Street Light','Pole','Traffic Sign Frame','Utility Pole',
        'Traffic Light','Traffic Sign (Back)','Traffic Sign (Front)','Trash Can',
        'Bicycle','Boat','Bus','Car','Caravan','Motorcycle','On Rails',
        'Other Vehicle','Trailer','Truck','Wheeled Slow','Car Mount','Ego Vehicle',
    )
    palette = [
        [165,42,42],[0,192,0],[196,196,196],[190,153,153],[180,165,180],
        [90,120,150],[102,102,156],[128,64,255],[140,140,200],[170,170,170],
        [250,170,160],[96,96,96],[230,150,140],[128,64,128],[110,110,110],
        [244,35,232],[150,100,100],[70,70,70],[150,120,90],[220,20,60],
        [255,0,0],[255,0,100],[255,0,200],[200,128,128],[255,255,255],
        [64,170,64],[230,160,50],[70,130,180],[190,255,255],[152,251,152],
        [107,142,35],[0,170,30],[255,255,128],[250,0,30],[100,140,180],
        [220,220,220],[220,128,128],[222,40,40],[100,170,30],[40,40,40],
        [33,33,33],[100,128,160],[142,0,0],[70,100,150],[210,170,100],
        [153,153,153],[128,128,128],[0,0,80],[250,170,30],[192,192,192],
        [220,220,0],[140,140,20],[119,11,32],[150,0,255],[0,60,100],
        [0,0,142],[0,0,90],[0,0,230],[0,80,100],[128,64,64],[0,0,110],
        [0,0,70],[0,0,192],[32,32,32],[120,10,10],
    ]
    # build dict: class_name -> (R,G,B)
    class2color = {cls: tuple(rgb) for cls, rgb in zip(classes, palette)}

    # 2) The **exact subset** you asked for, with fixed IDs:
    class_id_map = {
        'outlier':      1,   # this one isn’t in metainfo, keep your old RGB
        'Car':         10,
        'Bicycle':     11,
        'Bus':         13,
        'Motorcycle':  15,
        'On Rails':    16,
        'Truck':       18,
        'Other Vehicle': 20,
        'Person':      30,
        'Bicyclist':   31,
        'Motorcyclist':32,
        'Road':        40,
        'Parking':     44,
        'Sidewalk':    48,
        'Other-ground':49,   # also not in metainfo, you’ll keep your old RGB
        'Building':    50,
        'Fence':       51,
        'Other-structure':52,# not in metainfo → keep your old RGB
        'Lane-marking':60,   # not in metainfo → keep your old RGB
        'Vegetation':  70,
        'Trunk':       71,   # not in metainfo → keep old RGB
        'Terrain':     72,
        'Pole':        80,
        'Traffic-sign':81,   # not in metainfo → keep old RGB
        'Other-object':99,   # not in metainfo → keep old RGB
    }

    # 3) Build your final color→ID map:
    color_to_label = {}

    # For those in metainfo, pull their palette color:
    for cls, idnum in class_id_map.items():
        if cls in class2color:
            color_to_label[class2color[cls]] = idnum

    # For the “old” ones not in metainfo, add them by hand:
    # (these are the ones you originally had)
    color_to_label[(0,   0,   255)] = 1    # outlier
    color_to_label[(0, 128,   0)]   = 49   # Other-ground
    color_to_label[(128,   0, 128)] = 52   # Other-structure
    color_to_label[(0, 128, 128)]   = 60   # Lane-marking
    color_to_label[(255,128,255)]   = 81   # Traffic-sign
    color_to_label[(255,255,255)]   = 99   # Other-object
    color_to_label[(255,128,128)]   = 71   # Trunk

    # 4) Return, defaulting to 0:
    return color_to_label.get(tuple(color), 0)

def ProjectToImage(points, intrinsics, TVeloToRect):
    points[:, 3] = 1
    pointsCam = (TVeloToRect @ points.T).T[:, :3]
    return cam2image(pointsCam.T, intrinsics)

def loadVelodyneData(pcdFile):
    if not os.path.isfile(pcdFile):
        raise RuntimeError('%s does not exist!' % pcdFile)
    pcd = np.fromfile(pcdFile, dtype=np.float32).reshape(-1, 6)
    return pcd[:, :4]

def LoadTransformations():
    kitti360Path = "data"
    fileCameraToVelo = os.path.join(kitti360Path, 'calibration', 'calib_cam_to_velo.txt')
    fileCameraToPose = os.path.join(kitti360Path, 'calibration', 'calib_cam_to_pose.txt')
    TCam0ToVelo = loadCalibrationRigid(fileCameraToVelo)
    TCam_kToIMU = loadCalibrationCameraToPose(fileCameraToPose)
    return TCam0ToVelo, TCam_kToIMU

def TransformVeloToCam(cam_id, TCam0ToVelo, TCam_kToIMU):
    if cam_id == 0:
        return TCam0ToVelo
    TCam0ToIMU = TCam_kToIMU['image_00']
    TCam_idToIMU = TCam_kToIMU[f'image_{cam_id:02d}']
    return TCam0ToVelo @ np.linalg.inv(TCam0ToIMU) @ TCam_idToIMU
def cam2image(points, intrinsics):
        #print("But now, stacked column wise: ", points.shape)
        ndim = points.ndim
        if ndim == 2:
            points = np.expand_dims(points, 0)
        #print("With extra dimension at 0th axis: ",points.shape)
        # return  0, 0, 0
        points_proj = np.matmul(intrinsics["K"][:3,:3].reshape([1,3,3]), points)
        #print("Finally project onto the image plane: ", points_proj.shape)
        # After multiplication from K matrix, the 3rd coordinate from each point is not 1. 
        # For each pixel coordinate, it has a depth value in the 3rd coordinate.
        depth = points_proj[:,2,:]
        # print(depth)
        depth[depth==0] = -1e-6
        u = np.round(points_proj[:,0,:]/np.abs(depth)).astype(np.int64)
        v = np.round(points_proj[:,1,:]/np.abs(depth)).astype(np.int64)
        # print(v)
        # return  0, 0, 0
        if ndim==2:
            u = u[0]; v=v[0]; depth=depth[0]
        return u, v, depth

# Entry point
if __name__ == "__main__":
    main()

