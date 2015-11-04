## K2 TSP Research Project ##
```
Supervisors: Tim Bedding, Daniel Huber, Simon Murphy
Institution: The University of Sydney
```

A research project to see if it is possible to do meaningful photometry on B
star contamination of Kepler K2 postage stamps. Specifically, we focus on
examples in campaign 2, but create general techniques which can be applied to
any other campaign (or to astronomy in general).

### Usage ###

The real magic is inside `scripts/analysis/clever.py`. To analyse the &pi; Sco
data, run the following command in any *nix shell:

```
% ./scripts/analysis/clever.py --csv \
	-mf 400 -m data/pi_Sco/1.203442993/ap_203442993.txt -d 1 \
	-s pi+analysis.csv -t data/pi_Sco/1.203442993/xy_203442993.csv \
	data/pi_Sco/1.203442993/ktwo203442993-c02_lpd-targ.fits
% ./scripts/post/lc.py --no-title --no-fft -w 2 \
	-fp 1.570103 -pt 2452025.96 \
	<(./scripts/post/highpass.py -o 6 -w 201 -sc 50 -ec -580 pi+analysis.csv)
```

### &pi; Sco ###
This is an example of our analysis usnig aperture analysis, using
`EPIC 203442993`. This photometric analysis mirrors ground-based surveys of
&pi; Sco and has an incredible trendline.

![piscoexample.png](piscoexample.png)

### License ###
The source code under `scripts/` is licensed under version 2 of the GNU General
Public License:

```
keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
Copyright (C) 2015 Aleksa Sarai <cyphar@cyphar.com>

This program is free software; you can redistribute it and/or
modify it under the terms of version 2 of the GNU General Public
License as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
```

The files under `data/` are all [publicly available][k2-archive] and are
provided by NASA in compliance with their [data use policy][k2-data-policy].

The `*.json` metadata was collated using both [SIMBAD][simbad] and
[MAST][k2-search], both of which are also public resources.

[k2-archive]: https://archive.stsci.edu/pub/k2/target_pixel_files/
[k2-data-policy]: https://archive.stsci.edu/data_use.html
[k2-search]: https://archive.stsci.edu/k2/data_search/search.php
[simbad]: http://simbad.u-strasbg.fr/simbad/

### Where do I ~~sign~~ cite? ###

A paper is currently in the works, so there's nothing to cite *quite* yet. It'll
hopefully all be done and ready to publish by early 2016. Watch this space to
read the paper once it's published.
