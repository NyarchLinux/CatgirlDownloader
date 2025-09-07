#!/bin/bash
APPID="moe.Avelcius.furrydownloader"
BUNDLENAME="catgirldownloader.flatpak"
flatpak-builder --install --user --force-clean flatpak-app "$APPID".json

if [ "$1" = "bundle" ]; then
	flatpak build-bundle ~/.local/share/flatpak/repo "$BUNDLENAME" "$APPID"
fi