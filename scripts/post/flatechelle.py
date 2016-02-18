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
import scipy
import scipy.signal
import scipy.interpolate
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
		#pass

	# Convert to wrapped echelle.
	fx += config.off
	fx %= config.deltanu

	# Sort the arrays.
	sfilt = numpy.argsort(fx)
	fx = fx[sfilt]
	fy = fy[sfilt]

	# Smooth using a Savgol filter.
	#itp = scipy.interpolate.interp1d(fx, fy, kind='linear')
	#fy = scipy.signal.savgol_filter(itp(fx), config.width, 6)
	win = scipy.signal.boxcar(config.width)
	fy = scipy.signal.convolve(fy, win, mode="same")

	# Plot.
	ax = utils.latexify(fig.add_subplot(111))
	ax.plot(fx, fy, color="r")
	ax.set_ylabel("PSD (ppm$^2$$\mu$Hz$^{-1}$)")
	ax.set_xlabel("Frequency mod %s ($\mu$Hz)" % (config.deltanu,))

	plt.legend()
	fig.tight_layout()

def main(ifile, config):
	plot_echelle(config, plt.figure(figsize=(10, 6), dpi=50), ifile)

	if config.ofile:
		plt.savefig(config.ofile, transparent=True)
	else:
		plt.show()

if __name__ == "__main__":
	def __wrapped_main__():
		#DEFAULT_ORDER = 3
		DEFAULT_WIDTH = 51

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
		parser.add_argument("-so", "--start", dest="start", type=int, default=None, help="Start mode order (default: None).")
		parser.add_argument("-eo", "--end", dest="end", type=int, default=None, help="End mode order (default: None).")
		parser.add_argument("-w", "--width", dest="width", type=int, default=DEFAULT_WIDTH, help="Window size of filter (default: %f)." % (DEFAULT_WIDTH,))
		parser.add_argument("-o", "--off", dest="off", type=float, default=0, help="Offset (default: 0)")
		parser.add_argument("-s", "--save", dest="ofile", type=str, default=None, help="The output file.")
		parser.add_argument("csv", nargs=1)

		config = parser.parse_args()
		main(config.csv[0], config)

	__wrapped_main__()
