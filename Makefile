# Copyright (C) 2015 Aleksa Sarai <cyphar@cyphar.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

DOCKER  := docker
IMAGE   := cyphar/tsp:latest

DATA  := $(shell pwd)/data
CDATA := /opt/kepler/data

OUT  := $(shell pwd)/out
COUT := /opt/kepler/out

SRC  := scripts
DSRC := .dockerignore Dockerfile

VOLUMES := -v $(DATA):$(CDATA) -v $(OUT):$(COUT)
SHELL = bash

.PHONY: run shell build

# Run a shell in our workspace.
shell: build out
	@echo " [SHELL] $(IMAGE)"
	@$(DOCKER) run --rm -it $(VOLUMES) $(IMAGE) $(SHELL)

# Run a command in the workspace.
run: build out
	@echo "   [RUN] $(IMAGE) $(CMD)"
	@$(DOCKER) run -it --rm $(VOLUMES) $(IMAGE) $(CMD)

# Hack to automatically figure out if we need to build.
.build: $(SRC) $(DSRC)
	@touch $@
	@echo " [BUILD] ."
	@$(DOCKER) build -t $(IMAGE) .

# Wrap the internal builder.
build: .build

# Fill the out/ directory structure.
out:
	@echo " [MKDIR] $@"
	@mkdir -p $(shell ls -ld $(shell basename $(DATA))/*/[123456789].* | awk '{ print $$9 }' | sed s/data/$@/g)
