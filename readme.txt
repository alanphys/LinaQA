LinaQA Readme file (c) Yenzakahle MPI 2024


1) Introduction
LinaQA (pronounced Linakwa) is a GUI frontend for pylinac and pydicom. It is intended to be a general purpose medical physics quality assurance tool for radiotherapy, nuclear medicine and diagnostic radiology.

2) Licence
Please read the file Licence.txt. This means that if as a result of using this program you fry your patients, trash your linac, nuke the cat, blow the city power in a ten block radius and generally cause global thermonuclear meltdown! Sorry, you were warned!

3) System Requirements
Currently tested on
* Fedora 36/KDE 5.27/QT 5.15
* Window 10/Miniconda3
Windows users will need to install a python stack (such as anaconda) and PyQT5/QT5.

4) Dependencies
* PyQt5
* pylinac (tested with pylinac 3.20)
* pydicom (tested with pydicom 2.4.2)
* NumPy
If you install pylinac it will automatically install pydicom and numpy.

5) Installation
Copy the files into a directory

6) Use
Open a console window (miniconda prompt for windows users), change to the above directory and run
python LinaQA.pyw

Open a DICOM file either from the menu or toolbar. Drag and drop from your favourite file manager is also supported. Note: For mulitple files such as a CatPhan series the files must be selected in the file dialog.

Open the reference image if needed.

Select the appropriate MLC, phantom or test if necessary. Defaults can be set in "Settings"

Click the relevant Test button.

Non DICOM files such as machine logs (BIN) or film scans (JPG, TIF) currently will not be displayed, but the test can still be run.

7) Release notes
These detail new or changed functionality in BeamScheme. Please see the History for bug fixes

Version 0.02
Second draft based on PyQt5 due to problems with Miniconda.
Implemented StarShot and Machine Logs. Added version string and updated About package.

Version 0.01
First draft based on PySide2
Implemented DICOM Tags, CatPhan, Picket Fence, 2D phantoms, VMAT and Winston-Lutz

8) History

9) To Do
Run on PySide or PyQt, which ever is available.
Integrate PDFs
Error reporting to status bar
Edit DICOM tags
Show machine log?
