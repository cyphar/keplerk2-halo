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
import csv
import sys
import json
import numpy as np
import argparse

FIELDS = ["EPIC", "star", "Campaign", "RA", "Dec"]
DATA_JSON = "stars.json"
STAR_JSON = "targets.json"
TARGET_JSON = "target.json"

def convert_degrees(deg):
	if " " in deg:
		deg = np.array(deg.split(), dtype=float)
		deg = np.abs(deg) * np.sign(deg)[0]
		return np.sum(deg * np.power([60]*3, [2, 1, 0]))
	else:
		return float(deg)

def output_targets(path, wr):
	with open(os.path.join(path, DATA_JSON)) as fstars:
		stars = json.load(fstars)

	for star in stars["stars"]:
		with open(os.path.join(path, star, STAR_JSON)) as ftargets:
			targets = json.load(ftargets)

		for target in targets["targets"]:
			with open(os.path.join(path, star, target, TARGET_JSON)) as fepic:
				epic = json.load(fepic)
				wr.writerow({"star": star, "EPIC": epic["target"], "Campaign": epic["campaign"], "RA": convert_degrees(epic["coord"]["ra"]), "Dec": convert_degrees(epic["coord"]["dec"])})

def main(out, path):
	with open(out, "w", newline='') as cfile:
		wr = csv.DictWriter(cfile, fieldnames=FIELDS)
		wr.writerow({fn: fn for fn in FIELDS})
		output_targets(path, wr)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Outputs a CSV which contains the set of targets.")
	parser.add_argument("out")
	parser.add_argument("path")
	main(**vars(parser.parse_args()))
