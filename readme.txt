LinaQA Readme file (c) Yenzakahle MPI 2024-2026


1) Introduction
LinaQA (pronounced Linakwa) is a GUI frontend for pylinac and pydicom. It is intended to be a general purpose medical physics quality assurance tool for radiotherapy, nuclear medicine and diagnostic radiology.

2) Licence
Please read the file Licence.txt. This means that if as a result of using this program you fry your patients, trash your linac, nuke the cat, blow the city power in a ten block radius and generally cause global thermonuclear meltdown! Sorry, you were warned!

3) System Requirements
Currently tested on
* Fedora 42/KDE 6.05/QT 5.15
* Windows 11

4) Installation
From version 0.9 the Windows version of LinaQA is available as a one-file executable. Copy the LinaQA-0.X.xxx.exe file into an appropriate directory where X.xxx is the version number.

LinaQA can still be installed in a Mini/Anaconda/python environment from Github.

5) Use
For Windows:
From version 0.9 LinaQA is started from the one-file executable. Execute by double clicking the file from File Explorer. Mini/Anaconda is no longer required. Alternatively if you did a virtual environment install, open a console window, change to the install directory and run:

LinaQA-0.X.xxx.exe
or
LinaQA-0.X.xxx.exe \Path\to\DICOM\

For Linux open a console in the install directory and run:
linaqa.sh
or
linaqa.sh \Path\to\DICOM\

In LinaQA, open a file either from the menu or toolbar. Drag and drop from your favourite file manager is also supported. Note: For multiple files such as a CatPhan series the files must be selected in the file open dialog. You can use <ctrl>-A to select all files.

Open the reference image if needed.

Select the appropriate MLC, phantom or test if necessary. Defaults can be set in "Settings". Some settings can be changed on the fly by long press or right click on the respective Test button.

Click the relevant Test button.

Non image files such as machine logs (BIN) currently will not be displayed, but the test can still be run.

6) Release notes
These detail new or changed functionality in LinaQA. Please see the History for bug fixes

Current
The Windows version is available as a one-file executable containing all dependencies. Pylinac has been incorporated as a submodule PylinaQA.

Version 0.08
Documentation added. Error handling improved. Flip image left-right and up-down added. Toggable image display between raw pixels and real world value map, e.g. dose for EPID or activity concentration for NM/PET added. Quick set popup menus added to change parameters and analyses on the fly. DRCS added to VMAT analysis. SUV uptake analysis (EARL) added. Settings moved to Tab interface. Setting added to toggle toolbar icon text on/off. Script files added to automatically invoke python and start LinaQA. XIM image handling added. Raster images converted to DICOM on import. GE Helios Daily analysis added.

Version 0.07
Image sum from a set of images added. Image rescaling added. Nuclear medicine toolbar added. Toolbars can be made persistent in the settings. Implemented Maximum Count Rate, Simple Sensitivity, Planar Uniformity, Planar Spatial Resolution, Tomographic Uniformity, Tomographic Resolution, Tomographic Contrast and Centre of Rotation analysis. Added handling of multiframe images. Settings unit has been overhauled.

Version 0.06
Zip files can be uncompressed and displayed on the fly. ACR CT and ACR MRI Large analyses have been added. Fixed broken gamma analysis. Force option added to "Settings/Pydicom". If this is set to True will try and load the file as a DICOM image. Useful for DICOM files with badly formed headers but can have unpredictable results. Imaging and DICOM toolbars have been added. Toolbars can be toggled on/off. Imaging auto window and Invert icons moved to Imaging tool bar along with Gamma comparison. DICOM Find, Add, Edit and Delete icons moved to DICOM toolbar. Gamma analysis and DICOM icons removed from Radiotherapy toolbar. This is a GUI redesign to enable future expansion. Compute average image from a set of images added to imaging toolbar.

Version 0.05
Images are now handled internally uncompressed. Saving an image will save it uncompressed. The entire dataset may be saved. The image invert flag is carried through to analysis methods. Where methods do not have an invert flag the images are explicitly inverted.

Version 0.04
Implement QuartDVT phantom. Enable directory/file load from command line. Fix DICOM tag insert, delete and edit for nested tags. Note: Only tags can be inserted and deleted, not sequences.

Version 0.03
Add gamma function, DICOM tag editing and DICOM pixel data editing. Cater for high dpi and tweak UI. Support JPEG, TIFF and other image files for Starshot.

Version 0.02
Second draft based on PyQt5 due to problems with Miniconda.
Implemented StarShot and Machine Logs. Added version string and updated About package.

Version 0.01
First draft based on PySide2
Implemented DICOM Tags, CatPhan, Picket Fence, 2D phantoms, VMAT and Winston-Lutz

7) History
See GIT log.

8) To Do
Use internal PDF viewer
Implement integrity checking
Migrate to Pyside6

9) Known issues
DICOM sequences cannot be inserted, deleted or edited.
