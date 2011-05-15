# Makefile for btrfs-gui

ICONS := disk_icon fs_icon fs_icon_open

install:
	echo No installer ready yet

icons: $(foreach icon,$(ICONS),img/$(icon).gif)

img/%.png: img/icons.svg
	inkscape --export-png=$@ --export-id-only --export-id=$* \
		--export-background-opacity=0.0 --export-height=16 \
		--export-width=16 $<

img/%.gif: img/%.png
	convert $< $@
