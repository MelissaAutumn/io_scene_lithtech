import argparse
from PIL import Image
from io_scene_lithtech.dtx import DTX

parser = argparse.ArgumentParser(
    prog='ConvertTex',
    description='Converts DTX files to whatever pillow supports')

parser.add_argument('dtx_file')
parser.add_argument('img_file', default=None)

args = parser.parse_args()

if not args.img_file:
    args.img_file = f'{args.dtx_file.rsplit('.')[0]}.png'

def convert(dtx_file: str, img_file: str):
    print(f'Reading {dtx_file}')
    print('Decoding DTX...')
    dtx_obj = DTX(dtx_file)
    img_obj: Image = Image.frombytes('RGBA', (dtx_obj.width, dtx_obj.height), bytes(dtx_obj.pixels))
    img_obj.save(img_file, 'png')


convert(args.dtx_file, args.img_file)