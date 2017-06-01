#!/usr/bin/env python3
# keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
# Copyright (C) 2017 Aleksa Sarai <cyphar@cyphar.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import csv
import sys
import numpy
import argparse
import operator

import astropy.io.fits

import shapely.ops
import shapely.wkt
import shapely.geometry
import shapely.affinity

import utils

def filter_img(config, img, track=None, frame=0):
	flxs = img[1].data["FLUX"]
	time = img[1].data["TIME"]
	qual = img[1].data["QUALITY"]
	cadn = img[1].data["CADENCENO"]
	trac = None

	# We need to fix up the times so they are in *absolute* BJD.
	time += img[1].header["BJDREFI"] + img[1].header["BJDREFF"]

	# Remove frames not in our track data.
	if track is not None:
		filt = numpy.in1d(cadn, [tr["cadence"] for tr in track])

		flxs = flxs[filt]
		time = time[filt]
		qual = qual[filt]
		cadn = cadn[filt]

		# Fix up track.
		trac = numpy.array(track)[numpy.in1d([tr["cadence"] for tr in track], cadn)]
		del track

	# Remove bad quality frames.
	filt = (qual == 0)
	flxs = flxs[filt]
	time = time[filt]
	cadn = cadn[filt]
	if trac is not None:
		trac = trac[filt]

	if trac is not None:
		# We set the first track as being at the given one, because then
		# the users can deal with specifiying their track point at a time t.
		trac = numpy.array([(tr["x"], tr["y"]) for tr in trac], dtype=float)
		trac[:, 0] -= trac[frame, 0]
		trac[:, 1] -= trac[frame, 1]

	flxs = flxs[config.start:config.end]
	time = time[config.start:config.end]
	cadn = cadn[config.start:config.end]
	if trac is not None:
		trac = trac[config.start:config.end]

	return {
		"FLUX": flxs,
		"TIME": time,
		"CADENCENO": cadn,
		"TRACK": trac,
	}

def postage_stamp(flux):
	ignore = ~numpy.any(numpy.isnan(flux), axis=0)

	polys = []
	for pos in zip(*numpy.where(ignore)):
		x, y = pos
		px = shapely.geometry.box(x, y, x + 1, y + 1)
		polys.append(px)

	return shapely.ops.cascaded_union(polys)

def new_mask(config, img):
	return postage_stamp(img["FLUX"])

# TODO: Check that we're not hitting off-by-one errors in the polygon code.
#       Looking at the animation, it looks like the mask is slightly off.
def polymask(mask):
	# XXX: Simplistic mask-to-polygon converter. No smoothing through grouping
	#      algorithms and convex hulls. It just makes a series of boxes for each
	#      selected pixel (with no weighting) and then unions them.

	SELECT_CHAR = "x"
	mask = numpy.array(mask, dtype=str)
	polys = []

	# Basically the same as postage_stamp but with 'mask == SELECT_CHAR'.
	for x, y in zip(*numpy.where(mask == SELECT_CHAR)):
		px = shapely.geometry.box(x, y, x + 1, y + 1)
		polys.append(px)

	return shapely.ops.cascaded_union(polys)

def ascii_mask(mfile):
	# We reverse it from the "friendly" syntax to the coordinate-correct
	# version. Should we do this? Probably not. Do we care? Nope.
	mask = [[ch for ch in line.rstrip("\n")] for line in mfile][::-1]

	# Double check that the mask is valid.
	try:
		assert len(set(len(row) for row in mask)) == 1
	except AssertionError:
		raise ValueError("mask file must have equal length lines")

	# Create polygon based on mask.
	return polymask(mask)

def moving_mask(config, img, mask):
	flux = img["FLUX"]
	trac = img["TRACK"]

	stamp = postage_stamp(flux)
	for i, flx in enumerate(flux):
		# XXX: Output some information to convince people we haven't frozen.
		sys.stdout.write(".")
		sys.stdout.flush()

		# Translate the aperture and mask out the edges outside the stamp.
		_mask = shapely.affinity.translate(mask, *-trac[i])
		_mask = _mask.intersection(stamp)
		_mask = shapely.affinity.translate(_mask, *trac[i])

		# Update mask.
		mask = _mask

	return mask

def prf_similarity(vec, flx, prf):
	x, y, mult = vec

def subtract_prf(config, img, img_orig, mask):
	flux = img["FLUX"]
	trac = img["TRACK"]

	prf = astropy.io.fits.open(config.prf)

	# TODO: We should interpolate the PRF to the co-ordinates of the target.
	prf = prf[1].data

	# Move the mask to the right

	return mask

MODE_INIT="init"
MODE_ASCII="ascii"
MODE_TRACK="track"
MODE_PRF="prf"

def main(config):
	img_orig = astropy.io.fits.open(config.fits)

	track = None
	if config.track is not None:
		with open(config.track) as f:
			# TODO: Fix this by using the utils version?
			def parse_row(cadence, x, y):
				return (cadence, float(x), float(y))

			# TODO: Fix this by not using fieldnames=XYZ.
			rows = csv.DictReader(f)

			# First row specifies the polarity.
			_, mx, my = parse_row(**next(rows))
			track = numpy.array([{"cadence": cadence, "x": x*mx, "y": y*my} for (cadence, x, y) in (parse_row(**row) for row in rows)])

	img = filter_img(config, img_orig, track=track)

	if config.mode == MODE_INIT:
		# Create a new mask.
		mask = new_mask(config, img)
	elif config.mode == MODE_ASCII:
		# Convert the mask.
		mask = ascii_mask(sys.stdin)
	else:
		# Open the base mask.
		mask = shapely.wkt.loads(sys.stdin.read())

	if config.mode == MODE_TRACK:
		mask = moving_mask(config, img, mask)
	elif config.mode == MODE_PRF:
		mask = subtract_prf(config, img, img_orig, mask)

	# For my own sanity.
	assert mask.equals(shapely.wkt.loads(shapely.wkt.dumps(mask)))

	if config.plot:
		import matplotlib
		matplotlib.use("TkAgg")
		import matplotlib.pyplot as plt
		def plot_bounds(ax, ob, zorder=1, alpha=1):
			x, y = ob.boundary.xy
			ax.plot(x, y, 'o', color="k", zorder=zorder, alpha=alpha)
		plot_bounds(plt, mask)
		plt.show()

	sys.stdout.write(shapely.wkt.dumps(mask))
	sys.stdout.flush()

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Automatically create halo photometry apertures given a FITS file, a base apeture and options.")
		parser.add_argument("-f", "--fits", dest="fits", required=True, help="The FITS file to use as the bounds.")
		parser.add_argument("--plot", action="store_true", help="Plot mask as a debugging step.")
		# Mode to run in.
		group = parser.add_mutually_exclusive_group(required=True)
		group.add_argument("--init", dest="mode", action="store_const", const=MODE_INIT, help="Create a new aperture, just based on the NaN mask.")
		group.add_argument("--from-ascii", dest="mode", action="store_const", const=MODE_ASCII, help="Convert an ascii aperture (asciify) to a proper shapely mask.")
		group.add_argument("--track", dest="mode", action="store_const", const=MODE_TRACK, help="Use tracking data to clip the edges of a mask to avoid edge cutting.")
		group.add_argument("--fit-prf", dest="mode", action="store_const", const=MODE_PRF, help="Fit a PRF to to a given frame and deduct it from the input mask.")
		# Cadence options
		parser.add_argument("-sc", "--start", dest="start", type=int, default=None, help="Start cadence (default: None).")
		parser.add_argument("-ec", "--end", dest="end", type=int, default=None, help="End cadence (default: None).")
		# Input file.
		parser.add_argument("--input", action="store_true", default=False, help="Read input from stdin")
		parser.add_argument("--prf", default=None)
		parser.add_argument("--frame", default=None, type=int, help="")
		parser.add_argument("-t", dest="track", type=str, help="A CSV File with (cadence, x, y) track data of the FITS file.")

		args = parser.parse_args()

		# This is going to be fun.
		if not operator.xor(args.mode in {MODE_INIT}, args.input):
			raise ValueError("--input is mutually exclusive with --init")
		if not operator.xor(args.mode in {MODE_PRF}, args.prf is None):
			raise ValueError("--fit-prf requires --prf")
		if not operator.xor(args.mode in {MODE_PRF}, args.frame is None):
			raise ValueError("--fit-prf requires --frame")
		if not operator.xor(args.mode in {MODE_PRF, MODE_TRACK}, args.track is None):
			raise ValueError("-t is necessary for --track and --fit-prf")

		main(args)

	__wrapped_main__()
