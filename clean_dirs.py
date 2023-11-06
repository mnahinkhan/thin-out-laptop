#!/usr/bin/env python3
import sys
import os
from pathlib import Path

DIR_TO_CLEAN = sys.argv[1]

# This script runs on a directory containing direcoryies that have md5 hashes as names.
# This script will move all files of the form abcdefghijk/file.txt to ab/cd/efghijk/file.txt

# Go over every file in the directory that is one level deep at most
print("Starting to clean directory: " + DIR_TO_CLEAN)

for subdir, dirs, files in os.walk(DIR_TO_CLEAN):
    for file in files:
        # Get the full path of the file
        filepath = subdir + os.sep + file
        # Get the md5 hash of the file
        md5_hash = subdir.split("/")[-1]
        if subdir != DIR_TO_CLEAN + os.sep + md5_hash:
            print("Skipping " + filepath)
            continue
        # If the file starts with ._, skip it
        if file.startswith("._"):
            print("Skipping " + filepath)
            continue
        # Get the first two characters of the hash
        first_two = md5_hash[:2]
        # Get the next two characters of the hash
        next_two = md5_hash[2:4]
        # Get the rest of the characters of the hash
        rest = md5_hash[4:]
        # Get the new path of the file
        new_path = os.sep.join([DIR_TO_CLEAN, first_two, next_two, rest, file])
        # Move the file to the new path
        print("Moving " + filepath + " to " + new_path)
        # Create new directories if they don't exist
        Path(new_path).parent.mkdir(parents=True, exist_ok=True)
        os.rename(filepath, new_path)
        # Remove the old directory if it is empty
        if not os.listdir(subdir):
            print(f"Removing {subdir}")
            os.rmdir(subdir)
