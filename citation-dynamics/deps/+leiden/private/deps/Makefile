SHELL := /bin/bash

all: libleiden

libleiden: export DESTDIR = ../install
libleiden:
	meson build
	pushd build; ninja; popd
	pushd build; ninja install; popd

uninstall:
	pushd build; ninja uninstall; popd

clean: uninstall
	rm -rf build install
