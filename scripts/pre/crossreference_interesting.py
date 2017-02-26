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


# All of this is reverse engineered from what the requests look like to:
#   http://simbad.harvard.edu/simbad/sim-script
# Sucks that you can't get JSON output of the data -- you need to parse some
# weird custom output format they have...

import csv
import sys
import json
import time
import argparse
import requests

SIM_SCRIPT_URL = "http://simbad.harvard.edu/simbad/sim-script"
RETRY_NUMBER = 5

def simbad_script(script):
	for _ in range(RETRY_NUMBER):
		try:
			r = requests.get(SIM_SCRIPT_URL, params={
				"submit": "submit script",
				"script": script,
			})
		except OSError:
			# Weirdly we've hit some issue now.
			time.sleep(3)
			continue

		if r.status_code != requests.codes.ok:
			continue

		return r.text.strip()

	raise RuntimeError("retry failed -- status code was not 200: %d -- %s" % (r.status_code, r.text.strip()))

def simbad_search(search):
	# For more information about this _lovely_ scripting language, see
	#   http://simbad.harvard.edu/simbad/sim-help?Page=sim-fscript

	output = simbad_script(r"""
	format object "format: %IDLIST(1),%PLX(V[E]),%SP(S)%FLUXLIST(U,B,V)[,%*(F)]"
	set limit 0
	""" + "query %s" % (search,))

	# The lovely format is the following:
	#   ::script::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	#   <the script>
	#   ::console:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	#   <console output>
	#   ::data::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	#   [our format]

	# Where our format looks like this:
	#   format: ID,Parallax[Error],SpectralType,U,B,V

	matching = [line for line in output.split('\n') if line.startswith("format: ")]
	if len(matching) != 1:
		raise RuntimeError("output missing 'format: ': %s", (output,))

	csv_out = matching[0].split(": ")[1]
	ident, parallax, spectral, umag, bmag, vmag, *unused = csv_out.split(",")
	if len(unused) > 0:
		sys.stderr.write("# csv_out had more than 6 fields: %s\n" % (csv_out,))
		sys.stderr.flush()

	return {
		"ident": ident,
		"parallax": parallax,
		"spectral": spectral,
		"U": umag,
		"B": bmag,
		"V": vmag,
	}

def main(ifile, config):
	with open(ifile) as f:
		data = json.load(f)

	writer = csv.DictWriter(sys.stdout, fieldnames=["epic", "ident", "n_stamps",
		"spectral", "parallax",
		"U", "B", "V"])
	writer.writeheader()

	for bright in data["data"]:
		if not bright.get("hip", ""):
			sys.stderr.write("# skipping %s because missing HIP ident\n" % (bright["bright"]))
			sys.stderr.flush()
			continue

		result = simbad_search("hip %s" % (bright["hip"],))

		result["epic"] = bright["bright"]
		result["n_stamps"] = len(bright["nears"])
		writer.writerow(result)
		sys.stdout.flush()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Cross-references identifiers from a file output from find_interesting.py.")
	parser.add_argument("csv", nargs=1)

	args = parser.parse_args()
	main(ifile=args.csv[0], config=args)
