# io_scene_lithtech

This addon is forked from [io_scene_abc](https://github.com/cmbasnett/io_scene_abc), renamed to io_scene_lithtech due to the increased scope.

This addon provides limited support for importing and exporting various Lithtech models formats from [various games](https://en.wikipedia.org/wiki/LithTech#Games_using_LithTech) such as [Shogo](https://en.wikipedia.org/wiki/Shogo:_Mobile_Armor_Division), and [No One Lives Forever](https://en.wikipedia.org/wiki/The_Operative:_No_One_Lives_Forever) to and from Blender 2.8x/2.9x.

## How To Install

Download or clone the repository, and zip up the contents of the `src` folder. Go to `Edit -> Preferences` in Blender 2.8x/2.9x, go to the `Add-ons` tab, select `install` and then select the zip file you just created.

To download the respository, click the green `Code -> Download ZIP` at the top of the main page.

...or grab a release zip if one is there!

## Development

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

Additional format information can be found in [here](https://github.com/haekb/io_scene_lithtech/tree/master/research)

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
* [**Haekb**](https://github.com/haekb) - Current Maintainer / Programming / Research 
* [**Amphos**](https://github.com/Five-Damned-Dollarz) - Programming
* [**Psycrow**](https://github.com/Psycrow101) - Programming