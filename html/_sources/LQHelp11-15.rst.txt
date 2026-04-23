
.. index::
   pair: SUV Uptake; Settings

.. _suvuptakesettings:

SUV Uptake
==========

These contain customisable options for the :ref:`suvuptake`. Available settings are:

*  **Background dose**: Activity in Mega Bequerels (MBq) injected into background vol. If None it will be taken from sphere_dose.
*  **Background vol**: Volume of phantom background compartment (phantom vol - inserts vol)
*  **Mean area**: Choose between physical sphere volume or 50% isodose volume to calculate the SUV mean.
*  **Search Slices**: Number of image slices to search from sphere starting points
*  **Search window px**: Number of pixels to search from sphere starting points
*  **Sphere angles**: Comma delimited list of sphere angles starting at horizontal right and going counterclockwise.
*  **Sphere diameters mm**: Comma delimited list of sphere diameters in mm corresponding to the **sphere angles**
*  **Stock dose**: Activity in MBq injected into stock solution. If None it will be taken from series metadata.
*  **Stock vol**: Volume of stock solution mixed before injection into spheres
