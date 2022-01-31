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
        "--rtol",
        type=float,
        default=0.01,
        help="Relative comparison tolerance (default: 0.01)",
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=0.01,
        help="Absolute comparison tolerance (default: 0.01)",
    )
    parser.add_argument(
        "--dry",
        type=float,
        default=1e-4,
        help="Consider cells with volume (in m3) lower than this as 'dry'",
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
    parser.add_argument(
        "--time",
        type=int,
        default=-1,
        help="The index along the time axis to compare",
    )
    parser.add_argument(
        "--save_mapping",
        action="store_true",
        help="Whether to update the LHS (old) gridadmin with 'new_ids'.",
    )

    parser.add_argument(
        "lhs",
        nargs="?",
        default="old/results_3di.nc",
        help="Left-hand-side NetCDF file or (if --recursive) directory",
    )
    parser.add_argument(
        "lhs_grid",
        nargs="?",
        default="old/gridadmin.h5",
        help="Left-hand-side gridadmin file or (if --recursive) directory",
    )
    parser.add_argument(
        "rhs",
        nargs="?",
        default="new/results_3di.nc",
        help="Right-hand-side NetCDF file or (if --recursive) directory",
    )
    parser.add_argument(
        "rhs_grid",
        nargs="?",
        default="new/gridadmin.h5",
        help="Right-hand-side gridadmin file or (if --recursive) directory",
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


def patch_lhs(
    lhs: xarray.Dataset,
    lhs_grid: Path,
    rhs: xarray.Dataset,
    rhs_grid: Path,
    save_mapping: bool,
    dry: float,
):
    """Patch the left hand side (old) to match the new gridadmin"""
    # Node / line order
    node_mapping, line_mapping = create_grid_mapping(
        lhs_grid, rhs_grid, save=save_mapping
    )

    for name in ("Mesh2DNode_id", "Mesh2DLine_id", "Mesh1DNode_id", "Mesh1DLine_id"):
        lhs[name].values = map_ids(
            lhs[name].values,
            rhs[name].values,
            node_mapping if "Node" in name else line_mapping,
            name,
        )
        lhs = lhs.sortby(name)
    lhs = lhs.assign_coords({"time": rhs["time"].values})

    # sumax & zcc for boundary conditions are expected to be NaN
    is_bc_2d = lhs["Mesh2DNode_type"] == 5
    lhs["Mesh2DFace_sumax"].values[is_bc_2d] = np.nan
    lhs["Mesh2DFace_zcc"].values[is_bc_2d] = np.nan
    is_bc_1d = lhs["Mesh1DNode_type"] == 7
    lhs["Mesh1DNode_sumax"].values[is_bc_1d] = np.nan

    # in the old route there is no distinction between type 3 and 4
    rhs["Mesh1DNode_type"].values[rhs["Mesh1DNode_type"] == 4] = 3

    # if nodes are dry propagate that into s1 and su
    for ds in (lhs, rhs):
        dry = ds["Mesh1D_vol"] < dry
        ds["Mesh1D_vol"].values[dry] = 0.0
        ds["Mesh1D_s1"].values[dry] = -9999.0
        ds["Mesh1D_su"].values[dry] = 0.0
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
    lhs = patch_lhs(lhs, args.lhs_grid, rhs, args.rhs_grid, args.save_mapping, args.dry)
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
