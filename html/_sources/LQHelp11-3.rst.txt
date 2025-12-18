
.. index::
   pair: 2D Phantoms; Settings

.. _2Dphantomsettings:

2D Phantoms
===========

These contain customisable options for the :ref:`2Dphantoms`. Set values to 0 for automatic detection unless otherwise indicated. Available settings are:

*  **2D Type**: Sets the default 2D phantom. Select from the list provided.
*  **Angle override**: A manual override of the angle of the phantom. 0 is pointing from the center toward the right and positive values go counterclockwise.
*  **Center override**: A manual override of the center point of the phantom. Format is (x, y)/(col, row).
*  **Size override**: A manual override of the relative size of the phantom. This size value is used to scale the positions of the ROIs from the center.
*  **High contrast threshold**: This is the contrast threshold value which defines any high-contrast ROI as passing or failing.
*  **Low contrast threshold**: This is the contrast threshold value which defines any low-contrast ROI as passing or failing.
*  **SSD**: The SSD of the phantom itself in mm. If set to “auto”, will first search for the phantom at the SAD, then at 5cm above the SID.

|Note| Not all settings have been implemented.

|Hint| :ref:`Inverting<invert>` the image sets the invert flag.

.. |Note| image:: _static/Note.png

.. |Hint| image:: _static/Hint.png
