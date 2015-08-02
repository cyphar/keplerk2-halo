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
import json
import argparse
import requests

ARCHIVE_URL = "https://archive.stsci.edu/pub/k2/target_pixel_files/c%d/%.9d/%.5d/%s.gz"

DATA_JSON = "stars.json"
STAR_JSON = "targets.json"
TARGET_JSON = "target.json"

def fits_url(campaign, target, fits, **_):
	def lead(x, n):
		return x - x%n
	return ARCHIVE_URL % (campaign, lead(target, 1e5), lead(target % 1e5, 1e3), fits)

def save_fits(url, ofile, chunk_size=1024):
	r = requests.get(url, stream=True)
	n = 0
	for chunk in r.iter_content(chunk_size=chunk_size):
		if chunk:
			n += 1
			if not n % 300:
				sys.stdout.write(".")
				sys.stdout.flush()

			ofile.write(chunk)
			ofile.flush()

def save_data(path, config):
	with open(os.path.join(path, DATA_JSON)) as fstars:
		stars = json.load(fstars)

	for star in stars["stars"]:
		with open(os.path.join(path, star, STAR_JSON)) as ftargets:
			targets = json.load(ftargets)

		for target in targets["targets"]:
			sys.stdout.write("Saving target %s/%s " % (star, target))
			sys.stdout.flush()

			with open(os.path.join(path, star, target, TARGET_JSON)) as fepic:
				epic = json.load(fepic)
				url = fits_url(**epic)

			opath = os.path.join(path, star, target, epic["fits"] + ".gz")
			if config.clobber or not os.path.exists(opath):
				with open(opath, "wb") as ofile:
					save_fits(url, ofile)

			sys.stdout.write(" OK\n")
			sys.stdout.flush()

def main(path, config):
	save_data(path, config)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Downloads the set of Kepler K2 Long Cadence Files given by a particular `data` metadata tree.")
	parser.add_argument("-c", "--clobber", dest="clobber", action="store_const", const=True, default=False, help="Enable clobbering of existing data.")
	parser.add_argument("-nc", "--no-clobber", dest="clobber", action="store_const", const=False, default=False, help="Disable clobbering of existing data (default).")
	parser.add_argument("path")

	args = parser.parse_args()
	main(path=args.path, config=args)
