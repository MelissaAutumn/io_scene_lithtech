from glob import glob
from zipfile import ZipFile
import tomllib


def main():
    base_dir = '../src/io_scene_lithtech'

    with open(f'{base_dir}/blender_manifest.toml.prod', 'rb') as fh:
        config = tomllib.load(fh)

    id = config.get('id')

    zip_name = f'../{id}.zip'

    with ZipFile(zip_name, 'w') as extZip:
        extZip.write('../LICENSE', 'io_scene_lithtech/LICENSE')
        extZip.write('../README.md', 'io_scene_lithtech/README.md')
        for file in glob(f'{base_dir}/**'):
            if '__pycache__' in file:
                continue
            # Ignore our dev manifest / local defines
            if file.endswith('blender_manifest.toml') or file.endswith('local_defines.py'):
                continue
            out_file = file.replace(f'{base_dir}/', '')
            # Copy our prod manifest as just blender_manifest.toml
            if file.endswith('blender_manifest.toml.prod'):
                out_file = file.replace('.prod', '')
            extZip.write(file, f'io_scene_lithtech/{out_file}')


if __name__ == "__main__":
    main()
