
.. index::
   pair: Gamma; Radiology

.. _gamma:

Gamma Analysis
==============

Calculates the Gamma difference between the current displayed image and the reference image. The analysis can be opened by clicking the |ga| button on the :ref:`dxtoolbar` or by selecting 'Radiology, Gamma' from the :ref:`analysemenu`.

The 'Distance to agreement' and 'Dose to agreement' as well as other settings can be set in :ref:`gammasettings` settings.

Please see the `Gamma function <https://pylinac.readthedocs.io/en/latest/core_modules.html#pylinac.core.image.BaseImage.gamma>`_ in the `Pylinac documentation <https://pylinac.readthedocs.io/en/latest/>`_ for more information.

|Note| The displayed image and the reference image must have the same parameters, i.e. size and pixel depth.

.. |ga| image:: _static/Gamma.png

.. |Note| image:: _static/Note.png
