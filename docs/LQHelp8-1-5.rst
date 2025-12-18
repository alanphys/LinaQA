
.. index:: 
   pair: File; Save All

.. _filesaveall:

Save All
========

Saves the entire DICOM series under a new name. Multiframe images are converted into a series of single images. This is very useful for decompressing image series for import into a planning system. The 3D pixel array is **not** written to the individual dataset pixel arrays so image operations and processing changes will not be saved. This behaviour may change in future releases.

|Hint| Use this option to decompress a compressed image series.

|Hint| Use this option to convert a multiframe image into a series of single images.

|Note| DICOM files are stored internally uncompressed and are saved uncompressed.

|Note| Image changes are not save under 'Save All'

.. |Note| image:: _static/Note.png

.. |Hint| image:: _static/Hint.png

