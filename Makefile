# Makefile for btrfs-gui

# What do we need to ship?
ICONS := disk_icon fs_icon fs_icon_open subvolume subvolume_default directory
ICON_FILES := $(foreach icon,$(ICONS),img/$(icon).gif)
PY_LIB_FILES := $(shell find btrfsgui -name \*.py)
DOC_FILES := README LICENCE
SUPPORT_FILES := Makefile

DIST_FILES = btrfs-gui btrfs-gui-helper $(DOC_FILES) $(SUPPORT_FILES) \
	$(ICON_FILES) $(PY_LIB_FILES)

all: icons version

# Produce a distribution tarball
tarball: icons version
	$(eval DIST_DIR := btrfs-gui-$(shell cat .version))
	@mkdir $(DIST_DIR)
	@for file in $(DIST_FILES); do \
		if echo $${file} | fgrep -q /; then \
			mkdir -p $(DIST_DIR)/$${file%/*} ;\
		fi ;\
		cp $${file} $(DIST_DIR)/$${file} ;\
	done
	@cp btrfs-gui btrfs-gui-helper $(DIST_DIR)
	@tar -czf $(DIST_DIR).tar.gz $(DIST_DIR)
	@rm -rf $(DIST_DIR)

install:
	@echo No installer ready yet.
	@echo Please run directly from the source directory with ./btrfs-gui

# Image conversion: requires inkscape. Alternatively, download the
# tarball to get the images.
icons: $(ICON_FILES)

ICONS_WEB := http://carfax.org.uk/sites/default/files
img/%.png: img/icons.svg
	@inkscape --export-png=$@ --export-id-only --export-id=$* \
		--export-background-opacity=0.0 --export-height=16 \
		--export-width=16 $< || \
	wget $(ICONS_WEB)/$*.png -O $@

img/%.gif: img/%.png
	@convert $< $@ || \
	wget $(ICONS_WEB)/$*.gif -O $@

# Work out a version string: get the latest tag from git. If that
# doesn't match the current revision number, append the revision
# number to it as well.
version:
	$(eval VERSION := $(shell git tag -l | grep ^v[0-9] | tail -1))
	@echo $(VERSION) | sed -e s/^v// >.version-list
	@if [ $$(git show --pretty=format:%H $(VERSION) | head -1) != $$(git log -1 --pretty=format:%H) ]; then \
		git log -1 --pretty=format:%h >>.version-list ;\
	fi
	@for part in $$(cat .version-list); do \
		echo -n $${part}- ;\
	done | sed -e s/-$$// >.version.new
	@mv .version.new .version
	@rm .version-list
	@echo $$(cat .version)

clean:
	@find -name \*~ -o -name \*.pyc -exec rm -f {} \;
