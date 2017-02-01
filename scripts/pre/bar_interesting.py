#!/usr/bin/env python3
# keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
# Copyright (C) 2016 Aleksa Sarai <cyphar@cyphar.com>
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

import numpy
import matplotlib as mpl
mpl.use("TkAgg")
if not os.getenv("DISPLAY"):
	mpl.use("Agg") # Hack to fix no display.
import matplotlib.pyplot as plt

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

def bin_campaigns(ax, data, nears=1):
	Cs = numpy.array([int(campaign) for bright in data for campaign in bright["campaigns"] if len(bright["nears"]) >= nears])
	bins = (Cs.max() - Cs.min()) + 2

	ax.hist(Cs, bins, label="$\geq$ %d stamps" % (nears,))
	if nears == 1:
		ax.annotate(r"$\sum = %d$" % (len(Cs),), xy=(3, 1), xycoords="data",
		            xytext=(0.8, 0.8), textcoords="axes fraction",
		            horizontalalignment="right", verticalalignment="left")

def main(ifile, config):
	with open(ifile) as f:
		data = json.load(f)

	fig = plt.figure(figsize=(5, 5), dpi=80)

	ax1 = latexify(fig.add_subplot("111"))
	for near in config.nears:
		bin_campaigns(ax1, data["data"], nears=near)

	ax1.legend(loc="upper right")
	plt.show()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generates a bar graph for all campaigns given a file output from find_interesting.py.")
	parser.add_argument("-n", "--near", dest="nears", type=int, nargs="+", default=[1], help="Add an overlay for the given minimum number of postage stamps.")
	parser.add_argument("csv", nargs=1)

	args = parser.parse_args()
	main(ifile=args.csv[0], config=args)
