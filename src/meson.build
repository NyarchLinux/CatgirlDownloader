pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'catgirldownloader')
gnome = import('gnome')

gnome.compile_resources('catgirldownloader',
  'catgirldownloader.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'catgirldownloader.in',
  output: 'catgirldownloader',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

catgirldownloader_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'catgirl.py',
  'preferences.py',
  'preferenceswindow.py',
  'waifu.py',
  'types.py',
  'api_base.py',
]

install_data(catgirldownloader_sources, install_dir: moduledir)
