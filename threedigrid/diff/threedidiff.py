"""Compare 2 3Di netcdf files, taking into account possibly reordered nodes / lines

This file was adjusted from:

URL: https://github.com/crusaderky/recursive_diff/blob/master/recursive_diff/ncdiff.py
Date: January 27, 2022
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List
import numpy as np

import xarray
from recursive_diff import recursive_diff

from .map_grid import create_grid_mapping, map_ids

LOGFORMAT = "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s"


def argparser() -> argparse.ArgumentParser:
    """Return precompiled ArgumentParser"""
    parser = argparse.ArgumentParser(
        description="Compare either two NetCDF files or all NetCDF files in "
        "two directories.",
        epilog="Examples:\n\n"
        "Compare two NetCDF files:\n"
        "  ncdiff a.nc b.nc\n"
        "Compare all NetCDF files with identical names in two "
        "directories:\n"
        "  ncdiff -r dir1 dir2\n",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--engine",
        "-e",
        help="NeCDF engine (may require additional modules)",
        choices=[
            "netcdf4",
            "scipy",
            "pydap",
            "h5netcdf",
            "pynio",
            "cfgrib",
            "pseudonetcdf",
        ],
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress logging")

    parser.add_argument(
        "--match",
        "-m",
        default="**/*.nc",
        help="Bash wildcard match for file names when using --recursive "
        "(default: **/*.nc)",
    )

    parser.add_argument(
        "--rtol",
        type=float,
        default=1e-9,
        help="Relative comparison tolerance (default: 1e-9)",
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=0,
        help="Absolute comparison tolerance (default: 0)",
    )

    brief = parser.add_mutually_exclusive_group()
    brief.add_argument(
        "--brief_dims",
        nargs="+",
        default=(),
        metavar="DIM",
        help="Just count differences along one or more dimensions instead of "
        "printing them out individually",
    )
    brief.add_argument(
        "--brief",
        "-b",
        action="store_true",
        help="Just count differences for every variable instead of printing "
        "them out individually",
    )
    brief.add_argument(
        "--time",
        type=int,
        default=-1,
        help="The index along the time axis to compare",
    )

    parser.add_argument(
        "lhs", help="Left-hand-side NetCDF file or (if --recursive) directory"
    )
    parser.add_argument(
        "lhs_grid", help="Left-hand-side gridadmin file or (if --recursive) directory"
    )
    parser.add_argument(
        "rhs", help="Right-hand-side NetCDF file or (if --recursive) directory"
    )
    parser.add_argument(
        "rhs_grid", help="Right-hand-side gridadmin file or (if --recursive) directory"
    )

    return parser


def open_netcdf(fname: str, engine: str = None) -> xarray.Dataset:
    """Open a single NetCDF dataset
    Read the metadata into RAM. Do not load the actual data.

    :param str fname:
        path to .nc file
    :param str engine:
        NetCDF engine (see :func:`xarray.open_dataset`)
    :returns:
        :class:`xarray.Dataset`
    """
    # At the moment of writing, h5netcdf is the only engine
    # supporting LZF compression
    logging.info(f"Opening {fname}")
    return xarray.open_dataset(fname, engine=engine)


def patch_lhs(lhs: xarray.Dataset, lhs_grid: Path, rhs: xarray.Dataset, rhs_grid: Path):
    """Patch the left hand side (old) to match the new gridadmin"""

    ## NODE / LINE order
    node_mapping, line_mapping = create_grid_mapping(lhs_grid, rhs_grid)

    lhs["Mesh2DNode_id"].values = map_ids(
        lhs["Mesh2DNode_id"].values, rhs["Mesh2DNode_id"].values, node_mapping, "nodes"
    )
    lhs["Mesh2DLine_id"].values = map_ids(
        lhs["Mesh2DLine_id"].values, rhs["Mesh2DLine_id"].values, line_mapping, "lines"
    )
    lhs = lhs.sortby("Mesh2DNode_id")
    lhs = lhs.sortby("Mesh2DLine_id")
    lhs = lhs.assign_coords({"time": rhs["time"].values})

    # sumax & zcc for BC are expected to be NaN
    is_bc = lhs["Mesh2DNode_type"] == 5
    lhs["Mesh2DFace_sumax"].values[is_bc] = np.nan
    lhs["Mesh2DFace_zcc"].values[is_bc] = np.nan
    return lhs


def get_time_n(lhs, rhs, n):
    return lhs.isel(time=n), rhs.isel(time=n)


def main(argv: List[str] = None) -> int:
    """Parse command-line arguments, load all files, and invoke recursive_diff

    :returns:
        exit code
    """
    # Parse command-line arguments and init logging
    args = argparser().parse_args(argv)
    if args.brief:
        args.brief_dims = "all"

    if args.quiet:
        loglevel = logging.WARNING
    else:
        loglevel = logging.INFO

    # Don't init logging when running inside unit tests
    if argv is None:
        logging.basicConfig(level=loglevel, format=LOGFORMAT)  # pragma: nocover

    # Load metadata of all NetCDF stores
    # Leave actual data on disk
    lhs = open_netcdf(args.lhs, engine=args.engine)
    rhs = open_netcdf(args.rhs, engine=args.engine)

    # Patch RHS so that nodes are in the same order as LHS
    lhs = patch_lhs(lhs, args.lhs_grid, rhs, args.rhs_grid)
    lhs, rhs = get_time_n(lhs, rhs, int(args.time))

    logging.info("Comparing...")
    # 1. Load a pair of NetCDF variables fully into RAM
    # 2. compare them
    # 3. print all differences
    # 4. free the RAM
    # 5. proceed to next pair
    diff_iter = recursive_diff(
        lhs, rhs, abs_tol=args.atol, rel_tol=args.rtol, brief_dims=args.brief_dims
    )

    diff_count = 0
    for diff in diff_iter:
        diff_count += 1
        print(diff)

    print(f"Found {diff_count} differences")
    if diff_count:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: nocover
