import argparse
from glob import glob
from zipfile import ZipFile
import tomllib

import jinja2


def main(pycharm_debug = False):
    base_dir = '../src/io_scene_lithtech'

    loader = jinja2.FileSystemLoader('./templates/')
    env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)

    with open('../pyproject.toml', 'rb') as fh:
        project_manifest = tomllib.load(fh)

    project_info = project_manifest.get('project', {})
    project_urls = project_info.get('urls', {})

    env.globals['addon_id'] = project_info.get('name')
    env.globals['addon_version'] = project_info.get('version')
    env.globals['addon_name'] = project_info.get('name', '').replace('_', ' ').capitalize()
    env.globals['addon_description'] = project_info.get('description')
    env.globals['addon_maintainers'] = ', '.join([m.get('name') for m in project_info.get('maintainers', [])])
    env.globals['addon_licenses'] = [ f'SPDX:{project_info.get('license')}' ]
    env.globals['addon_url'] = project_urls.get('Repository', project_urls.get('Homepage'))
    if pycharm_debug:
        env.globals['pychame_debug'] = True

    manifest = env.get_template('blender_manifest.toml.j2').render()
    with open(f'{base_dir}/blender_manifest.toml', 'w') as fh:
        fh.write(manifest)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Make Manifest', description='Generates a blender manifest file based on values from pyproject.toml'
    )

    parser.add_argument('pycharm_debug', action='store_true')
    args = parser.parse_args()
    main(args.pycharm_debug)
