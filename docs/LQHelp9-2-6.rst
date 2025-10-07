
.. index::
   pair: Starshot; Radiotherapy

.. _starshot:

Starshot Analysis
=================

Analyse a starshot image or image series. The image can be EPID(DICOM) or film based and can be generated from collimator, MLC, gantry or couch. The analysis can be opened by clicking the |ss| button on the :ref:`rxtoolbar` or by selecting 'Radiotherapy, Starshot' from the :ref:`analysemenu`. While the default settings are usually sufficient certain settings can be changed as given in :ref:`starshotsettings`.

Please see the `Starshot Module <https://pylinac.readthedocs.io/en/latest/starshot_docs.html>`_ in the `Pylinac documentation <https://pylinac.readthedocs.io/en/latest/>`_ for more information.

|Hint| It is not necessary to sum or average individual star shot spoke images before analysis. The analysis will automatically combine a series of images.

.. |ss| image:: _static/Starshot.png

.. |Hint| image:: _static/Hint.png
