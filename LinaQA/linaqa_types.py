"""
===========================
Type definitions for LinaQA
===========================
"""
# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2026
# SPDX-License-Identifier: Licence.txt:

import inspect
from pylinac.picketfence import MLC
from pylinac.nuclear import Nuclide
from pylinac import planar_imaging

supported_modalities = ["RTIMAGE", "RTDOSE", "RTPLAN", "CT", "NM", "PT", "MR", "OT", "XA", "SR"]

supported_file_ext = [".dcm", ".ima", ".2", ".xim", ".jpg", ".jpeg", ".tif", ".tiff", ".png", ""]

# TODO pull these directly from class def
phantom3D_list = [
    "CatPhan503",
    "CatPhan504",
    "CatPhan600",
    "CatPhan604",
    "CatPhan700",
    "QuartDVT",
    "ACR CT",
    "ACR MRI",
    "GE Helios"]

vmat_list = ["DRGS", "DRMLC", "DRCS"]

phantom2D_list = [obj.common_name for name, obj in inspect.getmembers(planar_imaging) if hasattr(obj, "common_name")]

spatial_res_list = ["Four Bar", "Quadrant"]

mlc_list = [mlc.value.get("name") for mlc in MLC]

nuclide_list = [str(name) for name, value in vars(Nuclide).items() if not name.startswith("__")]

mean_area_def = ["Physical vol", "50% isodose"]

# colours for status bar messages
faint_red = "#ff7979"
faint_yellow = "#fffccf"
faint_green = "#d3ffe4"

