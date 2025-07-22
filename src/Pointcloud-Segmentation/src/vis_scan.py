import numpy as np
import open3d as o3d
import os
import matplotlib.pyplot as plt

def load_full_velodyne_data(pcd_file):
    if not os.path.isfile(pcd_file):
        raise RuntimeError(f"{pcd_file} does not exist!")
    return np.fromfile(pcd_file, dtype=np.float32).reshape(-1, 6)

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

def visualize_pointcloud_by_intensity(pcd_file, apply_dsor=False, mean_k=8, std_mul=1.0, range_mul=0.1):
    points_full = load_full_velodyne_data(pcd_file)
    points = points_full[:, :3]
    intensity = points_full[:, 3]

    if apply_dsor:
        points = dsor_filter(points, mean_k=mean_k, std_mul=std_mul, range_mul=range_mul)

    # Normalize intensity to [0, 1] (for filtered points, intensity is lost so recolor uniformly)
    if not apply_dsor:
        intensity_norm = (intensity - intensity.min()) / (intensity.max() - intensity.min() + 1e-8)
        cmap = plt.get_cmap('viridis')
        colors = cmap(intensity_norm)[:, :3]
    else:
        # When filtering, no intensity info preserved; use uniform color (e.g., white)
        colors = np.ones((points.shape[0], 3)) * 0.1

    pcd_o3d = o3d.geometry.PointCloud()
    pcd_o3d.points = o3d.utility.Vector3dVector(points)
    pcd_o3d.colors = o3d.utility.Vector3dVector(colors)

    o3d.visualization.draw_geometries([pcd_o3d], window_name="LiDAR Intensity Colored Point Cloud")

if __name__ == "__main__":
    pcd_file = "/media/litis/T5 EVO2/sequences/120113/velodyne/000690.bin"
    # Set apply_dsor=True to apply the dynamic statistical outlier removal
    visualize_pointcloud_by_intensity(pcd_file, apply_dsor=True, mean_k=5, std_mul=0.01, range_mul=0.05)

