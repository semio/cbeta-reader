# CBETA Reader — build targets
#
# Usage:
#   make static              # sync static files (JS, CSS, fonts) to dist/
#   make build               # full rebuild of dist/ (all collections)
#   make build COLLECTIONS="T X"  # rebuild with specific collections
#   make list                # list available collections
#   make clean               # remove dist/
#   make clean-read          # remove only dist/read/ (keep static/index/404)

COLLECTIONS ?=
OUTPUT ?= dist
PYTHON ?= uv run python

.PHONY: static build list clean clean-read

static:
	@echo "Syncing static files to $(OUTPUT)/static/..."
	@mkdir -p $(OUTPUT)/static
	@rsync -a --delete static/ $(OUTPUT)/static/
	@echo "Done."

build:
	$(PYTHON) generate.py -o $(OUTPUT) $(COLLECTIONS)

list:
	$(PYTHON) generate.py --list

clean:
	rm -rf $(OUTPUT)
	@echo "Removed $(OUTPUT)/"

clean-read:
	rm -rf $(OUTPUT)/read
	@echo "Removed $(OUTPUT)/read/"
