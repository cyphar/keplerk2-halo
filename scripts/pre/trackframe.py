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
import csv
import sys
import math
import numpy
import numpy.linalg
import scipy.interpolate
import scipy.optimize
import skimage.measure
import argparse

import matplotlib
matplotlib.use("TkAgg")
#if not os.getenv("DISPLAY"):
#	matplotlib.use("Agg") # Hack to fix no display.
r'''
matplotlib.rcParams.update({
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
'''
import matplotlib.pyplot as plt

import emcee
import corner
import astropy.io.fits
import utils

def filter_img(config, img):
	flxs = img[1].data["FLUX"]
	time = img[1].data["TIME"]
	qual = img[1].data["QUALITY"]
	cadn = img[1].data["CADENCENO"]

	# We need to fix up the times so they are in *absolute* BJD.
	time += img[1].header["BJDREFI"] + img[1].header["BJDREFF"]

	# Remove bad quality frames.
	filt = (qual == 0)
	flxs = flxs[filt]
	time = time[filt]
	cadn = cadn[filt]

	flxs = flxs[config.start:config.end]
	time = time[config.start:config.end]
	cadn = cadn[config.start:config.end]

	return {
		"FLUX": flxs,
		"TIME": time,
		"CADENCENO": cadn,
	}

def postage_stamp(flux):
	ignore = ~numpy.any(numpy.isnan(flux), axis=0)

	polys = []
	for pos in zip(*numpy.where(ignore)):
		x, y = pos
		px = shapely.geometry.box(x, y, x + 1, y + 1)
		polys.append(px)

	return shapely.ops.cascaded_union(polys)

def interpolate_flux(flux, delta, **kwargs):
	points = numpy.array(numpy.where(flux == flux)).T
	ylen, xlen = flux.shape
	gridx, gridy = (numpy.mgrid[1:ylen:ylen*1j,1:xlen:xlen*1j].T + delta).T - 1
	return scipy.interpolate.griddata(points, flux[list(points.T)], (gridx, gridy), **kwargs)

def flux_similarity(vec, base, flux, H):
	# Create an interpolated flux setup.
	interp = interpolate_flux(base, vec, method="cubic")
	interp[numpy.isnan(interp)] = numpy.median(base[~numpy.isnan(base)])
	interp = H * (interp - interp.mean()) / interp.std()

	win_size = None
	if any((numpy.array(flux.shape) - 11) < 0):
		win_size = 7

	# Compare similarity using SSIM (http://dl.acm.org/citation.cfm?id=2320551#)
	# which is better than the "trivial" root-mean-square method and instead
	# encodes structural information in the comparison.
	ssim = skimage.measure.compare_ssim(flux, interp, gaussian_weights=True, win_size=win_size)

	# We want to converge on a ssim of 1. Also multiply it so it's large enough
	# to not trigger early convergence detection.
	return 1000 * (1 - ssim)

def ignore_mask(fluxs):
	# Ignore pixels which are NaN at any point.
	ignore = numpy.any(numpy.isnan(fluxs), axis=0)

	# Take the median std of the postage stamp.
	stds = numpy.std(fluxs, axis=(0,1))
	stds = stds[~numpy.isnan(stds)]
	std = numpy.median(stds)
	# And the median mean.
	means = numpy.mean(fluxs, axis=(0,1))
	means = means[~numpy.isnan(means)]
	mean = numpy.median(means)

	# Ignore any pixels which reach a value of mean+30*std.
	ignore |= numpy.any(fluxs >= (mean+30*std), axis=0)
	return ignore

def hanning(shape):
	H = None
	for axis in shape:
		nxt = numpy.hanning(axis)
		if H is not None:
			nxt = numpy.outer(H, nxt)
		H = nxt
	return H

def DEBUG_plot(idx, fig, base, flx, H):
	X, Y = 200, 200
	grid = numpy.zeros([X, Y])
	for x, y in utils.positions(grid):
		vec = 5 - numpy.array([x / X, y / Y]) * 10
		grid[y, x] = flux_similarity(vec, base, flx, H) / 1000

	ax = utils.latexify(fig.add_subplot(111))
	s = ax.imshow(grid, interpolation='none', extent=[-5, 5, -5, 5], cmap="viridis")
	ax.set_xlabel(r"x offset (px)")
	ax.set_ylabel(r"y offset (px)")
	ax.set_title(r"$\left|base_{offset} - frame_{%d}\right|$" % (idx,))
	fig.tight_layout()
	fig.colorbar(s, cmap="viridis")

def main(ofile, config):
	img = astropy.io.fits.open(config.fits)
	img = filter_img(config, img)

	# Short-hand.
	cadn = img["CADENCENO"]
	time = img["TIME"]
	flxs = img["FLUX"]

	# Generate ignore mask.
	ignore = ignore_mask(flxs)
	# flxs[...,ignore] = 0
	flxs[...,ignore] = numpy.median(flxs[...,~ignore])

	# Normalise.
	flxs = ((flxs.T - flxs.mean(axis=(1, 2))) / flxs.std(axis=(1, 2))).T
	# Create a hanning window for it.
	H = hanning(flxs.shape[1:])
	flxs_hanning = flxs * H

	# Take the first frame as our "base". We grid interpolate it later.
	base = flxs_hanning[config.first,...]

	# XXX: This format is horrible...
	writer = csv.DictWriter(ofile, fieldnames=["cadence", "x", "y"])
	writer.writeheader()
	writer.writerow({"cadence": "", "x": -1, "y": -1})

	# Figure out the initial vector.
	NDIM = len(base.shape)
	seed_vec = config.perturb*numpy.random.rand(NDIM)

	# Purely for debugging.
	debug_ssim = set([int(idx) for idx in config.plot_ssim])

	# Iterate over the frames.
	for idx, flx in enumerate(flxs_hanning):
		# XXX: Output some information to convince people we haven't frozen.
		sys.stdout.write(".")
		sys.stdout.flush()

		# If we are on the base frame we know that the offset is (0, 0).
		if config.first == idx:
			seed_vec = numpy.zeros(NDIM)

		if idx in debug_ssim:
			fig = plt.figure(figsize=(10, 10), dpi=50)
			DEBUG_plot(idx, fig, base, flx, H)
			plt.legend()
			plt.savefig("output_%d.png" % (idx,))
			print("[!] output_%d.png" % (idx,))

		vec, fopt, *_ = scipy.optimize.fmin(flux_similarity, seed_vec, args=(base, flx, H), full_output=True, disp=False)
		writer.writerow({"cadence": cadn[idx], "x": vec[1], "y": vec[0]})
		ofile.flush()

		# We base the next frame on the previous one, sort of like MC.
		seed_vec = vec

	sys.stdout.write("DONE\n")
	sys.stdout.flush()

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Generate (x,y) tracking information for a Kepler/K2 postage stamp using MCMC.")
		parser.add_argument("fits", help="The FITS file to track, containing a Kepler/K2 postage stamp.")
		parser.add_argument("-F", "--first", dest="first", type=int, default=0, help="The index of the 'base frame' which is used as the template to minimise similarity to.")
		parser.add_argument("-o", "--output", dest="output", type=str, default=None, help="Output file for xy.csv (default: stdout).")
		parser.add_argument("--perturb", dest="perturb", type=float, default=0.001, help="Level of inital perturbation (default: 0.001).")
		parser.add_argument("--plot-ssim", dest="plot_ssim", action="append", default=[], help="Plot the SSIM space for the given indexes (default: none).")
		# Cadence options
		parser.add_argument("-sc", "--start", dest="start", type=int, default=None, help="Start cadence (default: None).")
		parser.add_argument("-ec", "--end", dest="end", type=int, default=None, help="End cadence (default: None).")

		args = parser.parse_args()
		if args.output is None:
			ofile = sys.stdout
		else:
			ofile = open(args.output, "w")
		with ofile:
			main(ofile, args)

	__wrapped_main__()
