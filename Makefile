# Makefile for btrfs-gui

# What do we need to ship?
ICONS := disk_icon fs_icon fs_icon_open subvolume subvolume_default directory
ICON_FILES := $(foreach icon,$(ICONS),img/$(icon).gif)
PY_LIB_FILES := $(shell find btrfsgui -name \*.py)
DOC_FILES := README LICENCE
SUPPORT_FILES := Makefile

DIST_FILES = btrfs-gui btrfs-gui-helper $(DOC_FILES) $(SUPPORT_FILES) \
	$(ICON_FILES) $(PY_LIB_FILES)

all: icons

# Produce a distribution tarball
tarball: icons
	python3 setup.py sdist

install:
	python3 setup.py install

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

clean:
	@find -name \*~ -o -name \*.pyc -exec rm -f {} \;
	@rm -rf build
