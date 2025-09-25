#!/bin/sh

VERSION=v1.0.0

echo Building project...
rm -rdf build
meson setup --prefix /usr/ build
meson compile -C build
meson install --destdir root -C build

# Flatpak
echo Building Flatpak...

APPID="moe.nyarchlinux.catgirldownloader"
BUNDLENAME="catgirldownloader-$VERSION.flatpak"
flatpak-builder --install --user --force-clean flatpak-app "$APPID".json
flatpak build-bundle ~/.local/share/flatpak/repo "$BUNDLENAME" "$APPID"
mv $BUNDLENAME build/

cp nfpm.yaml build/
cd build

# DEB
echo Building DEB...
export DEPENDS_PYTHON=python3
export DEPENDS_GTK4=gir1.2-gtk-4.0
export DEPENDS_LIBADWAITA=gir1.2-adw-1
export DEPENDS_PYTHON_GOBJECT=python3-gi
export DEPENDS_PYTHON_REQUESTS=python3-requests
nfpm pkg -p deb

# RPM
echo Building RPM...
export DEPENDS_PYTHON=python3
export DEPENDS_GTK4=gtk4
export DEPENDS_LIBADWAITA=libadwaita
export DEPENDS_PYTHON_GOBJECT=python3-gobject
export DEPENDS_PYTHON_REQUESTS=python3-requests
nfpm pkg -p rpm

# APK
echo Building APK...
export DEPENDS_PYTHON=python3
export DEPENDS_GTK4=gtk4.0
export DEPENDS_LIBADWAITA=libadwaita
export DEPENDS_PYTHON_GOBJECT=py3-gobject3
export DEPENDS_PYTHON_REQUESTS=py3-requests
nfpm pkg -p apk

# PACMAN
echo Building PACMAN...
export DEPENDS_PYTHON=python
export DEPENDS_GTK4=gtk4
export DEPENDS_LIBADWAITA=libadwaita
export DEPENDS_PYTHON_GOBJECT=python-gobject
export DEPENDS_PYTHON_REQUESTS=python-requests
nfpm pkg -p archlinux

# TAR.GZ
echo Building tar.gz...
tar -C root -zcf catgirldownloader-$VERSION.tar.gz usr