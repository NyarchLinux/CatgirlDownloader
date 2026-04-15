# CatgirlDownloader
A GTK4 application that downloads images of catgirl based on https://nekos.moe
![](http://nyarchlinux.moe/assets/img/catgirldownloader-screenshots.png)

## Requirements

### Build Tools
- **meson** - Build system
- **ninja** - Build backend
- **python3** - Runtime
- **gi** (PyGObject) - Python bindings

### Runtime Dependencies
- **gtk4** - GTK4 library
- **libadwaita** - GNOME Adwaita library
- **requests** - HTTP library
- **python3-gi** - Python GTK bindings

### Packaging Tools (optional)
- **nfpm** - Package creator (for deb, rpm, apk, pacman)
- **flatpak-builder** - For Flatpak packages
- **sh** - Shell interpreter

### Install Requirements (Debian/Ubuntu/Kali)
```bash
sudo apt install meson ninja-build python3 python3-gi python3-requests gir1.2-gtk-4.0 gir1.2-adw-1 nfpm flatpak-builder
```

### Install Requirements (Arch Linux)
```bash
sudo pacman -S meson ninja python python-gobject python-requests gtk4 libadwaita nfpm flatpak-builder
```

### Install Requirements (Fedora)
```bash
sudo dnf install meson ninja-python3 python3-pygobject3 python3-requests gtk4 libadwaita nfpm flatpak-builder
```

## Building
```bash
meson setup build [--prefix <prefix>]
meson compile -C build
meson install -C build
```

## Development Workflow

### Quick rebuild:
```bash
# 1. Edit files in src/ or data/

# 2. Rebuild
meson setup --reconfigure build

# 3. Install
meson install -C build

# 4. Run
./build/src/catgirldownloader
```

### Full reinstall:
```bash
# Uninstall first (if already installed)
sudo ninja -C build uninstall

# Clean rebuild
rm -rf build
meson setup build
meson compile -C build
sudo meson install -C build

# Run
./build/src/catgirldownloader
```

### Build all packages:
```bash
./package.sh
# Output files in build/:
# - catgirldownloader_1.0.0_all.deb
# - catgirldownloader-1.0.0-1.noarch.rpm
# - catgirldownloader_1.0.0_noarch.apk
# - catgirldownloader_1.0.0-1-any.pkg.tar.zst
# - catgirldownloader-v0.5.tar.gz
```

## Features

### Supported Sources
| Source | Search Tags | Blacklist Tags |
|--------|-------------|----------------|
| Danbooru | Yes (custom) | Yes |
| Waifu.im | No | Yes |
| Nekos.moe | No | Yes |
