Command-line tools to read City of Heroes PIGG files.

Requirements: Python 2.x, with the zlib module.


readpigg
--------

To list the contents of a .pigg file:

python readpigg.py -l file.pigg

To unpack a single file:

python readpigg.py file.pigg file

To unpack all files:

python readpigg.py file.pigg

The tool will reproduce the original directory structure,
creating directories as needed, then placing the unpacked
files in the proper subdirectory.


readtexture
-----------

To convert a .texture file, you can use:

python readtexture.py file.texture

The tool will recover the original .dds file. You can
then convert the .dds file to a standard format using any
DDS converter (e.g., Nvidia's). If you want a command-line
tool (e.g., if you want to convert in bulk), you can use
ImageMagick, for example.


readbin
-------

NOTE: listing items and parsing single items currently does not
work for all .bin files. For such files, your only option is to
parse the whole file.

To list the contents of a .bin file:

python readbin.py -l file.bin

To parse a single item in a .bin file:

python readbin.py file.bin item

To parse the whole .bin file:

python readbin.py

If you want the output sent to a text file, you can do:

python readbin.py > outfile.txt
