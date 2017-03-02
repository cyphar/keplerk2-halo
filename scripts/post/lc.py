#!/usr/bin/env python3
# keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
# Copyright (C) 2015 Aleksa Sarai <cyphar@cyphar.com>
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

import os
import sys
import math
import argparse
import itertools

import matplotlib as mpl
mpl.use("TkAgg")
if not os.getenv("DISPLAY"):
	mpl.use("Agg") # Hack to fix no display.
import matplotlib.pyplot as plt

mpl.rcParams.update({
	"backend": "ps",
	"text.latex.preamble": [r"\usepackage{gensymb}"],
	"axes.labelsize": 13, # fontsize for x and y labels (was 10)
	"axes.titlesize": 13,
	"font.size": 13, # was 10
	"legend.fontsize": 13, # was 10
	"xtick.labelsize": 13,
	"ytick.labelsize": 13,
	"font.family": "serif", # ???
})

import numpy as np

import utils

FIELDS = ["t", "flux"]
CASTS = [float, float]

COLORS = itertools.cycle(["0.5", "r", "b", "g"])
MARKERS = itertools.cycle(["o", "s", "^"])

def description(config):
	desc = []

	if config.start or config.end:
		desc.append("[$%s$:$%s$]" % (config.start or r"0", config.end or r"\infty"))
	if config.period:
		desc.append("period=%.6f" % (config.period,))
	if config.bins:
		desc.append("bins=%d" % (config.bins,))

	return str.join(" ", desc)

def amplitude(ys):
	return (np.max(ys) - np.min(ys)) / 2

# TODO: Make this calling convention prettier.
def plot_lc(ax, config, ifile):
	# Get the cadence information.
	with open(ifile, "r", newline="") as f:
		times, fluxs = utils.csv_column_read(f, FIELDS, casts=CASTS, start=config.start, end=config.end)

	# Times and fluxes.
	xs = times
	ys = fluxs

	# Convert flux to ppm.
	ys = ys / ys.mean() - 1
	#ys *= 1e6

	if config.period is not None:
		# TODO: We should allow for showing more than one phase.
		xs = (xs % config.period) / config.period
		xs = (xs + config.phase) % 1.0

	# Bin the folded phase plot by taking the average of ranges.
	if config.bins is not None:
		size = 1.0 / config.bins
		nys = np.zeros(config.bins)

		for i in range(config.bins):
			rnge = (i*size <= xs) & (xs < (i+1)*size)
			nys[i] = np.median(ys[rnge])

		ys = nys
		xs = np.arange(config.bins) * size

	# Replication.
	# TODO: Make this code less insane and work for fractional width.
	if config.period is not None:
		ceilwidth = math.ceil(config.width)
		xs = np.tile(xs, ceilwidth) + np.repeat(np.arange(ceilwidth), xs.shape[0])
		ys = np.tile(ys, ceilwidth)
		ax.set_xlim([0, config.width])

	if not (config.period or config.bins):
		ax.plot(xs, ys, color="0.5", linestyle="-", marker="None")
		#ax.plot(xs, ys, color="k", linestyle="None", marker="+", label=r"Kepler/K2 Halo Photometry")
		ax.set_xlabel("Time ($d$)")
	else:
		ax.plot(xs, ys, color=config.color, linestyle="None", marker=config.marker, markeredgecolor="k", label=config.label)
		ax.set_xlabel("Phase")
	ax.set_ylabel(r"Relative Intensity")

	if config.title:
		ax.set_title(r"Light Curve [%s] # %s" % (description(config), config.comment or ""))

def main(ifiles, config):
	fig = plt.figure(figsize=(5.7, 4.5), dpi=50)
	ax = utils.latexify(fig.add_subplot(111))
	for ifile in ifiles:
		config.marker = next(MARKERS)
		config.color = next(COLORS)
		# This is ugly.
		config.label = input("Label for %s: " % (ifile,))
		plot_lc(ax, config, ifile)

	fig.tight_layout()
	plt.legend()

	if config.ofile:
		plt.savefig(config.ofile, transparent=True)
	else:
		plt.show()

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Given an analysis, generate a light curve for the data.")
		parser.add_argument("-title", "--title", dest="title", action="store_const", const=True, default=True, help="Enable titles (default).")
		parser.add_argument("-notitle", "--no-title", dest="title", action="store_const", const=False, default=True, help="Disable titles.")
		parser.add_argument("-c", "--comment", dest="comment", type=str, default=None, help="Comment to add to the title (default: None).")
		parser.add_argument("-sc", "--start", dest="start", type=int, default=None, help="Start cadence (default: None).")
		parser.add_argument("-ec", "--end", dest="end", type=int, default=None, help="End cadence (default: None).")
		parser.add_argument("-fp", "--folding-period", dest="period", type=float, default=None, help="The folding period of the light curve (default: None).")
		parser.add_argument("-w", "--width", dest="width", type=float, default=1, help="The phase width displayed (default: 1).")
		parser.add_argument("-po", "--phase-offset", dest="phase", type=float, default=0, help="Amount by which to phase shift the light curve (default: 0).")
		parser.add_argument("-b", "--bins", dest="bins", type=int, default=None, help="The number of bins to bin the folded light curve (default: none).")
		parser.add_argument("-s", "--save", dest="ofile", type=str, default=None, help="The output file.")
		parser.add_argument("csv", nargs='+')

		config = parser.parse_args()

		main(config.csv, config)

	__wrapped_main__()
