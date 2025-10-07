
.. index::
   pair: Pydicom; Settings

.. _pydicomsettings:

Pydicom
=======

These contain customisable options for `Pydicom <https://pydicom.github.io/pydicom/stable/>`_. Available settings are:

*  **Force**: If true Pydicom will try and open a file as a DICOM file. Use this if the file is not fully DICOM compliant.
*  **Scale factor**: Default amount to rescale the image or image series by. Use with :ref:`scaleimage`

|Note| Not all settings have been implemented.

.. |Note| image:: _static/Note.png
