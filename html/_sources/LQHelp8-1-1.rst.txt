
.. index:: 
   pair: File; Open

.. _fileopen:

Open
====

Opens a dialogue box to select a DICOM file or series of DICOM files, a zipped series of DICOM files, image or machine log file to load. This function can be accessed using the Open images(s) button |open| on :ref:`maintoolbar` or by selecting Open from the :ref:`filemenu`. The number of images loaded is displayed in the :ref:`statusbar`.

Currently LinaQA will attempt to open the following DICOM modalities as images:

=======  ====================================================
RTIMAGE  Radiotherapy portal image, MV or kV
RTDOSE   Radiotherapy dose plane or 3D matrix
CT       Computed Tomography 2D or 3D image
NM       Nuclear Medicine (gamma camera) 2D or SPECT 3D image
PT       Positron Emission Tomograph (PET) image
MR       Magnetic Resonance Image (MRI) image
OT       Other image
XA       X-Ray Angiography
=======  ====================================================

Unsupported DICOM modalities will default to DICOM tag editing mode.

|Note| If you do not see the file you want make sure you have selected the correct file type.

|Note| If multiple DICOM images are selected for loading the images must have the same parameters, ie. modality, size, etc. Only a single multiframe image can be loaded at a time. Non-compliant images are discarded. The number of discarded images can be seen in the :ref:`statusbar`.

.. |Note| image:: _static/Note.png

.. |open| image:: _static/OpenImage.png
