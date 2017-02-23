#!/usr/bin/env python3
# keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
# Copyright (C) 2016 Aleksa Sarai <cyphar@cyphar.com>
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

import json
import argparse
import requests
import collections

K2_EPIC_URL = "https://archive.stsci.edu/k2/epic/search.php"
K2_DATA_URL = "https://archive.stsci.edu/k2/data_search/search.php"

def stsci_epic_search(url, **kwargs):
	data = collections.OrderedDict()
	data.update([
		("target", kwargs.get("target", "")),
		("resolver", kwargs.get("resolver", "Resolve")),
		("radius", kwargs.get("radius", "0.02")),
		("ra", kwargs.get("ra", "")),
		("dec", kwargs.get("dec", "")),
		("equinox", kwargs.get("equinox", "J2000")),
		("id", kwargs.get("id", "")),
		("k2_avail_flag", kwargs.get("k2_avail_flag", "")),
		("kp", kwargs.get("kp", "")),
		("teff", kwargs.get("teff", "")),
		("rad", kwargs.get("rad", "")),
		("ebv", kwargs.get("ebv", "")),
		("logg", kwargs.get("logg", "")),
		("feh", kwargs.get("feh", "")),
		("extra_column_name_1", kwargs.get("extra_column_name_1", "id")),
		("extra_column_value_1", kwargs.get("extra_column_value_1", "")),
		("extra_column_name_2", kwargs.get("extra_column_name_2", "id")),
		("extra_column_value_2", kwargs.get("extra_column_value_2", "")),
		("extra_column_name_3", kwargs.get("extra_column_name_3", "id")),
		("extra_column_value_3", kwargs.get("extra_column_value_3", "")),
		("extra_column_name_4", kwargs.get("extra_column_name_4", "id")),
		("extra_column_value_4", kwargs.get("extra_column_value_4", "")),
		("availableColumns", kwargs.get("availableColumns", "id")),
		("ordercolumn1", kwargs.get("ordercolumn1", "ang_sep")),
		("ordercolumn2", kwargs.get("ordercolumn2", "id")),
		("ordercolumn3", kwargs.get("ordercolumn3", "")),
		("coordformat", kwargs.get("coordformat", "sex")),
		("outputformat", kwargs.get("outputformat", "JSON")),
		("remnull", kwargs.get("remnull", "on")),
		("outputformat", "JSON"),
		("max_records", "50001"),
		("max_rpp", kwargs.get("max_rpp", "500")),
		("action", "Search"),
	])

	data.update(kwargs)

	if "selectedColumnsCsv" not in kwargs:
		kwargs["selectedColumnsCsv"] = "id,k2_ra,k2_dec,k2_avail_flag,kp,bmag,vmag,kepflag,ang_sep"

	r = requests.post(url, data=data)
	if r.status_code != requests.codes.ok:
		raise RuntimeError("status code was not 200: %d" % (r.status_code,))
	if r.text.strip() == "no rows found":
		return []
	return r.json()

def stsci_data_search(url, **kwargs):
	data = collections.OrderedDict()
	data.update([
		("action", "Search"),
		("target", kwargs.get("target", "")),
		("resolver", kwargs.get("resolver", "Resolve")),
		("radius", kwargs.get("radius", "0.02")),
		("ra", kwargs.get("ra", "")),
		("dec", kwargs.get("dec", "")),
		("equinox", kwargs.get("equinox", "J2000")),
		("ktc_k2_id", kwargs.get("ktc_k2_id", "")),
		("ktc_investigation_id", kwargs.get("ktc_investigation_id", "")),
		("twoMass", kwargs.get("twoMass", "")),
		("kp", kwargs.get("kp", "")),
		("ktc_target_type", kwargs.get("ktc_target_type", [])),
		("sci_campaign", kwargs.get("sci_campaign", "")),
		("objtype", kwargs.get("objtype", "")),
		("extra_column_name_1", kwargs.get("extra_column_name_1", "ktc_k2_id")),
		("extra_column_value_1", kwargs.get("extra_column_value_1", "")),
		("extra_column_name_2", kwargs.get("extra_column_name_2", "ktc_k2_id")),
		("extra_column_value_2", kwargs.get("extra_column_value_2", "")),
		("extra_column_name_3", kwargs.get("extra_column_name_3", "ktc_k2_id")),
		("extra_column_value_3", kwargs.get("extra_column_value_3", "")),
		("extra_column_name_4", kwargs.get("extra_column_name_4", "ktc_k2_id")),
		("extra_column_value_4", kwargs.get("extra_column_value_4", "")),
		("availableColumns", kwargs.get("availableColumns", "ktc_k2_id")),
		("ordercolumn1", kwargs.get("ordercolumn1", "ang_sep")),
		("ordercolumn2", kwargs.get("ordercolumn2", "ktc_k2_id")),
		("ordercolumn3", kwargs.get("ordercolumn3", "")),
		("coordformat", kwargs.get("coordformat", "sex")),
		("remnull", kwargs.get("remnull", "on")),
		("outputformat", "JSON"),
		("max_records", "50001"),
		("max_rpp", kwargs.get("max_rpp", "500")),
	])

	data.update(kwargs)

	if "selectedColumnsCsv" not in kwargs:
		kwargs["selectedColumnsCsv"] = "ktc_k2_id,sci_data_set_name,sci_campaign,objtype,sci_ra,sci_dec,ktc_target_type,refnum,sci_start_time,sci_end_time,kp,kepflag,hip,tyc,sdss,ucac,twomass,mflg,sci_module,sci_output,sci_channel,k2_hlsp,ang_sep"

	r = requests.post(url, data=data)
	if r.status_code != requests.codes.ok:
		raise RuntimeError("status code was not 200: %d" % (r.status_code,))
	if r.text.strip() == "no rows found":
		return []

	return r.json()


def main(outfile, config):
	out = {
		"radius": config.radius,
		"search": config.magnitude,
		"data": [],
	}

	print ("[*  ] Finding %s search." % (config.magnitude,))
	brights = stsci_epic_search(K2_EPIC_URL, extra_column_name_1="vmag", extra_column_value_1=config.magnitude, k2_avail_flag="0")

	for bright in brights:
		print("[** ] EPIC:   %s" % (bright["EPIC"],))
		print("[** ] Searching in <=%d' radius." % (config.radius,))

		postage_stamps = stsci_data_search(K2_DATA_URL, ra=bright["RA"], dec=bright["Dec"], radius=config.radius)

		print ("[** ] Found [%d] postage stamps!" % (len(postage_stamps),))

		nears = []
		campaigns = set()
		for postage_stamp in postage_stamps:
			campaigns.add(postage_stamp["Campaign"])
			nears.append({
				"epic": postage_stamp["K2 ID"],
				"dsname": postage_stamp["Dataset Name"],
				"campaign": postage_stamp["Campaign"],
				"ang_sep": postage_stamp["Ang Sep (')"],
			})

		out["data"].append({
			"bright": bright["EPIC"],
			"hip": bright.get("HIP", None),
			"campaigns": list(campaigns),
			"nears": nears,
		})

	with open(outfile, "w") as f:
		json.dump(out, f)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Finds and outputs all 'interesting' EPIC targets, for use in contamination photometry.")
	parser.add_argument("-m", "--magnitude", dest="magnitude", default="<=6", type=str, help="Magnitude rval of bright star in field.")
	parser.add_argument("-r", "--radius", dest="radius", default=5, type=float, help='Radius (arcmin) to search for contaminated postage stamps (default: 5").')
	parser.add_argument("csv", nargs=1)

	args = parser.parse_args()
	main(outfile=args.csv[0], config=args)
