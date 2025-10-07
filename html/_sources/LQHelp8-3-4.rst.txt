
.. index:: 
   pair: Sum; Image

.. _sumimage:

Sum Image
=========

Sums the loaded image series to a single image.  All the loaded images are used. Images must be of a single type, i.e. same size and pixel representation. To prevent integer overflow the image values are converted to floating point and added. The resulting image is rescaled to maxint and converted back to integer. If there is a linear display relationship or gray scale mapping this is preserved and adjusted accordingly. This means that dose information in EPID images is preserved. The images can be summed by clicking the |sum| button on the :ref:`dxtoolbar` or by selecting 'Sum Image' from the :ref:`imagemenu`. This is a destructive operation, i.e. it changes the image data.

|Note| Image data will be changed. Save the image to make the changes permanent.

.. |sum| image:: _static/ImageSum.png

.. |Note| image:: _static/Note.png
