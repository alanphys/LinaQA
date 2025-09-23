LinaQA Readme file (c) Yenzakahle MPI 2024-2025


1) Introduction
LinaQA (pronounced Linakwa) is a GUI frontend for pylinac and pydicom. It is intended to be a general purpose medical physics quality assurance tool for radiotherapy, nuclear medicine and diagnostic radiology.

2) Licence
Please read the file Licence.txt. This means that if as a result of using this program you fry your patients, trash your linac, nuke the cat, blow the city power in a ten block radius and generally cause global thermonuclear meltdown! Sorry, you were warned!

3) System Requirements
Currently tested on
* Fedora 42/KDE 6.05/QT 5.15
* Window 10/Miniconda3
Windows users will need to install a python stack (such as anaconda) and PyQT5/QT5.

4) Dependencies
* PyQt5
* pylinac (tested with pylinac 3.35)
* pydicom (tested with pydicom 3.0.1)
* NumPy
If you install pylinac it will automatically install pydicom and numpy.

LinaQA can read compressed images and save them uncompressed, but to do this it needs the additional libraries below which must be installed independently:
* pylibjpeg
* pylibjpeg-libjpeg
* GDCM (optional depending on type of compression)

5) Installation
This assumes the latest version of mini/anaconda or other python interpreter is installed.

Install PyQt5
Open miniconda prompt
>pip install PyQt5

Test if PyQt5 is active
At the minconda command prompt go into python
>python
from the python prompt
>>>from PyQt5 import QtCore
If does not give an error message your installation is active.
Exit python
>>>quit()

Install pylinac if it is not already installed. If it is installed consider upgrading to the latest version.
>pip install pylinac
or
>pip install pylinac --upgrade


Test pylinac install
At the minconda command prompt go into python
>python
from the python prompt
>>>from pylinac import DRGS
>>>DRGS.run_demo()
if the DRGS demo windows appears pylinac is active
Exit python
>>>quit()

Install LinaQA
Unzip LinaQA.zip into a suitable directory
At the minconda command prompt navigate to the LinaQA directory
start LinaQA by
>python LinaQA.pyw

This installation method is temporary and will be replaced by the conventional pip install when LinaQA is stable.

6) Use
Open a console window (miniconda prompt for windows users), change to the above directory and run
python LinaQA.pyw
or
python LinaQA.pyw \Path\to\DICOM\

Open a file either from the menu or toolbar. Drag and drop from your favourite file manager is also supported. Note: For multiple files such as a CatPhan series the files must be selected in the file open dialog. You can use <ctrl>-A to select all files.

Open the reference image if needed.

Select the appropriate MLC, phantom or test if necessary. Defaults can be set in "Settings"

Click the relevant Test button.

Non image files such as machine logs (BIN) currently will not be displayed, but the test can still be run.

7) Release notes
These detail new or changed functionality in LinaQA. Please see the History for bug fixes

Current
Image sum from a set of images added. Image rescaling added. Nuclear medicine toolbar added. Toolbars can be made persistent in the settings. Implemented Maximum Count Rate, Simple Sensitivity, Planar Uniformity, Planar Spatial Resolution, Tomographic Uniformity, Tomographic Resolution, Tomographic Contrast and Centre of Rotation analysis. Added handling of multiframe images. Settings unit has been overhauled.

Version 0.06
Zip files can be uncompressed and displayed on the fly. ACR CT and ACR MRI Large tests have been added. Fixed broken gamma analysis. Force option added to "Settings/Pydicom". If this is set to True will try and load the file as a DICOM image. Useful for DICOM files with badly formed headers but can have unpredictable results. Imaging and DICOM toolbars have been added. Toolbars can be toggled on/off. Imaging auto window and Invert icons moved to Imaging tool bar along with Gamma comparison. DICOM Find, Add, Edit and Delete icons moved to DICOM toolbar. Gamma analysis and DICOM icons removed from Radiotherapy toolbar. This is a GUI redesign to enable future expansion. Compute average image from a set of images added to imaging toolbar.

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

8) History
See GIT log.

9) To Do
Run on PySide or PyQt, which ever is available.
Integrate PDFs
Implement integrity checking
Add documentation
Migrate to Qt6

10) Known issues
DICOM sequences cannot be inserted, deleted or edited.
