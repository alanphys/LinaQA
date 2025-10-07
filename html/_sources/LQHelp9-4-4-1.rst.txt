
.. index::
   pair: Four Bar; Spatial Resolution

.. _fourbar:

Four Bar Spatial Resolution Analysis
====================================

Calculates the spatial resolution in terms of the Full Width Half Maximum (FWHM) and Full Width Tenth Maximum (FWTM) of a Gamma Camera image using the four bar method.

While the default settings are usually sufficient certain settings can be changed as given in :ref:`spatialressettings` settings.

Please see `Four Bar Spatial Resolution <https://pylinac.readthedocs.io/en/latest/nuclear.html#four-bar-spatial-resolution>`_ in the `Pylinac documentation <https://pylinac.readthedocs.io/en/latest/>`_ for more information.

|Note| A Gaussian fit is done to the peaks and the FWHM and FWTM determined from the fit. The FWTM may be unreliable.

.. |Note| image:: _static/Note.png
