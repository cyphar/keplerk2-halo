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

import sys
import math

import numpy as np
import matplotlib.pyplot as plt

import scipy as sp
import scipy.fftpack

import astropy as ap
import astropy.io.fits

import utils

def img_perpixel_fft(img):
	flx = img["FLUX"]
	time = img["TIME"]
	ws = np.mean(np.diff(time[~np.isnan(time)]))

	if flx.dtype.byteorder != "=":
		flx = flx.astype(flx.dtype.newbyteorder("="))

	for y in reversed(range(flx.shape[1])):
		for x in range(flx.shape[2]):
			data = flx[:, y, x]

			if np.any(np.isnan(data)):
				yield None
				continue

			fx = np.linspace(0, 1 / ws, data.size / 2)[1:]
			fy = sp.fftpack.fft(data)[1:fx.size+1]

			yield (fx, fy, x, y)

def plot_fft(img, output=None):
	flx = img["FLUX"]

	width = flx.shape[1]
	height = flx.shape[2]

	#plt.rcParams["figure.figsize"] = (128, 128)
	for i, fft in enumerate(img_perpixel_fft(img)):
		if fft is None:
			continue

		fx, fy, x, y = fft
		fy = np.abs(fy)

		mflx = np.mean(flx[:, y, x])

		if mflx > 200000:
			style = "black"
		elif mflx > 150000:
			style = "brown"
		elif mflx > 100000:
			style = "maroon"
		elif mflx > 50000:
			style = "red"
		else:
			style = "orange"

		plt.subplot(width, height, i + 1)
		#plt.ylim(ymin=1e1, ymax=1e10)
		plt.loglog(fx, fy, style)
		plt.axis("off")
		plt.grid("on")

	if output:
		plt.savefig(output, dpi=150)
	else:
		plt.show()

def main():
	if len(sys.argv) < 2 or len(sys.argv) > 3:
		print("invalid number of arguments")
		sys.exit(1)

	inp = sys.argv[1]
	out = None

	if len(sys.argv) == 3:
		out = sys.argv[2]

	with ap.io.fits.open(inp) as img:
		flx = utils.filter_img(img)
		plot_fft(flx, out)

if __name__ == "__main__":
	main()
