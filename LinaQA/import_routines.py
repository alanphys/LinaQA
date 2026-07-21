"""
=========================================================================
Data file import routines
=========================================================================
"""

# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2026
# SPDX-License-Identifier: Licence.txt:

from PyQt5.QtCore import QSettings
from pydicom import Dataset, dcmread, uid, errors
from pylinac.core.image import XIM, load
from linaqa_types import supported_modalities


settings = QSettings()

def is_similar_image(current, previous: Dataset) -> bool:
    return (current.Modality == previous.Modality and
            current.Rows == previous.Rows and
            current.Columns == previous.Columns)


def read_dicom(filename: str, force_read: bool=False) -> tuple[Dataset, bool]:
    """Read one DICOM file. Set stop flag if a multiframe image file or not a DICOM image file ."""
    stop_reading = False
    ds = dcmread(filename, force=force_read)
    if ds.Modality not in supported_modalities:
        raise errors.InvalidDicomError
    if "TransferSyntaxUID" not in ds.file_meta:
        ds.file_meta.TransferSyntaxUID = uid.ImplicitVRLittleEndian
    if "SpacingBetweenSlices" not in ds:
        ds.SpacingBetweenSlices = ds.SliceThickness if "SliceThickness" in ds else 1
    if "NumberOfFrames" not in ds:
        ds.NumberOfFrames = 1
    # conditions to stop reading
    if ds.NumberOfFrames > 1:                    # file is multi-frame image
        stop_reading = True
    if not hasattr(ds, "PixelData"):             # file is not image
        stop_reading = True
    # uncompress image if it is compressed
    if ds.file_meta.TransferSyntaxUID.is_compressed:
        ds.decompress()
    return ds, stop_reading


def read_xim(filename: str, args):
    """Read one XIM file"""
    # may need to add additional DICOM tags here. Pylinac's conversion is sketchy.
    stop_reading = False
    xim = XIM(filename)
    ds = xim.as_dicom()
    return ds, stop_reading


def read_tiff(filename: str, args):
    """Read one image file"""
    # may need to add additional DICOM tags here. Pylinac's conversion is sketchy.
    stop_reading = False
    tiff = load(filename)
    tiff.sid = settings.value("Star shot/SID", 1000, type=int)
    # modify to pull gantry, coll and couch from file name?
    ds = tiff.as_dicom(gantry=0, coll=0, couch=0)
    default_dpi = settings.value("Star shot/DPI", 75, type=int)
    dpi = tiff.dpi if tiff.dpi else default_dpi
    ds.ImagePlanePixelSpacing = [25.4 / dpi, 25.4 / dpi]
    return ds, stop_reading
