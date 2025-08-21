import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Load the data
data = pd.read_csv('traj.txt', delim_whitespace=True, header=0,
                   names=['timestamp', 'x', 'y', 'z', 'q_x', 'q_y', 'q_z', 'q_w'])

# Plot Z position over time
plt.figure(figsize=(10, 5))
plt.plot(data['timestamp'], data['z'], label='Z Position', color='blue')
plt.xlabel('Timestamp (s)')
plt.ylabel('Z Position (m)')
plt.title('Z Position over Time')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

