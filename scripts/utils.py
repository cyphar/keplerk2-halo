#!/usr/bin/false
# keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
# Copyright (C) 2015 Aleksa Sarai <cyphar@cyphar.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 2 of the GNU General Public
# License as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import csv

import numpy as np

def positions(ndarray):
	return zip(*np.where(np.ones_like(ndarray)))

def filter_img(img, track=None, frame=0):
	flxs = img[1].data["FLUX"]
	time = img[1].data["TIME"]
	qual = img[1].data["QUALITY"]
	cadn = img[1].data["CADENCENO"]
	trac = None

	# We need to fix up the times so they are in *absolute* BJD.
	time += img[1].header["BJDREFI"] + img[1].header["BJDREFF"]

	# Remove frames not in our track data.
	if track is not None:
		filt = np.in1d(cadn, [tr["cadence"] for tr in track])

		flxs = flxs[filt]
		time = time[filt]
		qual = qual[filt]
		cadn = cadn[filt]

		# Fix up track.
		trac = np.array(track)[np.in1d([tr["cadence"] for tr in track], cadn)]
		del track

	# Remove bad quality frames.
	filt = (qual == 0)
	flxs = flxs[filt]
	time = time[filt]
	cadn = cadn[filt]
	if trac is not None:
		trac = trac[filt]

	# Deal with NaNs.
	for flx in flxs:
		flx[np.isnan(flx)] = np.min(flx[~np.isnan(flx)])

	if trac is not None:
		# We set the first track as being at the given one, because then
		# the users can deal with specifiying their track point at a time t.
		trac = np.array([(tr["x"], tr["y"]) for tr in trac], dtype=float)
		trac[:, 0] -= trac[frame, 0]
		trac[:, 1] -= trac[frame, 1]

	return {
		"FLUX": flxs,
		"TIME": time,
		"CADENCENO": cadn,
		"TRACK": trac,
	}

def csv_column_read(f, fieldnames, casts=None, start=None, end=None, reset=False):
	if casts is None or len(fieldnames) != len(casts):
		casts = [object] * len(fieldnames)

	def parse_row(row):
		row = {k: v for k, v in row.items() if k in fieldnames}
		return [row[key] for key in sorted(row.keys(), key=lambda k: fieldnames.index(k))]

	if reset:
		pos = f.tell()

	reader = csv.DictReader(f)
	rows = [[cast(field) for cast, field in zip(casts, fields)] for fields in (parse_row(row) for row in reader)]

	if reset:
		f.seek(pos)

	return [np.array(col[start:end], dtype=cast) for cast, col in zip(casts, zip(*rows))]

def csv_column_write(f, cols, fieldnames):
	writer = csv.DictWriter(f, fieldnames=fieldnames)
	writer.writeheader()

	for fields in zip(*cols):
		writer.writerow({fieldnames[i]: field for i, field in enumerate(fields)})

SPINE_COLOR = "black"

def latexify(ax):
	for spine in ["top", "right"]:
		ax.spines[spine].set_visible(False)

	for spine in ["left", "bottom"]:
		ax.spines[spine].set_color(SPINE_COLOR)
		ax.spines[spine].set_linewidth(0.5)

	ax.xaxis.set_ticks_position("bottom")
	ax.yaxis.set_ticks_position("left")

	for axis in [ax.xaxis, ax.yaxis]:
		axis.set_tick_params(direction="out", color=SPINE_COLOR)

	return ax
