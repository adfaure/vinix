"""Vinix

Usage:
  vinix treemap <store-path> [-o=<filename>]
  vinix graph <store-path> [-o=<filename>]
  vinix printsize <store-path>
  vinix csv <store-path> [-o=<filename>]

Options:
  -h --help     Show this screen.
  -o --output=<filename>   Name of the output file.
"""

import os
import subprocess
import sys
import tempfile
from subprocess import check_output

from docopt import docopt


def split_nix_derivation(store_path: str) -> str:
    basename = os.path.basename(store_path)
    if "-" in basename:
        splitted = basename.split("-")
        if len(splitted[0]) == 32:  # If its a store hash
            # For derivation without version...
            if len(splitted) == 2:
                return (splitted[0], splitted[1], "")
            else:
                return (splitted[0], splitted[1], splitted[2])

    return (basename, None, None)


def get_size(start_path: str):
    """Get the size of the folder `start_path`"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size


def print_graph(store_path, result_file):
    # Create a temporary file that should automatically be deleted
    mytmpfile = tempfile.NamedTemporaryFile()

    # Get the store reference of the store provided store path
    subprocess.call(
        "nix-store -q --graph {} > {}".format(store_path, mytmpfile.name), shell=True
    )
    subprocess.call("dot -Tpng -o {} {}".format(result_file, mytmpfile.name).split(" "))


def print_csv(store_path, result_file):
    # Get the store reference of the store provided store path
    output = check_output("nix-store -qR {}".format(store_path), shell=True)

    # Construct the data string that will be piped into the r script
    input_string = ""
    for path in output.decode().splitlines():
        size = get_size(path)
        if size == 0:
            # print("path {} is of size 0, skipping...".format(size))
            continue

        # Remove the hash of the path
        (nix_hash, package_name, version) = split_nix_derivation(path)
        input_string += "{},{},{},{}\n".format(size, nix_hash, package_name, version)

    with open(result_file, "w") as f:
        f.write("size,hash,name,version\n")
        f.write(input_string)


def print_treemap(store_path, result_file):
    # Get the store reference of the store provided store path
    output = check_output("nix-store -qR {}".format(store_path), shell=True)

    # Construct the data string that will be piped into the r script
    input_string = ""
    for path in output.decode().splitlines():
        size = get_size(path)
        if size == 0:
            print("path {} is of size 0, skipping...".format(size))
            continue

        # Remove the hash of the path
        (nix_hash, package_name, version) = split_nix_derivation(path)
        input_string += "{} {}\n".format(size, package_name)

    p = subprocess.Popen(
        ["print_treemap.R", result_file],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # Send the data to the R process
    output = p.communicate(input=input_string.encode())[0]


def print_total_size(store_path: str) -> int:
    # Get the store reference of the store provided store path
    output = check_output("nix-store -qR {}".format(store_path), shell=True)

    total_size = 0
    for path in output.decode().splitlines():
        total_size += get_size(path)

    return total_size


def main() -> int:
    arguments = docopt(__doc__, version="vinix 0.1.0")

    if "--output" in arguments and arguments["--output"] is not None:
        result_file = arguments["--output"]
    else:
        (nix_hash_or_name, package_name, version) = split_nix_derivation(
            arguments["<store-path>"]
        )
        if package_name is None:
            result_file = nix_hash_or_name
        else:
            result_file = package_name + "-" + version
        if arguments["treemap"] or arguments["graph"]:
            result_file += ".png"
        if arguments["csv"]:
            result_file += ".csv"

    if arguments["treemap"]:
        print_treemap(arguments["<store-path>"], result_file)
    elif arguments["csv"]:
        print_csv(arguments["<store-path>"], result_file)
    elif arguments["graph"]:
        print_graph(arguments["<store-path>"], result_file)
    elif arguments["printsize"]:
        print(
            "Total derivation size: {} (bytes)".format(
                print_total_size(arguments["<store-path>"])
            )
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
