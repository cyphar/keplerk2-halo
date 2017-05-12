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

FIELDS = ["cadence", "x", "y"]
CASTS = [object, float, float]

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

def plot_track(ax, config, ifile):
	# Get the cadence information.
	with open(ifile, "r", newline="") as f:
		_, xs, ys = utils.csv_column_read(f, FIELDS, casts=CASTS, start=config.start, end=config.end)

	# Skip first row.
	xs = xs[1:] - xs[1]
	ys = ys[1:] - ys[1]

	ax.plot(xs, ys, color=config.color, linestyle="None", marker=config.marker, markeredgecolor="k", label=config.label)
	ax.set_xlabel(r"x offset (px)")
	ax.set_ylabel(r"y offset (px)")

def main(ifiles, config):
	fig = plt.figure(figsize=(5.7, 4.5), dpi=50)
	ax = utils.latexify(fig.add_subplot(111))
	for ifile in ifiles:
		config.marker = next(MARKERS)
		config.color = next(COLORS)
		# This is ugly.
		config.label = input("Label for %s: " % (ifile,))
		plot_track(ax, config, ifile)

	fig.tight_layout()
	plt.legend()

	if config.ofile:
		plt.savefig(config.ofile, transparent=True)
	else:
		plt.show()

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Plot a scatter of tracking data.")
		parser.add_argument("-sc", "--start", dest="start", type=int, default=None, help="Start cadence (default: None).")
		parser.add_argument("-ec", "--end", dest="end", type=int, default=None, help="End cadence (default: None).")
		parser.add_argument("-s", "--save", dest="ofile", type=str, default=None, help="The output file.")
		parser.add_argument("csv", nargs='+')

		config = parser.parse_args()

		main(config.csv, config)

	__wrapped_main__()
