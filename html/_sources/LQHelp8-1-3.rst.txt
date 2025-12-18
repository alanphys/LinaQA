
.. index:: 
   pair: File; Save

.. _filesave:

Save
====

Saves the current DICOM file. Changed pixel values are written to the pixel data array before saving. This function can be accessed using the 'Save image' button |save| on the :ref:`maintoolbar` or by selecting 'Save' from the :ref:`filemenu`.

|Note| This will overwrite the existing file. If changes have been made and the existing file should be kept use :ref:`filesaveas`. Files are stored internally uncompressed and will be saved uncompressed.

.. |Note| image:: _static/Note.png

.. |save| image:: _static/Save.png
