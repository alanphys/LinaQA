"""
=========================================================================
Data file import routines
=========================================================================
"""

# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2026
# SPDX-License-Identifier: Licence.txt:

from pydicom import Dataset, dcmread, uid, errors
from linaqa_types import supported_modalities


def read_dicom(filename, force_read: bool = False) -> tuple[Dataset, bool]:
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
    if ds.NumberOfFrames > 1:                # file is multi-frame image
        stop_reading = True
    if not hasattr(ds, "PixelData"):             # file is not image
        stop_reading = True
    # uncompress image if it is compressed
    if ds.file_meta.TransferSyntaxUID.is_compressed:
        ds.decompress()
    return ds, stop_reading
