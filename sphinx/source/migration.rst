Migrating from SkoolKit 3
=========================
SkoolKit 4 includes some changes that make it incompatible with SkoolKit 3. If
you have developed a disassembly using SkoolKit 3 and find that `skool2html.py`
no longer works with your `skool` files or `ref` files, or produces broken
output, look through the following sections for tips on how to migrate your
disassembly to SkoolKit 4.

[Info]
------
The ``[Info]`` section, introduced in SkoolKit 2.0, is not supported in
SkoolKit 4. If you have one in your `ref` file, copy its contents to the
:ref:`ref-Game` section.

[Graphics]
----------
The ``[Graphics]`` section, introduced in SkoolKit 2.0.5, is not supported in
SkoolKit 4. If you have one in your `ref` file, you can migrate it thus:

* Rename the ``[Graphics]`` section ``[PageContent:Graphics]``
* Add an empty ``[Page:Graphics]`` section to the `ref` file::

    [Page:Graphics]

* Add the following line to the ``[Paths]`` section::

    Graphics=graphics/graphics.html

* Add the ``Graphics`` page ID to the ``[Index:Graphics:Graphics]`` section to
  make a link to it appear on the disassembly index page; for example::

    [Index:Graphics:Graphics]
    Graphics
    GraphicGlitches