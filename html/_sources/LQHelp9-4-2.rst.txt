
.. index::
   pair: Simple Sensitivity; Nuclear Medicine

.. _simplesens:

Simple Sensitivity Analysis
===========================

Calculates the planar sensitivity of each collimator in counts per second per becquerel of a Gamma Camera image. To use a background image open it as the reference image. The analysis can be opened by clicking the |ss| button on the :ref:`nmtoolbar` or by selecting 'Simple Sensitivity' from the :ref:`nucmedmenu` analysis menu.

The 'Activity' and 'Nuclide' can be set in the 'Simple Sensitivity' group in :ref:`simplesenssettings`.

Please see `Simple Sensitivity <https://pylinac.readthedocs.io/en/latest/nuclear.html#simple-sensitivity>`_ in the `Pylinac documentation <https://pylinac.readthedocs.io/en/latest/>`_ for more information.

|Note| Currently this test does not handle multiframe images such as those from a dual head camera well. The background images are averaged. As a workaround save the multiframe image and background as separate image series (see :ref:`filesaveall`) and then load the separate image with its corresponding background for analysis.

.. |ss| image:: _static/SimpleSensitivity.png

.. |Note| image:: _static/Note.png
