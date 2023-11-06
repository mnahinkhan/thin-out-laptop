#!/usr/bin/env python3
import argparse
import hashlib
import os
import pathlib
import shutil
import sys
import time
from pathlib import Path

# This dir needs to exist.
SEAGATE_DIR = "/Volumes/files/thinning"  # change this to your Seagate directory

if not Path(SEAGATE_DIR).exists():
    print(f"Error: Seagate directory {SEAGATE_DIR} does not exist.")
    sys.exit(1)


# https://stackoverflow.com/a/43761127/8551394
def copystat(source, target):
    """copy stats (only) from source to target"""
    shutil.copystat(source, target)
    # copy owner and group
    st = os.stat(source)
    os.chown(target, st.st_uid, st.st_gid)


def exact_file_match(file1, file2):
    """Return True if the two files have the same content, False otherwise."""
    # Check md5 first, since it's fast.
    if get_file_md5(file1) != get_file_md5(file2):
        return False
    # Check file size next, since it's also fast.
    if os.path.getsize(file1) != os.path.getsize(file2):
        return False
    # Finally, check the content.
    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        return f1.read() == f2.read()


def evict(args):
    filename = args.file
    seagate_filename = filename + ".seagate"

    # check if the seagate file exists, and if so, whether it matches exactly
    if os.path.exists(seagate_filename):
        print(f"Error: A Seagate version of {filename} already exists.")
        sys.exit(1)

    try:
        md5hash = get_file_md5(filename)

        # copy the file to Seagate
        seagate_file_parent = (
            Path(SEAGATE_DIR) / md5hash[:2] / md5hash[2:4] / md5hash[4:]
        )
        seagate_file_path = Path(seagate_file_parent) / os.path.basename(filename)
        if seagate_file_path.exists():
            if exact_file_match(filename, seagate_file_path):
                print(
                    f"A Seagate version of {filename} already exists on the drive but has the same content..."
                )
                print("Will not copy again.")
            else:
                print(
                    "Error: A Seagate version of this file already exists and has different content."
                )
                sys.exit(1)
        else:
            seagate_file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(filename, seagate_file_path)

        # Verify MD5
        if md5hash != get_file_md5(seagate_file_path):
            print("Error: copying to Seagate did not work.")
            sys.exit(1)

        # add Seagate info to the original file
        with open(seagate_filename, "w") as f:
            # Here we want to write the seagate_file_path but without the SEAGATE_DIR
            # prefix, so that the file can be restored from anywhere.
            seagate_file_path_no_prefix = str(seagate_file_path).replace(
                SEAGATE_DIR + "/", ""
            )
            f.write(
                f"Seagate file path: {seagate_file_path_no_prefix}\nMD5 hash: {md5hash}"
            )

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

        # Add the SEAGATE_DIR prefix to the path. But if the path already has the prefix,
        # don't add it again.
        if (
            not seagate_file_path.startswith(SEAGATE_DIR)
            and not seagate_file_path.startswith("/Volumes/Files/thinning")
            and not seagate_file_path.startswith("/")
        ):
            seagate_file_path = os.path.join(SEAGATE_DIR, seagate_file_path)
        elif seagate_file_path.startswith("/Volumes/Files/thinning"):
            print("Adjusting old prefix to new prefix...")
            seagate_file_path = seagate_file_path.replace(
                "/Volumes/Files/thinning", SEAGATE_DIR
            )

        assert seagate_file_path.startswith(SEAGATE_DIR)
        print(seagate_file_path)

        # check if the file exists on Seagate
        if not os.path.exists(seagate_file_path):
            # Try to replace the hash digest so that there is a path separator after the first two characters and after the next two characters.
            # This is because the old version of this script did not include the path separators.
            seagate_file_path = seagate_file_path[len(SEAGATE_DIR) + 1 :]
            seagate_file_path = (
                seagate_file_path[:2]
                + "/"
                + seagate_file_path[2:4]
                + "/"
                + seagate_file_path[4:]
            )

            seagate_file_path = os.path.join(SEAGATE_DIR, seagate_file_path)
            print(seagate_file_path)

        assert seagate_file_path.startswith(SEAGATE_DIR)

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
    # Try the below operation five times before throwing exception, since it fails sometimes.
    for _ in range(5):
        try:
            os.rename(seagate_file_path, seagate_file_path + ".removable")
            break
        except OSError:
            # Sleep 0.1 seconds before trying again.
            time.sleep(0.1)

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
