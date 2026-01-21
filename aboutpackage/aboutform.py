"""
=========================
Show a tabbed help window
=========================

Show a tabbed help window displaying the readme, licence and credits
"""
# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2019-2026
# SPDX-License-Identifier: Licence.txt:

from .aboutformui import Ui_AboutForm
from PyQt5.QtWidgets import QDialog
import os

version = '0.08.490'  # previous git commit 4ab4ca7a


class About(QDialog):
    def __init__(self):
        super(About, self).__init__()
        self.ui = Ui_AboutForm()
        self.ui.setupUi(self)
        self.setWindowTitle(f'About LinaQA v{version}')
        textpath = os.path.join(os.path.dirname(__file__), os.pardir)

        try:
            infile = open(os.path.join(textpath, "readme.txt"))
            try:
                self.ui.qlAbout.setText(infile.read())
            finally:
                infile.close()
        except IOError:
            self.ui.qlAbout.setText("Sorry! No readme available.")

        try:
            infile = open(os.path.join(textpath, "licence.txt"))
            try:
                self.ui.qlLicence.setText(infile.read())
            finally:
                infile.close()
        except IOError:
            self.ui.qlLicence.setText("Sorry! No licence available.")

        try:
            infile = open(os.path.join(textpath, "credits.txt"))
            try:
                self.ui.qlCredits.setText(infile.read())
            finally:
                infile.close()
        except IOError:
            self.ui.qlCredits.setText("Sorry! No credits available.")
