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

def main(config):
	img = astropy.io.fits.open(config.fits)

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

	img = filter_img(config, img, track=track)

	if config.init:
		mask = new_mask(config, img)
	else:
		with open(config.input) as f:
			mask = shapely.wkt.loads(f.read())

	if config.track:
		mask = moving_mask(config, img, mask)

	# For my own sanity.
	assert mask.equals(shapely.wkt.loads(shapely.wkt.dumps(mask)))

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
		parser.add_argument("--init", dest="init", action="store_const", const=True, default=False, help="Create a new aperture, just based on the NaN mask.")
		parser.add_argument("-f", "--fits", dest="fits", required=True, help="The FITS file to use as the bounds.")
		parser.add_argument("-t", "--track", dest="track", type=str, help="A CSV File with (cadence, x, y) track data of the FITS file.")
		# Cadence options
		parser.add_argument("-sc", "--start", dest="start", type=int, default=None, help="Start cadence (default: None).")
		parser.add_argument("-ec", "--end", dest="end", type=int, default=None, help="End cadence (default: None).")
		# Input file.
		parser.add_argument("--input", default=None)

		args = parser.parse_args()

		if not operator.xor(args.init, args.input is not None):
			raise ValueError("--init and input are mutually exclusive")

		main(args)

	__wrapped_main__()
