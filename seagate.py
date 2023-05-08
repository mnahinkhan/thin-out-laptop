#!/usr/bin/env python3
import argparse
import hashlib
import os
import shutil
import sys

# This dir needs to exist.
SEAGATE_DIR = "/Volumes/Files/thinning"  # change this to your Seagate directory

# https://stackoverflow.com/a/43761127/8551394
def copystat(source, target):
    """copy stats (only) from source to target"""
    shutil.copystat(source, target)
    # copy owner and group
    st = os.stat(source)
    os.chown(target, st.st_uid, st.st_gid)


def evict(args):
    filename = args.file
    seagate_filename = filename + ".seagate"

    if os.path.exists(seagate_filename):
        print(f"Error: A Seagate version of {filename} already exists.")
        sys.exit(1)

    try:
        md5hash = get_file_md5(filename)

        # copy the file to Seagate
        seagate_file_parent = os.path.join(SEAGATE_DIR, md5hash)
        seagate_file_path = os.path.join(SEAGATE_DIR, md5hash, os.path.basename(filename))
        if os.path.exists(seagate_file_path):
            print(f"Error: A Seagate version of {filename} already exists on the drive.")
            sys.exit(1)

        if not os.path.exists(seagate_file_parent):
            os.mkdir(seagate_file_parent)

        shutil.copyfile(filename, seagate_file_path)

        # Verify MD5
        if md5hash != get_file_md5(seagate_file_path):
            print("Error: copying to Seagate did not work.")
            sys.exit(1)

        # add Seagate info to the original file
        with open(seagate_filename, "w") as f:
            f.write(f"Seagate file path: {seagate_file_path}\nMD5 hash: {md5hash}")

        copystat(filename, seagate_filename)

    except Exception as e:
        print(f"Error: Failed to copy {filename} to Seagate.")
        print(e)
        os.remove(seagate_file_path)  # since something went wrong
        sys.exit(1)

    # Everything went right.
    os.remove(filename)
    print(f"{filename} evicted to Seagate.")


def download(args):
    filename = args.file
    seagate_filename = filename + ".seagate"

    if not os.path.exists(seagate_filename):
        print(f"Error: No Seagate version of {filename} found.")
        sys.exit(1)

    try:
        # read the Seagate info from the .seagate file
        with open(seagate_filename, "r") as f:
            seagate_info = f.read().strip().split("\n")
            seagate_file_path = seagate_info[0].split(": ")[1]
            seagate_md5 = seagate_info[1].split(": ")[1]

        if os.path.exists(filename):
            print("Error: the file to be downloaded seems to already exist!")
            sys.exit(1)

        # copy the file from Seagate
        shutil.copyfile(seagate_file_path, filename)

        # verify the file's MD5 hash
        if get_file_md5(filename) != seagate_md5:
            print(f"Warning: {filename} does not match its Seagate version.")
            sys.exit(1)

        copystat(seagate_filename, filename)

    except:
        print(f"Error: Failed to copy {filename} from Seagate.")
        os.remove(filename)  # since something went wrong
        sys.exit(1)

    # everything went right
    os.remove(seagate_filename)
    os.rename(seagate_file_path, seagate_file_path + ".removable")
    print(f"{filename} restored from Seagate.")

def get_file_md5(filename):
    with open(filename, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

parser = argparse.ArgumentParser(description="Seagate file storage manager.")
subparsers = parser.add_subparsers(help="Subcommands", dest="subcommand")

evict_parser = subparsers.add_parser("evict", help="Evict a file to Seagate.")
evict_parser.add_argument("file", type=str, help="The name of the file to evict.")

download_parser = subparsers.add_parser("download", help="Restore a file from Seagate.")
download_parser.add_argument("file", type=str, help="The name of the file to restore.")

args = parser.parse_args()

if args.subcommand == "evict":
    evict(args)
elif args.subcommand == "download":
    download(args)
