import argparse
import h5py
import hdf5plugin
import progressbar
from prophesee_event_msgs.msg import EventArray, Trigger
import rosbag
import numpy as np

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert ROS bag to hdf5 for event streams')
    parser.add_argument('input_path', type=str, help='Input ROS bag path')
    parser.add_argument('output_path', type=str, help='Output HDF5 file path')
    args = parser.parse_args()
    
    input_data_path = args.input_path
    bag = rosbag.Bag(input_data_path, 'r')
    output_data_path = args.output_path
    event_file = h5py.File(output_data_path, 'w')
    
    # Create groups for each camera
    camera1_group = event_file.create_group('/camera1_master')
    camera2_group = event_file.create_group('/camera2_slave')

    # For progress bar
    total_messages = sum(1 for _ in bag.read_messages())
    bag.seek(0)  # Reset the read position
    bar = progressbar.ProgressBar(maxval=total_messages).start()
    
    # Temporary holders for events
    event_curr_idx = 0
    chunk_size = 100000
    event_x, event_y, event_p, event_t = [], [], [], []
    event_ms_to_idx = []

    trigger_timestamps = []
    trigger_polarities = []
    
    event_ms_idx = 0
    receive_event = False

    for i, (topic, msg, t) in enumerate(bag.read_messages(topics=[
        '/prophesee/camera1_master/cd_events_buffer',
        '/prophesee/camera2_slave/cd_events_buffer',
        '/prophesee/camera1_master/trigger_event'
    ])):
        bar.update(i + 1)

        if topic in ['/prophesee/camera1_master/cd_events_buffer', '/prophesee/camera2_slave/cd_events_buffer']:
            if topic == '/prophesee/camera1_master/cd_events_buffer':
                current_group = camera1_group
            else:
                current_group = camera2_group

            # Process events
            if not receive_event:
                receive_event = True
                event_t_offset = msg.events[0].ts
            
            for event in msg.events:
                event_x.append(event.x)
                event_y.append(event.y)
                event_p.append(event.polarity)
                event_t.append(int((event.ts.to_nsec() - event_t_offset.to_nsec()) / 1e3))
                
                while event_t[-1] >= 1000 * event_ms_idx:
                    event_ms_to_idx.append(event_curr_idx)
                    event_ms_idx += 1
                
                event_curr_idx += 1

            # Flush the holder temporarily
            if len(event_x) >= chunk_size:
                if 'events/t' not in current_group:
                    current_group.create_dataset('events/x', dtype='u2', maxshape=(None,), data=np.array(event_x, dtype='u2'), **hdf5plugin.Zstd())
                    current_group.create_dataset('events/y', dtype='u2', maxshape=(None,), data=np.array(event_y, dtype='u2'), **hdf5plugin.Zstd())
                    current_group.create_dataset('events/p', dtype='u1', maxshape=(None,), data=np.array(event_p, dtype='u1'), **hdf5plugin.Zstd())
                    current_group.create_dataset('events/t', dtype='u4', maxshape=(None,), data=np.array(event_t, dtype='u4'), **hdf5plugin.Zstd())
                else:
                    old_size = current_group['events/t'].shape[0]
                    new_size = len(event_t) + old_size
                    current_group['events/x'].resize((new_size,))
                    current_group['events/x'][old_size:] = np.array(event_x, dtype='u2')
                    current_group['events/y'].resize((new_size,))
                    current_group['events/y'][old_size:] = np.array(event_y, dtype='u2')
                    current_group['events/p'].resize((new_size,))
                    current_group['events/p'][old_size:] = np.array(event_p, dtype='u1')
                    current_group['events/t'].resize((new_size,))
                    current_group['events/t'][old_size:] = np.array(event_t, dtype='u4')
                
                event_x.clear()
                event_y.clear()
                event_p.clear()
                event_t.clear()

        elif topic == '/prophesee/camera1_master/trigger_event':
            # Process trigger messages
            trigger_timestamps.append(msg.ts.to_nsec())
            trigger_polarities.append(msg.polarity)

    # Flush the remaining data on holder for events
    for group in [camera1_group, camera2_group]:
        if 'events/t' in group:
            old_size = group['events/t'].shape[0]
            new_size = len(event_t) + old_size
            group['events/x'].resize((new_size,))
            group['events/x'][old_size:] = np.array(event_x, dtype='u2')
            group['events/y'].resize((new_size,))
            group['events/y'][old_size:] = np.array(event_y, dtype='u2')
            group['events/p'].resize((new_size,))
            group['events/p'][old_size:] = np.array(event_p, dtype='u1')
            group['events/t'].resize((new_size,))
            group['events/t'][old_size:] = np.array(event_t, dtype='u4')

    # Create trigger datasets under the camera1_group
    camera1_group.create_dataset('trigger/timestamps', dtype='u8', data=np.array(trigger_timestamps, dtype='u8'), **hdf5plugin.Zstd())
    camera1_group.create_dataset('trigger/polarities', dtype='u1', data=np.array(trigger_polarities, dtype='u1'), **hdf5plugin.Zstd())

    # Create the ms_to_idx dataset
    camera1_group.create_dataset('ms_to_idx', dtype='u8', data=np.array(event_ms_to_idx, dtype='u8'), **hdf5plugin.Zstd())
    camera1_group.create_dataset('t_offset', shape=(1,), dtype='i8', data=int(event_t_offset.to_nsec() / 1e3), **hdf5plugin.Zstd())

    bar.finish()
    event_file.close()

