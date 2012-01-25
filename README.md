B4U reader for Python
=============

This library parses .b4u files, which are the native format of [Before You Know It](http://www.byki.com/), a great flashcard application.

Many B4U files can be downloaded from http://www.byki.com/listcentral.html.

Usage
------------
    import read
    d = read.Deck('verbos.b4u')
    d.html('output')

will read the file `verbos.b4u` and create a HTML representation, with separate .OGG and .JPEG files as needed, in the folder `output`