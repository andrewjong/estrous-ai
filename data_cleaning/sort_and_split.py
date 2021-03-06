DOC = """ This script moves images into separate subdirectories (folders) for \
train/validation/test sets. \
The images are additionally separated into folders by phase label.

This formats the data for PyTorch's torchvision.datasets.ImageFolder loader \
function:
https://pytorch.org/docs/stable/torchvision/datasets.html#imagefolder.

Be sure to delete existing files before rerunning the script!
"""
"""
The folder structure will look like this:
    train/
        proestrus/
        estrus/
        metestrus/
        diestrus/
    val/
        ...
    test/
        ...
"""
import argparse
import glob
import os
from random import Random
from shutil import copy2  # for copying files

import numpy as np
import pandas as pd
from tqdm import tqdm  # handy progress bar

cwd = os.getcwd()

# set up command line arguments
parser = argparse.ArgumentParser(description=DOC)
parser.add_argument("labels_file", help="CSV file containing the labels for each image")
parser.add_argument(
    "from_dir", help="Root directory of where the unsorted images currently are"
)
parser.add_argument(
    "to_dir",
    nargs='?',
    default=os.path.join("..", "data", "lavage"),
    help="OPTIONAL. Root directory of where to put the sorted \
                    images (default: '../data/lavage/')",
)
parser.add_argument(
    "-s",
    "--split",
    nargs=3,
    type=int,
    default=[70, 15, 15],
    help="Split percentages for train, validation, and test \
                    sets respectively. E.g. '70 15 15'. Numbers must add up \
                    to 100! (default: 70 train, 15 val, 15 test).",
)
parser.add_argument(
    "-g",
    "--grouped_classes",
    nargs='+',
    type=list,
    default=['1', '2', '3', '4'],
    help='Group phases into classes by phase number. The '
    + 'phase numbers for proestrus, estrus, metestrus, and '
    + 'diestrus are 1, 2, 3, and 4 respectively. E.g. passing '
    + 'in "123 4" would group proestrus-estrus-metestrus as '
    + 'one prediction class and diestrus as another.',
)
parser.add_argument(
    "-e",
    "--exclude",
    nargs='+',
    help='Exclude files with the specified strings in their \
                    file paths. E.g. "40x" would ignore all images with file \
                    paths containing "40x". Exclude strings are case \
                    insensitive.',
)
args = parser.parse_args()
# make sure split is valid, i.e. sums to 100
split_sum = sum(args.split)
assert split_sum == 100, (
    "Split percentages must sum to 100. Sum=" + str(split_sum) + "."
)


# map phase numbers to the correct phase label. this is for sorting the excel
# spreadsheet
PHASE_NUM_TO_LABEL = {
    '1': "proestrus",
    '2': "estrus",
    '3': "metestrus",
    '4': "diestrus",
}

# each label points to an array of filepaths to copy later
labels_to_files = {label: [] for label in PHASE_NUM_TO_LABEL.values()}

# read our spreadsheet
labels_df = pd.read_csv(args.labels_file, index_col=0, dtype=str)
print(f'Reading labels for {len(labels_df)} animals from ' + f'"{args.labels_file}".')

print(f'Reading images from "{args.from_dir}".')
print(f'Sorting files...')

# show a progress bar for file sorting
with tqdm(total=len(labels_df), unit="sort") as pbar:
    # iterate over each row in the dataframe (using itertuples for speed)
    for row in labels_df.itertuples():
        animal_label = str(row.Index)

        # iterate over each row's elements
        # (we iterate using the index because the "row" returned by itertuples
        # doesn't store the full column name. iterating by index does)
        for i in range(1, len(labels_df.columns)):
            # get the value in the cell
            phase_num = row[i]
            # make sure the cell isn't empty
            if not pd.isnull(phase_num):
                phase_label = PHASE_NUM_TO_LABEL[str(phase_num)]
                # (columns are offset by 1 as it lacks the animal label)
                date_label = str(labels_df.columns[i - 1])

                # images are named starting with "AnimalNumber_Date"
                f_name = animal_label + "_" + date_label
                # includes subdirectories in search with "**"
                search_glob = os.path.join(args.from_dir, "**", f_name + "*")
                # match each found file to the appropriate phase label
                for filepath in glob.glob(search_glob, recursive=True):
                    # make sure the filepath does not have any of the exclude
                    # words
                    if not args.exclude or all(
                        exclusion.lower() not in filepath.lower()
                        for exclusion in args.exclude
                    ):
                        labels_to_files[phase_label].append(filepath)

        pbar.update(1)

print(f'Copying files to "{args.to_dir}"...')

# calculate our split percentages
train_split_percent = .01 * args.split[0]
val_split_percent = .01 * args.split[1]

total_files_to_copy = sum(len(x) for x in labels_to_files.values())
# make another progress bar for copying files
with tqdm(total=total_files_to_copy, unit="copy") as pbar:
    # perform groupings for the specified class groups
    for group in args.grouped_classes:
        group = sorted(group)  # make consistent ordering
        group_labels = [PHASE_NUM_TO_LABEL[num] for num in group]
        # aggregate the labels for this group
        group_labels_to_files = {k: labels_to_files[k] for k in group_labels}

        # work with each label separately, to ensure proportionate
        # distribution of files
        for label, files in group_labels_to_files.items():
            # shuffle for fair training. use a seed on Random for consistency
            # in shuffling
            Random(42).shuffle(files)
            total_files = len(files)

            # divide into train, val, test sets
            train_stop = int(train_split_percent * total_files)
            train_files = files[:train_stop]

            val_stop = int((train_split_percent + val_split_percent) * total_files)
            val_files = files[train_stop:val_stop]

            test_files = files[val_stop:]

            # make sub directories for each sub dataset and label
            for split_set in ("train", "val", "test"):
                # make the directory for the given split set
                sorted_dir = os.path.join(
                    args.to_dir, split_set, "_".join(group_labels)
                )
                os.makedirs(sorted_dir, exist_ok=True)
                # put the appropriate files in the directory we made
                split_set_files = locals()[split_set + "_files"]
                for f in split_set_files:
                    copy2(f, sorted_dir)
                    pbar.update(1)

print("Done!")
