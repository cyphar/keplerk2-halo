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
import argparse
import json
import utils

import numpy
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

def main(ifile, config):
	with open(ifile) as f:
		Bs, Vs, stamps, parallax = utils.csv_column_read(f, ["B", "V", "n_stamps", "parallax"], casts=[float, float, int, str])

	filt = [b != None and v != None and "~" not in p for b, v, p in zip(Bs, Vs, parallax)]
	Bs = Bs[filt]
	Vs = Vs[filt]
	stamps = stamps[filt]
	parallax = parallax[filt]

	fig = plt.figure(figsize=(5.7, 5.7), dpi=80)

	parallax = [float(p.split(" ")[0]) for p in parallax if p.split(" ")[0] != "~"]
	Mags = Vs + 5*(numpy.log10(parallax) + 1)
	colour = Bs - Vs

	ys = Mags
	xs = Bs - Vs

	eq0 = stamps == 0
	gt0 = stamps > 0

	ax1 = utils.latexify(fig.add_subplot("111"))
	ax1.scatter(xs[eq0], ys[eq0], marker="o", facecolors='None', edgecolors='b', label="$N_{stamps} = 0 ; \sum = %d$" % (eq0.sum(),))
	ax1.scatter(xs[gt0], ys[gt0], marker="s", facecolors='None', edgecolors='r', label="$N_{stamps} > 0 ; \sum = %d$" % (gt0.sum(),))
	ax1.set_xlabel("Colour Magnitude ($B-V$)")
	ax1.set_ylabel("Absolute V Magnitude")
	ax1.invert_yaxis()
	ax1.legend()

	fig.tight_layout()
	if config.ofile:
		plt.savefig(config.ofile, transparent=True)
	else:
		plt.show()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generates a HR diagram from a file output from find_interesting.py.")
	parser.add_argument("-s", "--save", dest="ofile", type=str, default=None, help="The output file.")
	parser.add_argument("csv", nargs=1)

	args = parser.parse_args()
	main(ifile=args.csv[0], config=args)
