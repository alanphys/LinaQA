
.. index::
   pair: 2D Phantoms; Radiotherapy

.. _2Dphantoms:

2D Phantom Analysis
===================

Analyse single images acquired from 2D image quality phantoms. The analysis can be opened by clicking the |ld| button on the :ref:`rxtoolbar` or by selecting 'Radiotherapy, 2D Phantoms' from the :ref:`analysemenu`. The phantom type can be selected from the list box underneath the |ld| button. The default phantom can be specified in :ref:`2Dphantomsettings` settings. If the image is :ref:`inverted <invert>` the invert flag is set and passed to the analysis. The 2D phantoms that are currently implemented are:

*  Doselab MC2 MV
*  Doselab MC2 kV
*  Doselab RLf
*  Elekta Las Vegas
*  IBA Primus A
*  IMT L-Rad
*  PTW Iso-Align
*  Las Vegas
*  Leeds
*  Leeds (Blue)
*  PTW EPID QC
*  SNC FSQA
*  SNC MV-QA
*  SNC MV-QA (12510)
*  SNC kV-QA
*  SI FC-2
*  SI QC-3
*  SI QC-kV]


While the default settings are usually sufficient certain settings can be changed as given in :ref:`2Dphantomsettings` settings. Please see the `Planar Imaging Module <https://pylinac.readthedocs.io/en/latest/planar_imaging.html#>`_ in the `Pylinac documentation <https://pylinac.readthedocs.io/en/latest/>`_ for more information.


.. |ld| image:: _static/LasVegas.png

.. |Note| image:: _static/Note.png
