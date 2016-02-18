#!/usr/bin/env python3
# keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
# Copyright (C) 2016 Aleksa Sarai <cyphar@cyphar.com>
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

import os
import sys
import argparse

import matplotlib as mpl
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

import numpy
import utils

def plot_echelle(config, fig, ifile):
	CASTS = [float, float]
	FIELDS = ["frequency", config.pgtype]

	if config.deltanu is None:
		raise NotImplementedError("∆𝜈 autocorrelation not implemented")

	# Get the cadence information.
	with open(ifile, "r", newline="") as f:
		fx, fy = utils.csv_column_read(f, FIELDS, casts=CASTS)

	# Filter start and end.
	filt = numpy.ones_like(fx, dtype=bool)
	if config.start is not None:
		filt &= fx >= config.start * config.deltanu
	if config.end is not None:
		filt &= fx <= (config.end + 1) * config.deltanu

	fx = fx[filt]
	fy = fy[filt]

	# Convert from power to amplitude.
	if config.pgtype == "psd":
		pass
		#fy *= numpy.diff(fx).mean()
		#fy **= 0.5

	# First we bin the transform.
	width = config.smoothwidth
	bins = int(fx.ptp() // width)

	newfy = numpy.zeros(bins)
	for i in range(bins):
		rnge = (i*width <= fx) & (fx < (i+1)*width)
		newfy[i] = fy[rnge].sum()

	fy = newfy
	fx = numpy.linspace(fx.min(), fx.max(), bins)

	# Then we compute the grid sizes.
	delta = numpy.diff(fx).mean()
	rows = int(fx.ptp() // config.deltanu)
	cols = int(config.deltanu // delta)

	# Fill in the grid from the binned data.
	grid = numpy.zeros([rows, cols])
	for y, _ in enumerate(grid):
		grid[y,...] = fy[y*cols:(y+1)*cols]

	ax = utils.latexify(fig.add_subplot(111))
	#ax.imshow(-grid, cmap="gray", interpolation="nearest", origin="bottom")
	#ax.imshow(grid, cmap="viridis", interpolation="nearest", origin="bottom")
	ax.pcolormesh(grid, cmap="viridis")
	#ax.pcolormesh(-grid, cmap="gray")
	#ax.xaxis.set_ticks(numpy.arange)
	ax.xaxis.set_ticks
	ax.set_xlim([0, config.deltanu])
	ax.xaxis.set_ticks(numpy.arange(*ax.get_xlim(), step=20))
	ax.xaxis.set_ticks(numpy.arange(*ax.get_xlim(), step=5), minor=True)
	ax.set_ylim([config.start, config.end-config.start])
	ax.yaxis.set_ticks(numpy.arange(*ax.get_ylim(), step=1)+1)
	#ax.yaxis.set_ticks(numpy.arange(*ax.get_ylim(), step=0.25), minor=True)
	#ax.set_ylabel("Frequency ($\mu$Hz)")
	ax.set_ylabel("Mode Order")
	ax.set_xlabel("Frequency mod %s ($\mu$Hz)" % (config.deltanu,))

	plt.legend()
	fig.tight_layout()

def main(ifile, config):
	plot_echelle(config, plt.figure(figsize=(8, 10), dpi=50), ifile)

	if config.ofile:
		plt.savefig(config.ofile, transparent=True)
	else:
		plt.show()

if __name__ == "__main__":
	def __wrapped_main__():
		class PeriodogramTypeAction(argparse.Action):
			def __init__(self, option_strings, dest, nargs=None, **kwargs):
				if nargs is not None:
					raise ValueError("nargs not allowed")
				super().__init__(option_strings, dest, **kwargs)

			def __call__(self, parser, namespace, values, option_string=None):
				if values not in {"amplitude", "psd"}:
					raise ValueError("type needs to be 'psd' or 'amplitude'")
				setattr(namespace, self.dest, values)

		parser = argparse.ArgumentParser(description="Given an analysis, generate a light curve for the data.")
		parser.add_argument("-t", "--type", dest="pgtype", action=PeriodogramTypeAction, default="amplitude", help="The type of periodogram in the file.")
		parser.add_argument("-dn", "--delta-nu", dest="deltanu", type=float, default=None, help="∆𝜈 (default: computed using correlation function).")
		parser.add_argument("-w", "--smooth-width", dest="smoothwidth", type=float, default=1, help="The width of the transform binning (default: 1 µHz).")
		parser.add_argument("-so", "--start", dest="start", type=int, default=None, help="Start mode order (default: None).")
		parser.add_argument("-eo", "--end", dest="end", type=int, default=None, help="End mode order (default: None).")
		parser.add_argument("-s", "--save", dest="ofile", type=str, default=None, help="The output file.")
		parser.add_argument("csv", nargs=1)

		config = parser.parse_args()
		main(config.csv[0], config)

	__wrapped_main__()
