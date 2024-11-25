import h5py
import sys
import hdf5plugin
def convert_hdf5_to_h5(input_file, output_file):
    with h5py.File(input_file, 'r') as hdf5_file:
        with h5py.File(output_file, 'w') as h5_file:
            # Copy all groups and datasets to the new file
            def copy_group(group, new_group):
                for key in group.keys():
                    item = group[key]
                    if isinstance(item, h5py.Group):
                        new_group.create_group(key)
                        copy_group(item, new_group[key])
                    else:
                        new_group.create_dataset(key, data=item[...])

            copy_group(hdf5_file, h5_file)
            print(f"Successfully converted {input_file} to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_hdf5_to_h5.py <input_file.hdf5> <output_file.h5>")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        convert_hdf5_to_h5(input_file, output_file)

