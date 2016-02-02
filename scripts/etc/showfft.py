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

import utils

def plot_fft(fig, config):
	CASTS = [float, float]
	FIELDS = ["frequency", config.pgtype]

	# Iterate over all inputs.
	nfiles = len(config.ifiles)
	for i, ifile in enumerate(config.ifiles):
		# Get the periodogram information.
		with open(ifile, "r", newline="") as f:
			fx, fy = utils.csv_column_read(f, FIELDS, casts=CASTS)

		# Create a latex axis.
		ax = utils.latexify(fig.add_subplot("%d%d%d" % (nfiles, 1, i + 1)))

		# Plot the periodogram.
		ax.plot(fx, fy, color="k", linestyle="-", marker="None")
		ax.set_axisbelow(True)
		ax.set_xlabel("Frequency ($\mu$Hz)")

		# Make sure the axis names are correct.
		if config.pgtype == "amplitude":
			ax.set_ylabel("Amplitude (ppm)")
		elif config.pgtype == "psd":
			ax.set_ylabel("PSD (ppm$^2$ $\mu$Hz$^{-1}$)")

		if config.maxx > config.minx >= 0:
			ax.set_xlim([config.minx, config.maxx])
		if config.maxy > config.miny >= 0:
			ax.set_ylim([config.miny, config.maxy])

	plt.legend()
	fig.tight_layout()

def main(config):
	plot_fft(plt.figure(figsize=(10, 6 * len(config.ifiles)), dpi=80), config)

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

		parser = argparse.ArgumentParser(description="Given a PSD or Amplitude Periodogram, generate a nice plot for it.")
		parser.add_argument("--min-x", dest="minx", type=float, default=0, help="Minimum x value for frequency.")
		parser.add_argument("--max-x", dest="maxx", type=float, default=0, help="Maximum x value for frequency.")
		parser.add_argument("--min-y", dest="miny", type=float, default=0, help="Minimum y value for frequency.")
		parser.add_argument("--max-y", dest="maxy", type=float, default=0, help="Maximum y value for frequency.")
		parser.add_argument("-t", "--type", dest="pgtype", action=PeriodogramTypeAction, default="amplitude", help="The type of periodogram in the file.")
		parser.add_argument("--save-fft", dest="fftout", type=str, default=None, help="The output file for the FFT data.")
		parser.add_argument("-s", "--save", dest="ofile", type=str, default=None, help="The output file.")
		parser.add_argument("csv", nargs="+")

		config = parser.parse_args()
		config.ifiles = config.csv
		main(config)

	__wrapped_main__()
