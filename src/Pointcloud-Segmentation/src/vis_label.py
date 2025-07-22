import numpy as np
import open3d as o3d
import os

# Function to load the LiDAR point cloud data from a .bin file
def load_velodyne_data(pcd_file):
    if not os.path.isfile(pcd_file):
        raise RuntimeError(f"{pcd_file} does not exist!")
    # LiDAR point cloud data is stored as a 1x4 array per point (x, y, z, intensity)
    pcd = np.fromfile(pcd_file, dtype=np.float32).reshape(-1, 6)
    return pcd[:, :3]  # x, y, z

# Function to load the label data from a .label file
def load_labels(label_file):
    # Read the label file and return the labels as a numpy array
    labels = np.fromfile(label_file, dtype=np.uint32)
    return labels

# Function to map label IDs to RGB colors
def label_to_color(label):
    label_colors = {
        
        40: (128, 64, 128),   # Road
        48: (244, 35, 232),   # Sidewalk
        50: (70, 70, 70),     # Building
        4: (102, 102, 156),  # Wall
        5: (190, 153, 153),  # Fence
        80: (153, 153, 153),  # Pole
        81: (250, 170, 30),   # Traffic light
        82: (220, 220, 0),    # Traffic sign
        70: (107, 142, 35),   # Vegetation
        72: (152, 251, 152), # Terrain
        11: (70, 130, 180),  # Sky
        12: (220, 20, 60),   # Person
        10: (255, 0, 0),     # Car
        13: (0, 0, 142)      # Bus
    }
    #print(f"Label: {label}, Color: {label_colors.get(label, [0, 0, 0])}")  # Debugging print
    return label_colors.get(label, [0, 0, 0])  # Default to black if not found


# Function to visualize the colored point cloud
def visualize_colored_point_cloud(pcd_file, label_file):
    # Load the point cloud data
    points = load_velodyne_data(pcd_file)
    
    # Load the labels
    labels = load_labels(label_file)
    
    # Map the labels to colors
    colors = np.array([label_to_color(label) for label in labels]) / 255.0  # Normalize to [0, 1] range
    
    # Create an Open3D point cloud object
    pcd_o3d = o3d.geometry.PointCloud()
    pcd_o3d.points = o3d.utility.Vector3dVector(points)
    pcd_o3d.colors = o3d.utility.Vector3dVector(colors)
    
    # Visualize the point cloud
    o3d.visualization.draw_geometries([pcd_o3d])

# Example usage
if __name__ == "__main__":
    '''pcd_file = "data/velodyne_points/good_data/000005.bin"  # Path to your LiDAR point cloud file
    label_file = "data/labels/000005.label"  # Path to your label file'''
    pcd_file = "/media/litis/T5 EVO2/sequences/120113/velodyne/000000.bin"  # Path to your LiDAR point cloud file
    label_file = "/media/litis/T5 EVO2/sequences/120113/labels/000000.label"  # Path to your label file
    
    visualize_colored_point_cloud(pcd_file, label_file)
