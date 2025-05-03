# io_scene_lithtech

This addon is forked from [io_scene_abc](https://github.com/cmbasnett/io_scene_abc), renamed to io_scene_lithtech due to the increased scope.

This addon provides limited support for importing and exporting various Lithtech models formats from [various games](https://en.wikipedia.org/wiki/LithTech#Games_using_LithTech) such as [Shogo](https://en.wikipedia.org/wiki/Shogo:_Mobile_Armor_Division), and [No One Lives Forever](https://en.wikipedia.org/wiki/The_Operative:_No_One_Lives_Forever) to and from Blender 4.2+

## How To Install

Grab the latest release from the [releases](https://github.com/MelissaAutumn/io_scene_lithtech/releases) section.

Install on Blender 4.2.0 (LTS) or higher.

## Development

### Setup

To get started you'll need to install [uv](https://docs.astral.sh/uv). Once installed run `uv sync` to kick-start a 
local python venv, and download/install the project requirements. 

Next generate the blender_manifest.toml with the following command:

```shell
uv run scripts/make_manifest.py
```

This step uses information from pyproject.toml to fill in blender_manifest.toml. It also allows us to add any extra 
wheels (third party libraries) or other settings conditionally. Right now the only extra argument is to add the 
pycharm debug fork of pydevd for linux x86_64 boxes (aka my machine.)

### Linting

For linting and formatting we use ruff. ruff can be accessed via `uvx ruff check` or `uvx ruff check --fix` to fix any 
found linting issues.

### Developing in Blender

To install for development all you need to do is create a local repository pointing to the plugin's src folder.

* Edit -> Preferences
* Within preferences select the Get Extensions tab
* Click on the Repositories select box on the top right of the Get Extensions panel
* Click + and select local repository
* Name the repository `io_scene_lithtech (dev)`, tick custom directory and select this project's `src` directory
* Enable the extension in the Add-ons tab

## Supported Formats

| Format    | Import             | Export             |
|-----------|--------------------|--------------------|
| ABCv6     | Full               | Full               |
| ABCv13    | Rigid and Skeletal | Limited            |
| LTA       | No                 | Rigid and Skeletal |
| LTB (PS2) | Rigid and Skeletal | No                 |
| LTB (PC)  | Rigid and Skeletal | No                 |

The ABC file format description can be found on our wiki [here](https://github.com/cmbasnett/io_scene_abc/wiki/ABC).

Additional format information can be found in [here](https://github.com/melissaautumn/io_scene_lithtech/tree/master/research)

## Known Issues
 - In order to export you must have a mesh, a armature hooked up, and at least one animation action setup
 - Socket locations are a tad off in Blender (They're fine in engine.)
 - Imported skeletal meshes are mirrored on the X axis (They're flipped back on export!)
 - Converters may not provide 1:1 source files
 - Converters don't convert lods!

![](https://raw.githubusercontent.com/haekb/io_scene_lithtech/master/doc/readme/example.png)

## Credits
* [**Colin Basnett**](https://github.com/cmbasnett) - Original Creator / Programming
* [**ReindeerFloatilla**](https://github.com/ReindeerFloatilla) - Research
* [**Haekb**](https://github.com/haekb) - Previous Maintainer / Programming / Research
* [**Amphos**](https://github.com/Five-Damned-Dollarz) - Programming
* [**Psycrow**](https://github.com/Psycrow101) - Programming
* [**Melissa Autumn**](https://github.com/melissaautumn) - Current Maintainer / Programming / Research
