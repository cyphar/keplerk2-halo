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

# This is just a rough version of a more clever cropping method. A correct
# method of doing this in a more clever way would be to do a bucket fill
# algorithm after selecting choice points as being the centroids of stars.
# We then would have to do this for every frame (or track the motion) and then
# remove them from the data set. It'd be nice if we always had the same number
# of pixels in each frame (because, strictly speaking, we shouldn't have
# different numbers of stars to ignore in different frames of the same target).

# Unfortuntately, that would take more time than it takes to write this comment
# (and also, we aren't entirely sure if this is a good idea). So we're going to
# fudge it quite a bit here. We instead are going to delete all pixels in each
# frame that fulfil a certain criteria (they are brighter than a certain
# threshold bigger than the median value). Then we have to take a weighted sum
# so we can compare frame-to-frame values of "total flux".

# It'd also be nice if we could automate the disgarding of unstable frames that
# occur at the beginning of c2. But that'd be a pain, so we'll just hardcode it,
# because that's what real hackers do. :P

# It's also important to notice that certain frames are just bad. We need to
# filter them out. This is going to be a very bumpy ride.

import sys
import argparse
import warnings

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors

import numpy as np
import numpy.fft
import numpy.ma

import astropy as ap
import astropy.io.fits

import utils

DEFAULT_PMIN = 1.0
DEFAULT_PMAX = 95.0
DEFAULT_FRACTION = 0.2
DESCRIPTION = str.join(" ", sys.argv[1:-1])

def sigma_flux(flx, fraction=DEFAULT_FRACTION):
	# TODO: Figure out a nice value for the parameter.
	flat = flx.flatten()

	if fraction <= 0:
		return None

	with warnings.catch_warnings():
		warnings.filterwarnings('ignore', message="(.*)invalid value(.*)")
		n = int(fraction * len(flx.flatten()))
		k = np.median(np.sort(flat)[-n:]) / np.median(flat)
	return k

def normalise_flux(flx, vmin, vmax):
	nflx = np.copy(flx)
	with warnings.catch_warnings():
		warnings.filterwarnings('ignore', message="(.*)invalid value(.*)")
		nflx[np.isnan(nflx) | (nflx < vmin)] = vmin
	return nflx

def percentile_sample(sample, pmin=DEFAULT_PMIN, pmax=DEFAULT_PMAX):
	with warnings.catch_warnings():
		warnings.filterwarnings('ignore', message="(.*)invalid value(.*)")
		return np.percentile(sample[sample > 0], [pmin, pmax])

def crop_flux(flx, sigma):
	if sigma is None:
		return flx

	# TODO: Check if this is the best value.
	noise_median = np.median(flx)
	threshold = sigma * noise_median

	# We fill the pixels which are considered to be "too bright" with the median
	# noise value. This might be dodgy, but it shouldn't affect the statistical
	# properties of the data (and it's easier than tracking pixels that don't
	# exist).
	nflx = np.copy(flx)
	with warnings.catch_warnings():
		warnings.filterwarnings('ignore', message="(.*)invalid value(.*)")
		nflx[nflx > threshold] = noise_median
	return nflx

def yield_crop(flxs, start=0, end=-1, **kwargs):
	vmin, vmax = percentile_sample(flxs)
	for flx in flxs[start:end]:
		flx = normalise_flux(flx, vmin=vmin, vmax=vmax)
		yield crop_flux(flx, **kwargs)

# XXX: Remove me. I'm just here for demonstration.
#      Or add the ability to animate me.
def plot_crop(flximg, start=0, end=-1, **_kwargs):
	flxs = flximg["FLUX"]
	vmin, vmax = percentile_sample(flxs)

	del _kwargs["logy"], _kwargs["logx"], _kwargs["crop"]

	kwargs = {
		#"norm": mpl.colors.LogNorm(vmin=vmin, vmax=vmax),
		"cmap": "gray",
		"origin": "lower",
		"interpolation": "nearest",
		"vmax": vmax,
		"vmin": vmin,
	}

	for t, crp in enumerate(yield_crop(flxs, start=start, end=end, **_kwargs)):
		flx = normalise_flux(flxs[start+t], vmin=vmin, vmax=vmax)

		# Show a comparison.
		# XXX: Make this nicer?
		fig = plt.figure(figsize=flx.shape[::-1], dpi=30)

		ax = fig.add_subplot(121)
		ax.matshow(flx, **kwargs)

		bx = fig.add_subplot(122)
		bx.matshow(crp, **kwargs)

		plt.show()

def plot_lc(ax, flximg, start=0, end=-1, logy=False, logx=False, crop=True, **kwargs):
	flxs = flximg["FLUX"]

	if crop:
		flxs = yield_crop(flxs, start=start, end=end, **kwargs)
	else:
		vmin, vmax = percentile_sample(flxs)
		flxs = [normalise_flux(flx, vmin=vmin, vmax=vmax) for flx in flxs]

	sums = [np.sum(flx.flatten()) for flx in flxs]
	mean = np.mean(sums)

	ys = (sums / mean) - 1
	xs = np.arange(0, len(ys)) + start

	ax.plot(xs, ys)
	ax.set_title(r"Light Curve (%s)" % (DESCRIPTION,))
	ax.set_ylabel(r"$\Sigma{Flux}$ [Arbitrary Units]")
	if logy:
		ax.set_yscale("log")
	ax.set_xlabel(r"Frame Number")
	if logx:
		ax.set_xscale("log")
	ax.grid("on")

def plot_fft(ax, flximg, start=0, end=-1, logy=False, logx=False, crop=True, **kwargs):
	flxs = flximg["FLUX"]
	time = flximg["TIME"]

	if crop:
		flxs = list(yield_crop(flxs, start=start, end=end, **kwargs))
	else:
		vmin, vmax = percentile_sample(flxs)
		flxs = [normalise_flux(flx, vmin=vmin, vmax=vmax) for flx in flxs]

	sums = [np.sum(flx.flatten()) for flx in flxs]
	mean = np.mean(sums)

	ws = np.median(np.diff(time[~np.isnan(time)]))
	ys = (sums / mean) - 1

	fx = np.linspace(0, 1 / (2 * ws), ys.size // 2)
	fy = np.abs(np.fft.fft(ys)[:ys.size // 2])

	ax.plot(fx, fy)
	ax.set_title(r"Fourier Transform (%s)" % (DESCRIPTION,))
	ax.set_ylabel(r"Amplitude [Arbitrary Units]")
	if logy:
		ax.set_yscale("log")
	ax.set_xlabel(r"Frequency [Arbitrary Units]")
	if logx:
		ax.set_xscale("log")
	ax.grid("on")

def main(fits, plot_type, sigma=None, sigma_fraction=DEFAULT_FRACTION, **kwargs):
	fits = fits[0]
	with ap.io.fits.open(fits) as img:
		flximg = utils.filter_img(img)
		fig = plt.figure(figsize=flximg["FLUX"][0].shape[::-1], dpi=30)
		ax = fig.add_subplot(111)

		# XXX: This is sort of a horrible hack atm. It's very easily broken.
		if sigma is None:
			if sigma_fraction > 0:
				sigma = np.median([sigma_flux(flx, sigma_fraction) for flx in flximg["FLUX"]])
		kwargs["sigma"] = sigma

		if plot_type == "fft":
			plot_fft(ax, flximg, **kwargs)
			plt.show()
		elif plot_type == "lc":
			plot_lc(ax, flximg, **kwargs)
			plt.show()
		elif plot_type == "disp":
			# TODO: Let this be killed.
			plot_crop(flximg, **kwargs)

if __name__ == "__main__":
	def wrap_num(tp, min, max):
		def wrapper(num):
			try:
				assert(min <= tp(num) <= max)
			except (ValueError, AssertionError):
				raise argparse.ArgumentTypeError("%r is not in the valid range [%r,%r]" % (tp(num), min, max))
			return tp(num)
		return wrapper

	parser = argparse.ArgumentParser(description="Take a Kepler Long Cadence K2 FITS File, crop out the brightest objects then plot photometry data. The cropping is done using a rudimentary sigma signal-to-noise approach, where any pixel above a certain threshold is capped to the median value.")
	parser.add_argument("-sf", "--start-frame", dest="start", type=int, default=0, help="The start frame (default: 0).")
	parser.add_argument("-ef", "--end-frame", dest="end", type=int, default=-1, help="The end frame (default: -1).")
	#parser.add_argument("--pmin", type=wrap_num(float, 1.0, 100.0), default=DEFAULT_PMIN, help="The lower percentage limit for sampling (default: %f)." % (DEFAULT_PMIN,))
	#parser.add_argument("--pmax", type=wrap_num(float, 1.0, 100.0), default=DEFAULT_PMAX, help="The upper percentage limit for sampling (default: %f)." % (DEFAULT_PMAX,))
	parser.add_argument("--sigma", type=wrap_num(float, 1.0, 20.0), default=None, help="The sigma threshold for objects to crop (default: automated).")
	parser.add_argument("--sigma-fraction", type=wrap_num(float, 0.0, 1.0), default=DEFAULT_FRACTION, help="The sigma fraction parameter to crop (only used for automated thresholding).")
	o_crop = parser.add_mutually_exclusive_group()
	o_crop.add_argument("--no-crop", dest="crop", action="store_false", help="Disable brightest object cropping.")
	o_crop.add_argument("--crop", dest="crop", action="store_true", help="Enable brightest object cropping (default).")
	o_logx = parser.add_mutually_exclusive_group()
	o_logx.add_argument("--logx", dest="logx", action="store_true", help="Use a log(x) scale.")
	o_logx.add_argument("--linearx", dest="logx", action="store_false", help="Use a linear(x) scale (default).")
	o_logy = parser.add_mutually_exclusive_group()
	o_logy.add_argument("--logy", dest="logy", action="store_true", help="Use a log(y) scale.")
	o_logy.add_argument("--lineary", dest="logy", action="store_false", help="Use a linear(y) scale (default).")
	o_type = parser.add_mutually_exclusive_group(required=True)
	o_type.add_argument("--fourier", "--fft", dest="plot_type", action="store_const", const="fft", help="Plot a Fourier Transform of the flux.")
	o_type.add_argument("--light-curve", "--lc", dest="plot_type", action="store_const", const="lc", help="Plot a Light Curve of the flux.")
	o_type.add_argument("--display", "--disp", dest="plot_type", action="store_const", const="disp", help="Plot a Light Curve of the flux.")
	parser.add_argument("fits", nargs=1)
	parser.set_defaults(crop=True, logx=False, logy=False)

	args = parser.parse_args()
	#DEFAULT_PMAX = args.pmax
	#DEFAULT_PMIN = args.pmin

	#del args.pmax, args.pmin

	main(**vars(args))
