# Copyright (C) 2015 Aleksa Sarai <cyphar@cyphar.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# 1. The above copyright notice and this permission notice shall be included in
#    all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
