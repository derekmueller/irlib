#! /usr/bin/env python
"""
h5dumpmeta - HDF5 metadata dump

Utility to write the metadata from raw radar data files to ASCII.
Data is sent to stdout by default or to csv/shapefile depending on args

Note that the csv file will output metadata for all traces.
The shapefile output (by necessity) will be only traces with lat/lon/elevation

"""
# standard libraries
import sys
import os.path
import glob
import traceback
import argparse
import io as StringIO
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString


def write_csv(data, outfile):
    data.to_csv(outfile + ".csv", sep=",", index=False)
    pass


def write_geopackage(data, outfile):
    data.to_file(outfile, driver="GPKG")
    pass


def write_geojson(data, outfile):
    data.to_file(outfile, driver="GeoJSON")
    pass


def write_kml(data, outfile):
    data.to_file(outfile, driver="KML")
    pass


def write_shapefile(data, outfile):
    data.to_file(outfile)
    pass


def meta2pd(infile, swap_lat=False, swap_lon=False):
    """
    Takes a single h5 file and dumps the metadata to a pandas dataframe

    Parameters
    ----------
    infile : str
        An h5 file name, with extension (with path or in current directory)
    swap_lat : bool, optional
        set to True if h5 ver <5 AND survey is in the Southern Hemisphere, DEFAULT: False
    swap_lon : bool, optional
        set to True if h5 ver <5 AND survey is in the Eastern Hemisphere, DEFAULT: False
    Returns
    -------
    a pandas dataframe with slightly different col names (10 char)

    """
    stringbuffer = StringIO.StringIO()

    try:
        irlib.misc.ExtractAttrs(
            infile,
            fout=stringbuffer,
            eastern_hemisphere=swap_lon,
            southern_hemisphere=swap_lat,
        )
    except:
        sys.stderr.write("Error reading radar data\n")
        raise

    stringbuffer.seek(0)
    meta = pd.read_csv(stringbuffer, header=0)

    # change column headings to be 10 chars or less  (could get rid of this if not using shapefiles)
    meta.rename(
        columns={
            "datacapture": "datacapt",
            "vertical_range": "vrange",
            "sample_rate": "samplerate",
        }
    )
    meta = meta.sort_values("FID")

    # format FID
    fid = ["{:0>16}".format(fid) for fid in meta.FID]
    meta.FID = fid

    return meta


## MAIN HERE  ###

parser = argparse.ArgumentParser()
parser.add_argument(
    "infile",
    help="input HDF (*.h5) filename, with or without path, if you use wildcards in linux, put this in quotes",
)
parser.add_argument(
    "-o",
    "--outfile",
    help="output file BASENAME (could include a path) [if missing, will be automatically generated] OR if you used a wildcard in your infile it will represent an output path",
)
parser.add_argument("-c", "--csv", help="create csv metadata file", action="store_true")
parser.add_argument(
    "-w", "--wpt", help="create a waypoint metadata geomatics file", action="store_true"
)
parser.add_argument(
    "-l", "--ln", help="create a line metadata geomatics file", action="store_true"
)
parser.add_argument(
    "-g",
    "--geopackage",
    help="output in geopackage format",
    action="store_true",
)
parser.add_argument(
    "-j",
    "--geojson",
    help="output in GeoJSON format",
    action="store_true",
)
parser.add_argument(
    "-k",
    "--kml",
    help="output in KML (Google Earth) format -- Note that there are sometimes type conversion bugs so this format is not recommended for wpts",
    action="store_true",
)
parser.add_argument(
    "-s",
    "--shapefile",
    help="output in Shapefile format",
    action="store_true",
)

parser.add_argument("--clobber", help="overwrite existing files", action="store_true")

parser.add_argument(
    "--swap_lon",
    action="store_true",
    help="Use if your h5 file if from Ice Radar version < 5 AND your survey is in the Eastern Hemisphere",
)
parser.add_argument(
    "--swap_lat",
    action="store_true",
    help="Use if your h5 file if from Ice Radar version < 5 AND your survey is in the Southern Hemisphere",
)


args = parser.parse_args()

try:
    import irlib.misc  # Delay import for speed
except ImportError:
    print("Cannot find irlib libraries, check your path/environment")

# Expand file list if there are wildcards
infiles = glob.glob(args.infile)
infiles.sort()
outfiles = [f.rsplit(".")[0] for f in infiles]

# interpret outfiles as a path if there is a wildcard in the infile list
if "*" in args.infile or "?" in args.infile:
    if args.outfile == None:
        args.outfile = "."
    outfiles = [os.path.join(args.outfile, fname) for fname in outfiles]

else:
    if len(infiles) == 1 and args.outfile:
        if args.outfile:
            outfiles[0] = args.outfile


# go through all files.
for i, infile in enumerate(infiles):
    sys.stderr.write("\n\n---\t" + infile + "\t---\n")

    if not os.path.isfile(infile):
        sys.stderr.write(infile + "does not exist \n")
        sys.exit(1)

    meta = meta2pd(infile)
    lines = meta.line.unique()
    print(f"File {infile} has {len(lines)} lines and {len(meta)} traces")
    for line in lines:
        print(
            f"Line {line}\t{len(meta.loc[meta.line == line])} traces \tFrom "
            f"{meta.loc[meta.line == line, 'timestamp'].min()} to "
            f"{meta.loc[meta.line == line, 'timestamp'].max()}"
        )

    print("\n")
    print("Sample metadata....")
    print("\n")
    print(
        meta
    )  # this will give users a sample of what is there without the long scroll
    print("\n")

    # Create geomatics layer for the metadata  (point first then line)
    meta_geom = meta.dropna(subset=["lon", "lat", "alt_asl"])
    proj = "EPSG:4326"  # Assuming WGS84
    # Creating a points while zipping 3 coordinates(3 dimension)
    if meta_geom.shape[0] == 0:
        print("No valid location data found - cannot generate shapefile(s)")
        continue
    pts_gdf = gpd.GeoDataFrame(
        meta_geom,
        geometry=gpd.points_from_xy(
            meta_geom.lon.astype(float),
            meta_geom.lat.astype(float),
            z=meta_geom.alt_asl,
            crs=proj,
        ),
    )
    # this is required to create geopackage output (the field name FID is reserved)
    pts_gdf.rename(columns={"FID": "ipr_FID"}, inplace=True)
    # this will remove a conversion error for kml (bit of a workaround for a suspected library problem)
    # KML files will give warnings about this and will be corrupt. If that happens run again with clobber
    # and see if the data fields are correct.
    pts_gdf["echogram"] = pts_gdf["echogram"].astype("Int64")

    # create a line dataframe
    lines = meta_geom.line.unique()  # finding all the unique object ids
    index_list = []
    geometry_list = []
    for ln in lines:  # looping through lines
        ln_df = meta_geom.loc[
            meta_geom.line == ln
        ]  # subsetting pandas dataframe to the specific object
        line = LineString(
            zip(ln_df.lon.astype(float), ln_df.lat.astype(float), ln_df.alt_asl)
        )
        index_list.append(ln)
        geometry_list.append(line)

    lines_gdf = gpd.GeoDataFrame(index=index_list, crs=proj, geometry=geometry_list)
    lines_gdf["lines"] = lines

    output_basename = outfiles[i]

    output_layers = {
        "csv": meta,
        "wpt": pts_gdf,
        "ln": lines_gdf,
    }

    output_formats = {
        "csv": {"ext": ".csv", "func": write_csv},
        "geopackage": {"ext": ".gpkg", "func": write_geopackage},
        "geojson": {"ext": ".geojson", "func": write_geojson},
        "kml": {"ext": ".kml", "func": write_kml},
        "shapefile": {"ext": ".shp", "func": write_shapefile},
    }

    # Example: flags for formats and data types, from user args
    formats_selected = [fmt for fmt in output_formats if getattr(args, fmt)]
    layers_selected = [layer for layer in output_layers if getattr(args, layer)]
    # csv layer is a kind of default, but special case
    if "csv" not in layers_selected:
        layers_selected.append("csv")
    layers_selected.sort()
    formats_selected.sort()

    # Flag some potential issues to user
    if not formats_selected:
        print("No file output requested\n")

    if (
        "wpt" not in layers_selected
        and "line" not in layers_selected
        and len(formats_selected) > 1
    ):
        print(
            "Geomatics file(s) not output, please specify if you want lines and/or point with --wpts and --lines\n"
        )

    for layer in layers_selected:
        for fmt in formats_selected:
            # This is to handle csv output (slightly different from others)
            if fmt == "csv" and layer == "csv":
                df = output_layers[layer]
                ext = output_formats[fmt]["ext"]
                write_func = output_formats[fmt]["func"]
                outname = f"{output_basename}{ext}"

                # test for clobber condition
                if os.path.exists(outname) and not args.clobber:
                    print(f"File {outname} exists. Use --clobber to overwrite.")
                    continue

                print(f"Writing {layer} as {fmt} to {outname}")
                write_func(df, outname)

            # These are not valid combinations
            elif fmt != "csv" and layer == "csv":
                continue
            # These are not valid combinations
            elif fmt == "csv" and (layer == "wpt" or layer == "ln"):
                continue
            # This part is for geom layers/formats
            else:
                df = output_layers[layer]
                ext = output_formats[fmt]["ext"]
                write_func = output_formats[fmt]["func"]
                outname = f"{output_basename}_{layer}{ext}"

                # test for clobber condition
                if os.path.exists(outname) and not args.clobber:
                    print(f"File {outname} exists. Use --clobber to overwrite.")
                    continue

                print(f"Writing {layer} as {fmt} to {outname}")
                write_func(df, outname)
