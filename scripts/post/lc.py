#!/usr/bin/env python3
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

import os
import sys
import argparse

import matplotlib as mpl
if "--animate" in sys.argv or "--ani" in sys.argv:
	mpl.use("TkAgg") # Hack to fix OS X.
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
def plot_lc(config, fig, ifile):
	# Get the cadence information.
	with open(ifile, "r", newline="") as f:
		times, fluxs = utils.csv_column_read(f, FIELDS, casts=CASTS, start=config.start, end=config.end)

	# Times and fluxes.
	xs = times
	ys = fluxs

	# Convert flux to ppm.
	#ys = ys / ys.mean() - 1
	#ys *= 1e6

	# Figure out time-related offsets.
	offset = np.min(times)
	xs -= offset
	if config.timestamp is not None:
		config.timestamp -= offset

	if config.fft:
		fx, fy = utils.lombscargle_amplitude(xs, ys, upper=config.high_freq)

		if config.fftout:
			with open(config.fftout, "w", newline="") as f:
				utils.csv_column_write(f, [fx, fy], ["frequency", "amplitude"])

	if config.lc:
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
		xs = np.tile(xs, config.width) + np.repeat(np.arange(config.width), xs.shape[0])
		ys = np.tile(ys, config.width)

	if config.fft and config.lc:
		ax1 = utils.latexify(fig.add_subplot(211))
	else:
		ax1 = utils.latexify(fig.add_subplot(111))

	if config.lc:
		if not (config.period or config.bins):
			ax1.plot(xs, ys, color="0.5", linestyle="-", marker="None")
			#ax1.plot(xs, ys, color="k", linestyle="None", marker="+", label=r"Kepler/K2 Halo Photometry")
			ax1.set_xlabel("Time ($d$)")
		else:
			# TODO: We should overlay a binned version.
			if config.timestamp is not None:
				predicted = (config.timestamp % config.period) / config.period
				predicted = (predicted + config.phase) % 1.0
				ax1.xaxis.set_ticks(predicted + np.arange(config.width), minor=True)
				ax1.xaxis.grid(True, which="minor", color="r", linestyle="--", linewidth=2)
			ax1.plot(xs, ys, color="0.5", linestyle="None", marker="o", label=r"Kepler/K2 Halo Photometry")
			ax1.set_xlabel("Phase")
		ax1.set_ylabel(r"Intensity (ppm)")

	if config.lc and config.title:
		ax1.set_title(r"Light Curve [%s] # %s" % (description(config), config.comment or ""))

	if config.fft:
		if config.lc:
			ax2 = utils.latexify(fig.add_subplot(212))
		else:
			ax2 = ax1
		ax2.plot(fx, fy, color="k", linestyle="-", marker="None")
		#ax2.xaxis.set_ticks(np.arange(*ax2.get_xlim(), step=1))
		#ax2.xaxis.set_ticks(np.arange(*ax2.get_xlim(), step=0.25), minor=True)
		#ax2.xaxis.grid(True, which="major", color="k", linestyle="--")
		#ax2.xaxis.grid(True, which="minor", color="k", linestyle=":")
		ax2.set_axisbelow(True)
		#ax2.set_xlabel("Frequency ($d^{-1}$)")
		ax2.set_xlabel("Frequency ($\mu$Hz)")
		ax2.set_ylabel("Amplitude (ppm)")
		#ax2.set_ylabel("PDF (ppm$^2$ $\mu$Hz$^{-1}$)")

	plt.legend()
	fig.tight_layout()

def main(ifile, config):
	if config.fft and config.lc:
		figsize = (10, 12)
	else:
		figsize = (10, 6)

	plot_lc(config, plt.figure(figsize=figsize, dpi=50), ifile)

	if config.ofile:
		plt.savefig(config.ofile, transparent=True)
	else:
		plt.show()

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Given an analysis, generate a light curve for the data.")
		parser.add_argument("-lc", "--light-curve", dest="lc", action="store_const", const=True, default=True, help="Enable light curve (default).")
		parser.add_argument("-nolc", "--no-light-curve", dest="lc", action="store_const", const=False, default=True, help="Disable light curve.")
		parser.add_argument("-fft", "--fft", dest="fft", action="store_const", const=True, default=True, help="Enable Fourier transform (default).")
		parser.add_argument("-nofft", "--no-fft", dest="fft", action="store_const", const=False, default=True, help="Disable Fourier transform.")
		parser.add_argument("-title", "--title", dest="title", action="store_const", const=True, default=True, help="Enable titles (default).")
		parser.add_argument("-notitle", "--no-title", dest="title", action="store_const", const=False, default=True, help="Disable titles.")
		parser.add_argument("-c", "--comment", dest="comment", type=str, default=None, help="Comment to add to the title (default: None).")
		parser.add_argument("-sc", "--start", dest="start", type=int, default=None, help="Start cadence (default: None).")
		parser.add_argument("-ec", "--end", dest="end", type=int, default=None, help="End cadence (default: None).")
		parser.add_argument("-fs", "--fft-samples", dest="samples", type=float, default=1e3, help="Number of samples in periodogram (default: 1000).")
		parser.add_argument("-hf", "--high-frequency", dest="high_freq", type=float, default=None, help="Highest frequency in periodogram (default: approximate nyquist).")
		parser.add_argument("-fp", "--folding-period", dest="period", type=float, default=None, help="The folding period of the light curve (default: None).")
		parser.add_argument("-w", "--width", dest="width", type=int, default=1, help="The phase width displayed (default: 1).")
		parser.add_argument("-po", "--phase-offset", dest="phase", type=float, default=0, help="Amount by which to phase shift the light curve (default: 0).")
		parser.add_argument("-pt", "--past-timestamp", dest="timestamp", type=float, default=None, help="BJD timestamp of some event that occured in the past to plot the predicted value of given the period (default: None).")
		parser.add_argument("-b", "--bins", dest="bins", type=int, default=None, help="The number of bins to bin the folded light curve (default: none).")
		parser.add_argument("-s", "--save", dest="ofile", type=str, default=None, help="The output file.")
		parser.add_argument("--save-fft", dest="fftout", type=str, default=None, help="The output file for the FFT data.")
		parser.add_argument("csv", nargs=1)

		config = parser.parse_args()

		main(config.csv[0], config)

	__wrapped_main__()
