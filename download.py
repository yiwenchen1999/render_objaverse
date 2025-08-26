import objaverse
print(objaverse.__version__)
print('successfully imported objaverse')
import os
import json
import objaverse.xl as oxl
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Objaverse Loader Script with Custom Base Path")
parser.add_argument(
    "--base_path", 
    type=str, 
    default="/projects/vig/Datasets", 
    help="Base path where the objaverse dataset is located"
)
parser.add_argument(
    "--begin_uid", 
    type=int, 
    default=0, 
    help="Number of processes to use for downloading objects"
)
parser.add_argument(
    "--end_uid", 
    type=int, 
    default=1000, 
    help="Number of processes to use for downloading objects"
)
parser.add_argument(
    "--obj_list", 
    type=str, 
    default='all_objaverse_filtered_data.json', 
    help="which list to download, default is all_objaverse_filtered_data.json"
)

args = parser.parse_args()

# Set base path
objaverse.BASE_PATH = os.path.join(args.base_path, "objaverse")

__version__ = "<REPLACE_WITH_VERSION>"
objaverse._VERSIONED_PATH = os.path.join(objaverse.BASE_PATH, "hf-objaverse-v1")

# uids = objaverse.load_uids()
# print('successfully loaded uids')
# annotations = objaverse.load_annotations()
# print('successfully loaded annotations')
# cc_by_uids = [uid for uid, annotation in annotations.items() if annotation["license"] == "by"]
# print('successfully filtered cc by uids')
import multiprocessing
processes = multiprocessing.cpu_count()
print(f'number of processes: {processes}')
# Download a random sample of 100 object uids
import random
random.seed(42)
# # loading LVIS annotations
# lvis_annotations = objaverse.load_lvis_annotations()
# load the csv file
index_uid_list = []
# with open("filtered_uids.csv", "r") as f:
#     for line in f:
#         index, uid = line.strip().split(",")
#         index_uid_list.append((index, uid))
# print(f'successfully loaded lvis id list, of length: {len(index_uid_list)}')
if args.obj_list.endswith('.json'):
    with open(args.obj_list, 'r') as f:
        obj_list = json.load(f)
        index_uid_list = list(obj_list.keys())
    # Preview
    print(f"Loaded {len(index_uid_list)} entries")
    download_uids = index_uid_list[args.begin_uid:args.end_uid]

elif args.obj_list.endswith('.csv'):
    import csv
    csv_path = "filtered_uids.csv"
    index_uid_list = []
    with open(csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 2:
                index, uid = row
                index_uid_list.append((index.strip(), uid.strip()))
    # Preview
    print(f"Loaded {len(index_uid_list)} entries")

    download_uids = [uid for index, uid in index_uid_list[args.begin_uid:args.end_uid]]
objects = objaverse.load_objects(
    uids=download_uids,
    download_processes=2,
)
print('successfully loaded objects')
print(objects)