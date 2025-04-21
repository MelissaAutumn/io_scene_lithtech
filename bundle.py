from glob import glob
from zipfile import ZipFile
import tomllib


def main():
    base_dir = 'src/io_scene_lithtech/'

    with open('blender_manifest.toml', 'rb') as fh:
        config = tomllib.load(fh)

    id = config.get('id')
    version = config.get('version')

    zip_name = f'{id}-{version}.zip'

    with ZipFile(zip_name, 'w') as extZip:
        extZip.write('LICENSE', 'io_scene_lithtech/LICENSE')
        extZip.write('README.md', 'io_scene_lithtech/README.md')
        for file in glob(f'{base_dir}/**'):
            out_file = file.replace(base_dir, '')
            extZip.write(file, f'io_scene_lithtech/{out_file}')


if __name__ == "__main__":
    main()
