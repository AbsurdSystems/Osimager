# Install these dependencies: sudo apt-get install cc65 srecord
# Adjust the run address to match the .org in the source code

SCRIPT_PATH=/usr/local/bin/osimager
BASH_SCRIPT_LOCATION=/usr/bin

VENV_NAME=.venv
VENV_PATH=$(SCRIPT_PATH)/$(VENV_NAME)
VENV_BIN=$(VENV_PATH)/bin


define BASH_SCRIPT
#!/bin/bash
$(VENV_BIN)/python3 $(SCRIPT_PATH)/src/osimager.py $$*
endef
export BASH_SCRIPT


all: install

console:
	$(VENV_BIN)/python3

test:
	@echo "$$BASH_SCRIPT" > ./osimager.sh

dependencies:
	apt-get update
	apt-get install fdisk

install:
	mkdir -p $(SCRIPT_PATH)
	cp -r ./src $(SCRIPT_PATH)
	python3 -m venv $(VENV_PATH)
	. $(VENV_BIN)/activate
	chmod -R 755 $(SCRIPT_PATH)
	@echo "$$BASH_SCRIPT" > $(BASH_SCRIPT_LOCATION)/osimager
	chmod -R 755 $(BASH_SCRIPT_LOCATION)/osimager

upgrade:
	cp -ruv ./src $(SCRIPT_PATH)

uninstall:
	rm -R $(SCRIPT_PATH)
	rm $(BASH_SCRIPT_LOCATION)/osimager



