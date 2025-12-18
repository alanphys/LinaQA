
.. index::
   pair: Images; DICOM

Images and DICOM files
======================

LinaQA is primarily intended to operate on DICOM images. Support for non-image DICOM files such as Radiation Dose Structured Reports (RDSR) is included. If the DICOM file is not in the list of supported modalities LinaQA will automatically open it in the :ref:`dicomtab`. Non-DICOM image files such as jpeg or tiff can be opened and displayed, but not all operations will work on them. certain non-image non-DICOM files such as trajectory log files can be opened, but these will not be displayed. See :ref:`fileopen`

DICOM files are stored internally as a `Pydicom <https://pydicom.github.io/pydicom/stable/>`_ Dataset. For multiple open 2D images such as a CT dataset a 3D array is created consisting of the stacked 2D images for display purposes. For a single multi-frame image the image is converted to a series of single frame 2D images and the 3D array is constructed of the stacked frames. Image processing operations generally work on the 3D array leaving the underlying pixel data unaffected. The exception is the pixel editor which operates on the 2D image and transfers changes back to the pixel data. Saving a single image will transfer the slice in the 3D array to the pixel data. Therefore, if any operations are carried out on an image, save the image to carry these changes through to any analysis.

DICOM images usually store the image data as raw pixel values in the pixel data array. These are the original pixel values from the imaging device and usually should not be interpreted in terms of some calibrated value such as Hounsfield Units (HU) or Dose, etc. Most image operations work on the raw pixel values except for the :ref:`sumimage` which will use the calibrated values if available.

In some instances it is desirable to view the image in terms of calibrated units such as Dose for an EPID image or SUV for a Nuclear Medicine image. These images contain a 'Rescale' DICOM tag including a 'RescaleSlope' and 'RescaleIntercept'. They create a linear relationship between the raw pixel values and the calibrated values. It is also possible to have Look Up Tables (LUTs) for more complex relationships but this is not implemented in LinaQA. LinaQA can toggle between displaying the raw pixel values and the calibrated pixel values using the :ref:`scalelut`.

Due to the limitations of Pylinac LinaQA does not transfer data for analysis very consistently. In some cases the data is transferred as a Pydicom dataset, in others as a filename and reopened, and in still others simply as a numpy array. This will hopefully be resolved in future versions.

Non-DICOM images are not stored at all, but simply displayed. This means that no operations can be carried out on them. Analysis can be carried out as the filename is passed to the analysis operation.
