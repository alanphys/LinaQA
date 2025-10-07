
.. index::
   pair: Starshot; Settings

.. _starshotsettings:

Starshot
========

These contain customisable options for the :ref:`starshot`. Available settings are:

*  **DPI**: Image resolution in Dots Per Inch (DPI). Usually needed for scanned film.
*  **Normalised analysis radius**: Distance in % between starting point and closest image edge; used to build the circular profile which finds the radiation lines. Must be between 0.05 and 0.95.
*  **Recursive analysis**: If True will recursively search for a “reasonable” wobble.
*  **SID**: Source Image Distance (SID) in mm. Usually needed for scanned film.
*  **Tolerance**: The tolerance in mm to test against for a pass/fail result.

|Note| Not all settings have been implemented.

|Hint| :ref:`Inverting<invert>` the image sets the invert flag. Invert the image if the automatically-determined pylinac inversion is incorrect.

.. |Note| image:: _static/Note.png

.. |Hint| image:: _static/Hint.png
