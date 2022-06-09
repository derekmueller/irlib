Command-line Utilities
======================

The command-line utilities in *radar_tools* are useful for performing data
management and pre-processing tasks on HDF radar datasets, as well as for
performing basic data exploration and conversion tasks.

In general, typing any of the utilities without arguments yield invocation and
usage instructions that are printed to the screen. This section summarizes
individual tool's functionality.

Recommended data cleaning workflow
----------------------------------

The following steps are very helpful for data cleaning and streamlining
workflow. Some of the steps are prerequisites for subsequent
analyses, so **do this in the correct order**. It is really very
important that you **take notes on what you did so that your workflow
can be recreated later**. It is recommmend you open a document and copy paste
what you did from the terminal in there for safekeeping. Also, you can
copy the screen output there too. As you go be aware that some scripts
will overwrite files. Recommend that you use unique file names that
represent the step that you just completed.

-  ``h5_dumpmeta.py`` : examine metadata, visualize on a GPS
-  ``h5_consolidate`` : combining h5 files streamlines workflow, take notes
	of the lines you want to work with 
-  ``h5_replace_gps.py`` : if you have better GPS data use it to refine
	position
-  ``h5_add_utm.py`` : allows irlib to calculate distances easier using 
	cartesian coordinates
-  ``h5_dumpmeta.py`` : check that all is well by comaring to earlier
	metadata
-  ``h5_dumpmeta.py`` : generate caches to speed up data access and do
	some more metadata

Once this has been been completed the data is ready to be used for Ice Thickness
Determination.


Data management
----------------

h5_consolidate
~~~~~~~~~~~~~~

::

``h5_consolidate`` combines multiple datasets into a single dataset. In the
process, lines are re-numbered so that they stay in sequential order.
Concatenating datasets is useful, for example, to combine multiple surveys
collected on different days into a single file that is easier to manage (but
larger).

    SYNTAX: h5_consolidate INFILE1 INFILE2 [...] -o OUTFILE

		Combines multiple datasets (>1) into a single concatenated dataset.


h5_replace_gps
~~~~~~~~~~~~~~

::

If GPS data collected from the on-board receiver are missing or of poor
quality, they can be replaced by data from a hand-held GPS receiver. The data
from the hand-held receiver must be exported as or converted to GPX format,
which is a standard open format. Calling ``h5_replace_gps`` creates a copy of
the original dataset with the new coordinates inserted. Command-line flags can
be used to specify matching tolerances and which lines to work on.

    SYNTAX: h5_replace_gps infile outfile gpsfile {gpx,ppp} {iprgps,iprpc,both} [OPTIONS]
	
		This tool replaces the existing geographical data in a ice radar HDF
		database with data taken from a GPX file, e.g. obtained from a handheld or
		external GPS unit or from a CSV file, e.g. obtained from a PPP output of 
		GPS data

	Positional arguments:
		infile				input HDF (.h5) filename, with or without path, 
						for which GPS or PC timestamps exist
		outfile				output HDF (.h5) filename, with or without path, 
						if this file exists, it will be overwritten
		gpsfile				GPS filename(s), with enhanced location, with or 
						without path / wildcards
		{gpx,ppp}			Select which format the gps file is in - either 
						gpx or ppp
		{iprgps,iprpc,both}	Select which timestamp to match gps timestamps to 
		                    - iprgps (recommended), iprpc (if iprgps not available) 
							or both (use caution)

    Optional arguments:
		-t hh 	The hour offset (hh) of the GPR computer from UTC (default = 0)
		-l n    Work only on line (n); default works on all lines
		-d n 	Set the max time delta permissible for matching locations to 
				(n) seconds; default is 15 seconds
		-o n 	Adds an offset (n) to the elevations to account for the height of 
				GPS off the ice or different geoid, use a neg. number to 
				subtract.
		-n  	Replace coordinates in HDF with no appropriate supplementary GPS 
				counterpart with 'NaN'. By default, the original coordinates 
				are retained.
		-p  	Keep all coordinates positive (use with old h5 format where 
				coordinates are Lat_N and Long_W).
		

h5_add_utm
~~~~~~~~~~

::

``h5_add_utm`` uses the *pyproj* library to append projected UTM zone
coordinates to datasets that only include lon-lat coordinates. This is a
required step for many of the data processing operations that might be used
later.


    SYNTAX: h5_add_utm INFILE OUTFILE

        Replaces geographical coordinates in INFILE with UTM coordinates
        in OUTFILE. Does not perform any datum shift. Projection is calculated
        assuming that the data from neither from western Norway nor Svalbard.


The UTM zone is calculated based on a naive algorithm that is ignorant of the
exceptional UTM circumstances in the vicinity of western Norway and Svalbard.

Works with 2 formats from BSI HDF files: 
  	Old format - 
		
		Latitude and longitude data in BSI HDF files are unsigned. It 
		is assumed to be in the western hemisphere by default. Passing the --swap_lon 
		key forces longitudes to be interpretted from the eastern hemisphere.
		UTM projection is calculated assuming that the data from neither from western 
		Norway nor Svalbard.
		
	New format - 
		
		Latitude and longigude data in BSI HDF files are signed to indicate 
		hemisphere. If any lat or lon values are negative, the --swap_lon key is disabled

h5_generate_caches
~~~~~~~~~~~~~~~~~~

::

    SYNTAX: h5_generate_caches HDF_SURVEY [OPTIONS]

        -d [DIR]    cache directory (default: cache/)
        -g          fix static GPS issues
        -s          smoothen coordinates
        -b          remove blank traces caused by triggering failure
        -r          remove stationary traces by averaging all traces within # m 
					(defaults to 0 m or off), recommend 3 for L1 GPS
        -f          force regeneration of existing caches
        -q          silence standard output
        -e          print failed datacaptures
        --dc=[#]    specify datacapture (default: 0)
		-n 			remove traces with NaN coordinates
		-i			interpolate over NaN coordinates (overrides -n)
		-v			print failed datacaptures

Caching improves performance and is a very good idea. ``h5_generate_caches``
creates caches (``.ird`` files) for every line within a survey, and optionally
applies a number of pre-processing steps to the data:

    - **static gps correction**: attempt to recognize period when the GPS was
      in "static mode", and interpolate continuous positions.

    - **smoothen coordinates**: filter noisy position data

    - **remove blank traces**: exclude empty soundings from the cache

    - **remove stationary traces**: attempt to recognize period when the radar
      sled was motionless, and remove redundant soundings

``h5_generate_caches`` should be the last of the data management scripts to
run, because modifying the original HDF dataset won't affect the caches until
they are regenerated.


Exploration and conversion
---------------------------

h5_dumpmeta
~~~~~~~~~~~

::

``h5_dumpmeta`` exports the radar metadata to a CSV file or a shapefile. 
The actual sounding data is not included.


    SYNTAX: h5_dumpmeta infile [OPTIONS]

    Positional arguments:
		infile	input HDF (*.h5) filename, with or without path, if you use 
		wildcards in linux, put this in quotes

    Optional arguments:
		-o 		output file BASENAME [if missing, will be automatically 
				generated]
		-c 		create csv metadata file
		-w 		create a waypoint metadata shapefile
		-l 		create a line metadata shapefile
		--clobber  	overwrite existing files
		

h5_export
~~~~~~~~~

::

``h52a.py`` exports a line from HDF5 to an ASCII, REFLEX or BINARY file.


	SYNTAX: h5_export.py [-h] [-o OUTFILE] [-l LINE] [--clobber] 
	{ascii,binary,reflex} infile
	
	Positional arguments:
		{ascii,binary,reflex}	Select which format to export to - either ascii, 
							binary or reflex	
		infile				input HDF (.h5) filename, with or without path
	
	Optional arguments: 
		-o OUTFILE			output filename, basename only NO extension; 
							defaults to infile
		-l LINE				line number to export - defaults to all
		--clobber			overwrite existing files
		

h52mat
~~~~~~

::

``h52mat`` converts HDF data to a MATLAB ``.mat`` file. The filters from
``h5_generate_caches`` are available. For those who prefer MATLAB, the rest of
this document can be ignored.

    SYNTAX: h52mat SURVEYFILE OUTFILE [options]

    SURVEYFILE is the HDF5 file generated by IceRadar.
    OUTFILE is the anme of the *.mat file to be generated.

    Options:
        g		fix static GPS issues
        s       smoothen coordinates
        b       remove blank traces (trigger failure)
        r       remove stationary traces
        o       overwrite
        q       silence standard output


Thickness Determination
-----------------------

Once Data Management and Exploration and Conversion steps have been completed, the 
process of thickness determination can begin.

icepick2
~~~~~~~~

::

``icepick2`` allows for interaction with radargrams. See chapter 4 for full description.

	SYNTAX: icepick2 <HDF_survey> [-L line_number]


mergepicks
~~~~~~~~~~

::

	SYNTAX: mergepicks infile outdir oldpicks [OPTIONS]
	
	Positional arguments:
		infile		input HDF (.h5) filename
		outdir		subfolder where new picking files will be written
		oldpicks	folder where old picking files are found

    Optional arguments:
		-d			cache directory, default: cache/
		-n			will priviledge new picks over old picks in case 
					of conflict
		--dc 		specify datacapture, default: 0

joinradar
~~~~~~~~~

::

``join_radar`` combines information from picking, rating, offset, 
and HDF5 files, and computes ice thickness at each valid
observation location. You must have a subdirectory 'picking' to 
run this script If there is no rating directory, all picks will be 
processed with a rating of '-9' If there is a rating directory, ONLY 
lines with ratings will be processed. If there is no offsets directory, 
you can specify --offset that will be applied to all traces Caution--
This script will overwrite files in the results subdirectory.

	SYNTAX: join_radar.py [-h] [-v VELOCITY] [-q QUAL_MIN] [-c] [-w] [-o OFFSET] [-n] infile
	
	Positional Arguments:
		infile				input HDF (*.h5) filename, with or without path

	Optional Arguments:
		-v VELOCITY		radar velocity in ice, defaults to 1.68e8 m/s
		-q QUAL_MIN		the minimum rating value to include 1 to 5 (defaults to -9, 
						which signifies unrated picks)
		-c				create csv file with fid,lon,lat,elev,thickness,error
		-w				create a waypoint shapefile
		-o OFFSET		if no offsets directory exists, provide antenna offset (m) 
						for all traces
		-n				remove any trace that has no thickness data


icerate
~~~~~~~

::

``icerate`` is a tool that evaluates the quality of picks, see chapter 5 for 
full decription.

	SYNTAX: icerate -f file_name [-L line_number] [--pick pick_filename]
