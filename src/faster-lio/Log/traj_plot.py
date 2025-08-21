import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Load the data, using the first row as headers
data = pd.read_csv('traj.txt', delim_whitespace=True, header=0,
                   names=['timestamp', 'x', 'y', 'z', 'q_x', 'q_y', 'q_z', 'q_w'])

# Convert quaternion columns to floats to ensure numeric processing
data[['q_x', 'q_y', 'q_z', 'q_w']] = data[['q_x', 'q_y', 'q_z', 'q_w']].astype(float)

# Convert quaternion to Euler angles (roll, pitch, yaw)
data[['roll', 'pitch', 'yaw']] = data.apply(
    lambda row: R.from_quat([row['q_x'], row['q_y'], row['q_z'], row['q_w']]).as_euler('xyz', degrees=True),
    axis=1, result_type='expand')

# Initialize 3D plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plot trajectory (x, y, z positions)
ax.plot(data['x'], data['y'], data['z'], label='Trajectory', color='b')

# Plot orientation vectors (sample every few points for visibility)
for i in range(0, len(data), max(1, len(data)//100)):  # Skip points to reduce clutter
    x, y, z = data.loc[i, ['x', 'y', 'z']]
    q = [data.loc[i, 'q_x'], data.loc[i, 'q_y'], data.loc[i, 'q_z'], data.loc[i, 'q_w']]
    orientation = R.from_quat(q).as_matrix()  # Convert quaternion to rotation matrix
    
    # Draw orientation vector (scaled for visibility)
    scale = 0.1
    ax.quiver(x, y, z, orientation[0, 0]*scale, orientation[1, 0]*scale, orientation[2, 0]*scale, color='r')

# Labels and legend
ax.set_xlabel('X Position')
ax.set_ylabel('Y Position')
ax.set_zlabel('Z Position')
ax.legend()
plt.show()

