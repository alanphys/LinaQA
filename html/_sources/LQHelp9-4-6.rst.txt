
.. index::
   pair: Tomographic Resolution; Nuclear Medicine

.. _tomores:

Tomographic Resolution Analysis
===============================

Calculates the spatial resolution in terms of the Full Width Half Maximum (FWHM) and Full Width Tenth Maximum (FWTM) of a SPECT image in all three dimensions (x,y,z). The analysis can be opened by clicking the |tr| button on the :ref:`nmtoolbar` or by selecting 'Tomographic Resolution' from the :ref:`nucmedmenu` analysis menu. No settings are currently available.

Please see `Tomographic Resolution <https://pylinac.readthedocs.io/en/latest/nuclear.html#tomographic-resolution>`_ in the `Pylinac documentation <https://pylinac.readthedocs.io/en/latest/>`_ for more information.

|Note| A Gaussian fit is done to the peak and the FWHM and FWTM is determined from the fit. The FWTM may be unreliable.

.. |tr| image:: _static/TomoRes.png

.. |Note| image:: _static/Note.png
