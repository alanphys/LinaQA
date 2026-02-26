"""
=========================================================================
Extra functionality for pylinac classes. Merge into pylinac at some stage
=========================================================================
"""

# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2026
# SPDX-License-Identifier: Licence.txt:

import io
import os
import math
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.colors as colors
from scipy.optimize import curve_fit, minimize
from scipy.ndimage import center_of_mass
from skimage.morphology import isotropic_erosion

from pydicom import Dataset, dcmread

# We need to monkey patch NMImageStack to accept a dataset. This is bad practice, very bad, but the only
# workaround I have at the moment.
from pylinac.core.image import DicomImage, NMImageStack, _rescale_dicom_values
from pylinac.core.geometry import Circle, direction_to_coords
import functools


def patch_nm_image_stack():
    original_init = NMImageStack.__init__

    @functools.wraps(original_init)
    def enhanced_init(self, paths: str | Path | list[Dataset], raw_pixels: bool = False):
        """The enhanced init has been contracted to a single function to deal with the RAW/Lut case and does
        not call the original init any more. This means backward compatibility is broken."""
        self.path = paths
        self.frames = []
        for path in paths:
            ds = path if isinstance(path, Dataset) else dcmread(path, force=True)
            if ds.Modality not in ["NM", "PT"]:
                raise TypeError("The file is not a NM image")
            full_array = ds.pixel_array
            # we may have a single dataset with multiple frames
            if hasattr(ds, 'NumberOfFrames') and (ds.NumberOfFrames > 1):
                for i in range(ds.NumberOfFrames):
                    array = full_array[i]
                    img = DicomImage.from_dataset(ds)
                    img.array = _rescale_dicom_values(array, ds, raw_pixels, False)
                    self.frames.append(img)
            # or we may have multiple images with one frame each
            else:
                img = DicomImage.from_dataset(ds)
                img.array = _rescale_dicom_values(full_array, ds, raw_pixels, False)
                self.frames.append(img)
        self.metadata = ds

    NMImageStack.__init__ = enhanced_init


# apply the patch
patch_nm_image_stack()

from pylinac.nuclear import gaussian_fit, TomographicResolutionAxisData


def patch_tomo_res_axis_data():
    original_post_init = TomographicResolutionAxisData.__post_init__

    @functools.wraps(original_post_init)
    def new_post_init(self):
        # np.argmax is a better estimator for the position of the peak than np.mean
        xs = np.arange(len(self.profile_array)) * self.pixel_size
        self.popt, _ = curve_fit(
            gaussian_fit,
            xs,
            self.profile_array,
            p0=[np.max(self.profile_array), np.argmax(self.profile_array) * self.pixel_size, self.pixel_size])

    TomographicResolutionAxisData.__post_init__ = new_post_init


patch_tomo_res_axis_data()

from pylinac.nuclear import (
    Nuclide,
    MaxCountRate,
    SimpleSensitivity,
    PlanarUniformity,
    FourBarResolution,
    QuadrantResolution,
    TomographicUniformity,
    TomographicResolution,
    TomographicContrast,
    CenterOfRotation,
    contrast_f,
    TomographicROI,
    get_fov)
from pylinac.core import pdf
from pylinac.core.contrast import michelson



class LinaQAMaxCountRate(MaxCountRate):
    _model = "Maximum Count Rate"

    def __init__(self, path: str | Path | list[Dataset]) -> None:
        self.stack = NMImageStack(path)

    def publish_pdf(
        self,
        filename: str | Path,
        notes: str | None = None,
        metadata: dict | None = None,
        logo: Path | str | None = None,
        ) -> None:
        """Publish (print) a PDF containing the analysis and quantitative results.

        Parameters
        ----------
        filename : (str, file-like object}
            The file to write the results to.
        notes : str, list of strings
            Text; if str, prints single line.
            If list of strings, each list item is printed on its own line.
        metadata : dict
            Extra data to be passed and shown in the PDF. The key and value will be shown with a colon.
            E.g. passing {'Author': 'Joe Soap', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: Joe Soap
            Unit: TrueBeam
            --------------
        logo: Path, str
            A custom logo to use in the PDF report. If nothing is passed, the default pylinac logo is used.
        """
        analysis_title = f"{self._model} Analysis"
        results_text = self.results().splitlines()
        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)

        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 22-idx*0.5))

        analysis_images = io.BytesIO()
        plt.clf()
        self.plot(show=False)
        plt.savefig(analysis_images)
        canvas.add_image(analysis_images, location=(1, 3), dimensions=(18, 18))

        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))
        canvas.finish()


class LinaQASimpleSensitivity(SimpleSensitivity):
    _model = "Simple Sensitivity"
    phantom_img = None
    background_img = None

    def __init__(
        self,
        phantom_path: str | Path | Dataset,
        background_path: str | Path | Dataset | None = None):
        # redefine init to take a dataset

        if isinstance(phantom_path, Dataset):
            self.phantom_path = Path(phantom_path.filename)
            self.phantom_img = DicomImage.from_dataset(phantom_path)
        else:
            self.phantom_path = Path(phantom_path)
            self.phantom_img = DicomImage(phantom_path)

        if isinstance(background_path, Dataset):
            self.background_path = Path(background_path.filename)
            self.background_img = DicomImage.from_dataset(background_path)
        elif background_path is not None:
            self.background_path = Path(background_path)
            self.background_img = DicomImage(background_path)
        else:
            self.background_path = None

    @property
    def phantom_cps(self) -> float:
        """The counts per second of the phantom."""
        # phantom_img = DicomImage(self.phantom_path, raw_pixels=True)
        counts = self.phantom_img.array.sum()
        return counts / self.duration_s

    @property
    def duration_s(self) -> float:
        """The duration of the phantom image."""
        # phantom_img = DicomImage(self.phantom_path, raw_pixels=True)
        return self.phantom_img.metadata.ActualFrameDuration / 1000

    @property
    def background_cps(self) -> float:
        """The counts per second of the background."""
        # TODO this appears to sum both frames, handle frames apart
        if self.background_path is None:
            return 0
        else:
            # background_stack = NMImageStack(self.background_path)
            duration_s = self.background_img.metadata.ActualFrameDuration / 1000
            # mean background
            counts = self.background_img.array.sum()
            return counts / duration_s

    def publish_pdf(
        self,
        filename: str | Path,
        notes: str | None = None,
        metadata: dict | None = None,
        logo: Path | str | None = None,
        ) -> None:
        """Publish (print) a PDF containing the analysis and quantitative results.

        Parameters
        ----------
        filename : (str, file-like object}
            The file to write the results to.
        notes : str, list of strings
            Text; if str, prints single line.
            If list of strings, each list item is printed on its own line.
        metadata : dict
            Extra data to be passed and shown in the PDF. The key and value will be shown with a colon.
            E.g. passing {'Author': 'Joe Soap', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: Joe Soap
            Unit: TrueBeam
            --------------
        logo: Path, str
            A custom logo to use in the PDF report. If nothing is passed, the default pylinac logo is used.
        """
        analysis_title = f"{self._model} Analysis"
        results_text = self.results().splitlines()
        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)

        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 23-idx*0.5))

        analysis_image = io.BytesIO()
        plt.clf()
        plt.imshow(self.phantom_img.array, cmap='gray')
        plt.title(os.path.basename(self.phantom_path))
        plt.savefig(analysis_image)
        canvas.add_image(analysis_image, location=(1, 3), dimensions=(18, 18))

        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))
        canvas.finish()


class LinaQAPlanarUniformity(PlanarUniformity):
    _model = "Planar Uniformity"

    def __init__(self, path: str | Path | list[Dataset]) -> None:
        self.stack = NMImageStack(path)
        # self.path = Path(path)

    def publish_pdf(
        self,
        filename: str | Path,
        notes: str | None = None,
        metadata: dict | None = None,
        logo: Path | str | None = None,
        ) -> None:
        """Publish (print) a PDF containing the analysis and quantitative results.

        Parameters
        ----------
        filename : (str, file-like object}
            The file to write the results to.
        notes : str, list of strings
            Text; if str, prints single line.
            If list of strings, each list item is printed on its own line.
        metadata : dict
            Extra data to be passed and shown in the PDF. The key and value will be shown with a colon.
            E.g. passing {'Author': 'Joe Soap', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: Joe Soap
            Unit: TrueBeam
            --------------
        logo: Path, str
            A custom logo to use in the PDF report. If nothing is passed, the default pylinac logo is used.
        """
        analysis_title = f"{self._model} Analysis"
        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)
        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        plt.clf()
        figs, axs = self.plot(show=False)
        for key, result in self.frame_results.items():
            if key != "1":
                canvas.add_new_page()
            canvas.add_text(
                text=f"Frame {key}: ",
                location=(2.0, 22.0))
            canvas.add_text(
                text=f"UFOV integral uniformity: {result['ufov'].integral_uniformity: .2f}%",
                location=(2.0, 21.5))
            canvas.add_text(
                text=f"UFOV differential uniformity {result['ufov'].differential_uniformity: .2f}%",
                location=(2.0, 21.0))
            canvas.add_text(
                text=f"CFOV integral uniformity: {result['cfov'].integral_uniformity: .2f}%",
                location=(2.0, 20.5))
            canvas.add_text(
                text=f"CFOV differential uniformity {result['cfov'].differential_uniformity: .2f}%",
                location=(2.0, 20.0))

            axs[int(key) - 1].legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
            figs[int(key) - 1].tight_layout()
            analysis_image = io.BytesIO()
            figs[int(key) - 1].savefig(analysis_image, bbox_inches='tight')
            canvas.add_image(analysis_image, location=(1, 3), dimensions=(18, 18))
        canvas.finish()


class LinaQAFourBarRes(FourBarResolution):
    _model = "Four Bar Spatial Resolution"

    def __init__(self, path: str | Path | list[Dataset]) -> None:
        self.stack = NMImageStack(path)
        if isinstance(path[0], Dataset):
            self.path = Path(path[0].filename)
        else:
            self.path = Path(path)

    def publish_pdf(
        self,
        filename: str | Path,
        notes: str | None = None,
        metadata: dict | None = None,
        logo: Path | str | None = None,
        ) -> None:
        """Publish (print) a PDF containing the analysis and quantitative results.

        Parameters
        ----------
        filename : (str, file-like object}
            The file to write the results to.
        notes : str, list of strings
            Text; if str, prints single line.
            If list of strings, each list item is printed on its own line.
        metadata : dict
            Extra data to be passed and shown in the PDF. The key and value will be shown with a colon.
            E.g. passing {'Author': 'Joe Soap', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: Joe Soap
            Unit: TrueBeam
            --------------
        logo: Path, str
            A custom logo to use in the PDF report. If nothing is passed, the default pylinac logo is used.
        """
        analysis_title = f"{self._model} Analysis"
        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)

        results_text = self.results().splitlines()
        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 22 - idx * 0.5))

        plt.clf()
        figs, axs = self.plot(show=False)
        analysis_image = io.BytesIO()
        figs[0].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 3), dimensions=(15, 15), preserve_aspect_ratio=True)

        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        canvas.add_new_page()
        axs[1].legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        figs[1].tight_layout()
        analysis_image = io.BytesIO()
        figs[1].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 13), dimensions=(15, 15), preserve_aspect_ratio=True)

        axs[2].legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        figs[2].tight_layout()
        analysis_image = io.BytesIO()
        figs[2].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 0), dimensions=(15, 15), preserve_aspect_ratio=True)
        canvas.finish()


class LinaQAQuadrantRes(QuadrantResolution):
    _model = "Quadrant Resolution"

    def __init__(self, path: str | Path | list[Dataset]) -> None:
        self.stack = NMImageStack(path)
        if isinstance(path[0], Dataset):
            self.path = Path(path[0].filename)
        else:
            self.path = Path(path)

    def publish_pdf(
        self,
        filename: str | Path,
        notes: str | None = None,
        metadata: dict | None = None,
        logo: Path | str | None = None,
        ) -> None:
        """Publish (print) a PDF containing the analysis and quantitative results.

        Parameters
        ----------
        filename : (str, file-like object}
            The file to write the results to.
        notes : str, list of strings
            Text; if str, prints single line.
            If list of strings, each list item is printed on its own line.
        metadata : dict
            Extra data to be passed and shown in the PDF. The key and value will be shown with a colon.
            E.g. passing {'Author': 'Joe Soap', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: Joe Soap
            Unit: TrueBeam
            --------------
        logo: Path, str
            A custom logo to use in the PDF report. If nothing is passed, the default pylinac logo is used.
        """
        analysis_title = f"{self._model} Analysis"
        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)

        results_text = self.results().splitlines()
        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 22 - idx * 0.5))

        plt.clf()
        figs, axs = self.plot(show=False)
        analysis_image = io.BytesIO()
        figs[0].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 3), dimensions=(15, 15), preserve_aspect_ratio=True)

        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        canvas.add_new_page()
        analysis_image = io.BytesIO()
        figs[1].savefig(analysis_image)
        canvas.add_image(analysis_image, location=(1, 13), dimensions=(15, 15), preserve_aspect_ratio=True)

        analysis_image = io.BytesIO()
        figs[2].savefig(analysis_image)
        canvas.add_image(analysis_image, location=(1, 0), dimensions=(15, 15), preserve_aspect_ratio=True)
        canvas.finish()


class LinaQATomoUniformity(TomographicUniformity):
    _model = "Tomographic Uniformity"

    mean_value: float

    def __init__(self, path: str | Path | list[Dataset], raw_pixels: bool) -> None:
        self.stack = NMImageStack(path, raw_pixels)
        if isinstance(path[0], Dataset):
            self.path = Path(path[0].filename)
        else:
            self.path = Path(path)

    def center_mean_value(self, center_ratio: float) -> float:
        """The center mean value.

        The center ROI is a 6cm diameter circle in the center of the phantom.
        """
        array = np.copy(self.stack.frames[0].array)
        # remove pixels that are <75% of mean of "meaningful" pixels
        # meaningful pixels are those > 10% of max
        # this helps remove the background
        threshold = array[array > np.max(array) * 0.10].mean() * self.threshold
        array[array < threshold] = 0
        center_array, center_x, center_y = get_fov(array, size=center_ratio)
        center_array[center_array == 0] = np.nan
        return np.nanmean(center_array)

    def analyze(
        self,
        first_frame: int = 0,
        last_frame: int = -1,
        ufov_ratio: float = 0.8,
        cfov_ratio: float = 0.75,
        center_ratio: float = 0.4,
        threshold: float = 0.75,
        window_size: int = 5,
        ) -> None:
        """Analyze the image to determine the uniformity.
        This will take a mean of pixel values for frames between the first and last stated frame.

        Parameters
        ----------
        first_frame : int
            The index of the first frame to analyze.
        last_frame : int
            The index of the last frame to analyze.
        ufov_ratio : float
            The ratio of the UFOV to the phantom.
        cfov_ratio : float
            The ratio of the central FOV to the UFOV.
        center_ratio : float
            The ratio of the center ROI to the phantom.
        threshold : float
            The threshold to use for the image.
        window_size : int
            Number of pixels for differential uniformity
        """
        super().analyze(first_frame, last_frame, ufov_ratio, cfov_ratio, center_ratio, threshold, window_size)
        self.mean_value = self.center_mean_value(center_ratio)

    def results(self) -> str:
        """Return a string representation of the results."""
        return (
            f"Tomographic Uniformity results for {self.path.name}\n"
            f"Frames: {self.first_frame}:{self.last_frame}\n"
            f"CFOV Integral Uniformity: {self.frame_result['cfov'].integral_uniformity:.3f}%\n"
            f"CFOV Differential Uniformity: {self.frame_result['cfov'].differential_uniformity:.3f}%\n"
            f"UFOV Integral Uniformity: {self.frame_result['ufov'].integral_uniformity:.3f}%\n"
            f"UFOV Differential Uniformity: {self.frame_result['ufov'].differential_uniformity:.3f}%\n"
            f"Center-to-Border ratio: {self.center_ratio:.3f}\n"
            f"CFOV Mean Value: {self.mean_value:.3f}"
        )

    def publish_pdf(
        self,
        filename: str | Path,
        notes: str | None = None,
        metadata: dict | None = None,
        logo: Path | str | None = None,
        ) -> None:
        """Publish (print) a PDF containing the analysis and quantitative results.

        Parameters
        ----------
        filename : (str, file-like object}
            The file to write the results to.
        notes : str, list of strings
            Text; if str, prints single line.
            If list of strings, each list item is printed on its own line.
        metadata : dict
            Extra data to be passed and shown in the PDF. The key and value will be shown with a colon.
            E.g. passing {'Author': 'Joe Soap', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: Joe Soap
            Unit: TrueBeam
            --------------
        logo: Path, str
            A custom logo to use in the PDF report. If nothing is passed, the default pylinac logo is used.
        """
        analysis_title = f"{self._model} Analysis"
        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)

        results_text = self.results().splitlines()
        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 22-idx*0.5))

        analysis_images = io.BytesIO()
        plt.clf()
        self.plot(show=False)
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        plt.tight_layout()
        plt.savefig(analysis_images, bbox_inches='tight')
        canvas.add_image(analysis_images, location=(1, 3), dimensions=(18, 18))

        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))
        canvas.finish()


class LinaQATomoResolution(TomographicResolution):
    _model = "Tomographic Resolution"

    def __init__(self, path: str | Path | list[Dataset], raw_pixels: bool = False) -> None:
        self.stack = NMImageStack(path, raw_pixels)
        if isinstance(path[0], Dataset):
            self.path = Path(path[0].filename)
        else:
            self.path = Path(path)

    def publish_pdf(
        self,
        filename: str | Path,
        notes: str | None = None,
        metadata: dict | None = None,
        logo: Path | str | None = None,
        ) -> None:
        """Publish (print) a PDF containing the analysis and quantitative results.

        Parameters
        ----------
        filename : (str, file-like object}
            The file to write the results to.
        notes : str, list of strings
            Text; if str, prints single line.
            If list of strings, each list item is printed on its own line.
        metadata : dict
            Extra data to be passed and shown in the PDF. The key and value will be shown with a colon.
            E.g. passing {'Author': 'Joe Soap', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: Joe Soap
            Unit: TrueBeam
            --------------
        logo: Path, str
            A custom logo to use in the PDF report. If nothing is passed, the default pylinac logo is used.
        """
        analysis_title = f"{self._model} Analysis"
        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)
        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        results_text = self.results().splitlines()
        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 22-idx*0.5))

        plt.clf()
        figs, axs = self.plot()
        axs[0].legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        figs[0].tight_layout()
        analysis_image = io.BytesIO()
        figs[0].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 3), dimensions=(15, 15), preserve_aspect_ratio=True)

        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        canvas.add_new_page()
        axs[1].legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        figs[1].tight_layout()
        analysis_image = io.BytesIO()
        figs[1].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 13), dimensions=(15, 15), preserve_aspect_ratio=True)

        axs[2].legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        figs[2].tight_layout()
        analysis_image = io.BytesIO()
        figs[2].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 0), dimensions=(15, 15), preserve_aspect_ratio=True)

        canvas.finish()


class LinaQACenterOfRotation(CenterOfRotation):
    _model = "Centre of Rotation"

    def __init__(self, path: str | Path | list[Dataset]) -> None:
        self.stack = NMImageStack(path)
        if isinstance(path[0], Dataset):
            self.path = Path(path[0].filename)
        else:
            self.path = Path(path)

    def publish_pdf(
        self,
        filename: str | Path,
        notes: str | None = None,
        metadata: dict | None = None,
        logo: Path | str | None = None,
        ) -> None:
        """Publish (print) a PDF containing the analysis and quantitative results.

        Parameters
        ----------
        filename : (str, file-like object}
            The file to write the results to.
        notes : str, list of strings
            Text; if str, prints single line.
            If list of strings, each list item is printed on its own line.
        metadata : dict
            Extra data to be passed and shown in the PDF. The key and value will be shown with a colon.
            E.g. passing {'Author': 'Joe Soap', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: Joe Soap
            Unit: TrueBeam
            --------------
        logo: Path, str
            A custom logo to use in the PDF report. If nothing is passed, the default pylinac logo is used.
        """
        analysis_title = f"{self._model} Analysis"
        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)

        results_text = self.results().splitlines()
        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 22-idx*0.5))

        plt.clf()
        figs, axs = self.plot(show=False)
        axs[0].legend(bbox_to_anchor=(0, -0.3), loc='upper left', borderaxespad=0)
        figs[0].tight_layout()
        analysis_image = io.BytesIO()
        figs[0].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 3), dimensions=(18, 18), preserve_aspect_ratio=True)

        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        canvas.add_new_page()
        analysis_image = io.BytesIO()
        figs[1].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 12.5), dimensions=(15, 15), preserve_aspect_ratio=True)

        analysis_image = io.BytesIO()
        figs[2].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 0), dimensions=(15, 15), preserve_aspect_ratio=True)

        canvas.finish()


class LinaQATomoContrast(TomographicContrast):
    _model = "Tomographic Contrast"

    def __init__(self, path: str | Path | list[Dataset]) -> None:
        self.stack = NMImageStack(path)
        if isinstance(path[0], Dataset):
            self.path = Path(path[0].filename)
        else:
            self.path = Path(path)

    def publish_pdf(
        self,
        filename: str | Path,
        notes: str | None = None,
        metadata: dict | None = None,
        logo: Path | str | None = None,
        ) -> None:
        """Publish (print) a PDF containing the analysis and quantitative results.

        Parameters
        ----------
        filename : (str, file-like object}
            The file to write the results to.
        notes : str, list of strings
            Text; if str, prints single line.
            If list of strings, each list item is printed on its own line.
        metadata : dict
            Extra data to be passed and shown in the PDF. The key and value will be shown with a colon.
            E.g. passing {'Author': 'Joe Soap', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: Joe Soap
            Unit: TrueBeam
            --------------
        logo: Path, str
            A custom logo to use in the PDF report. If nothing is passed, the default pylinac logo is used.
        """
        analysis_title = f"{self._model} Analysis"
        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)
        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        results_text = self.results().splitlines()
        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 22-idx*0.5))

        plt.clf()
        figs, axs = self.plot(show=False)
        # makes more sense to display the contrast graphs first
        axs[2].legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        figs[2].tight_layout()
        analysis_image = io.BytesIO()
        figs[2].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 3), dimensions=(15, 15), preserve_aspect_ratio=True)

        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        canvas.add_new_page()
        analysis_image = io.BytesIO()
        figs[0].savefig(analysis_image)
        canvas.add_image(analysis_image, location=(1, 13), dimensions=(15, 15), preserve_aspect_ratio=True)

        analysis_image = io.BytesIO()
        figs[1].savefig(analysis_image)
        canvas.add_image(analysis_image, location=(1, 0), dimensions=(15, 15), preserve_aspect_ratio=True)

        canvas.finish()


class SUVTomoROI(TomographicROI):
    # Original TomographicROI was defined for "cold" spheres with no activity.
    # We must add functionality for "hot" spheres with activity
    @property
    def max_value(self) -> float:
        return float(np.nanmax(self.sphere_array))

    @property
    def max_hot_contrast(self) -> float:
        return michelson(np.asarray([self.max_value, self.uniformity_baseline])) * 100


class SUVUptake:
    """Use the methods detailed here for SUV calculation
    https://qibawiki.rsna.org/index.php/Standardized_Uptake_Value_(SUV)"""
    _model = "EARL Contrast"

    def __init__(self, path: str | Path | list[Dataset]) -> None:
        self.stack = NMImageStack(path)
        self.scaled_3d_array = self.stack.as_3d_array()
        if isinstance(path[0], Dataset):
            self.path = Path(path[0].filename)
        else:
            self.path = Path(path)

    @cached_property
    def sphere_slice_index(self):
        images_max = self.scaled_3d_array.max(axis=(1, 2))
        return images_max.argmax()  # assume peak is brightest sphere

    @cached_property
    def sphere_slice(self):
        # get slice with spheres
        return self.scaled_3d_array[self.sphere_slice_index, :, :]

    @cached_property
    def binary_slice(self):
        # return thresholded slice
        slice_ave = np.mean(self.sphere_slice)
        return self.sphere_slice > slice_ave

    @cached_property
    def phantom_center(self):
        # get centre of phantom
        return center_of_mass(self.binary_slice)

    @cached_property
    def phantom_radius(self):
        return math.sqrt(np.sum(self.binary_slice) / math.pi)

    @cached_property
    def backgnd_roi(self):
        mask_outer = isotropic_erosion(self.binary_slice, radius=int(15/self.stack.metadata.PixelSpacing[0]))
        mask_inner = isotropic_erosion(self.binary_slice, radius=int(45/self.stack.metadata.PixelSpacing[0]))
        return mask_outer ^ mask_inner

    @cached_property
    def backgnd(self) -> dict[str, float]:
        # return mean background value and standard deviation in a 3cm band 1.5 cm in from rim of phantom
        # for slices +/- 2 cm around sphere slice
        start_index = int(self.sphere_slice_index - 20/self.stack.metadata.SpacingBetweenSlices)
        stop_index = int(self.sphere_slice_index + 20/self.stack.metadata.SpacingBetweenSlices)
        backgnd_slices = self.scaled_3d_array[start_index: stop_index, :, :]
        return {'mean': backgnd_slices[:, self.backgnd_roi].mean(),
                'stddev': backgnd_slices[:, self.backgnd_roi].std()}

    def analyze(
        self,
        sphere_diameters_mm: Sequence[float] = (37.0, 28.0, 22.0, 17.0, 13.0, 10.0),
        sphere_angles: Sequence[float] = (120, 60, 0, -60, -120, -180),
        ufov_ratio: float = 0.8,
        search_window_px: int = 5,
        search_slices: int = 3,
    ) -> None:
        """Analyze the image to determine the contrast.

        Parameters
        ----------
        sphere_diameters_mm : list
            The diameters of the spheres in mm.
        sphere_angles : list
            The angles of the spheres in degrees.
        ufov_ratio: float = 0.8
            Ratio of the useful field of view to the phantom size
        search_window_px: int = 5
            Number of pixels to search around the estimated centre
        search_slices: int = 3
            Number of slices to search around the sphere slice
        """
        if len(sphere_diameters_mm) != len(sphere_angles):
            raise ValueError(
                "The number of sphere diameters and angles must be the same."
            )

        # get radius to ring of spheres
        sphere_radius = self.phantom_radius * 0.434
        # can also use
        # sphere_radius = 11.4/(2*self.stack.metadata.PixelSpacing[0])

        rois = {}
        for idx, (angle, diameter) in enumerate(zip(sphere_angles, sphere_diameters_mm)):
            radius = diameter / (2 * self.stack.metadata.PixelSpacing[0])
            col_x, row_y = direction_to_coords(self.phantom_center[1], self.phantom_center[0], sphere_radius, angle)
            # quicker but less accurate at the smallest ROIs
            res = minimize(
                contrast_f,
                x0=(col_x, row_y, self.sphere_slice_index),
                args=(self.scaled_3d_array, radius, self.backgnd['mean']),
                method="Nelder-Mead",
                bounds=[
                    (col_x - search_window_px, col_x + search_window_px),
                    (row_y - search_window_px, row_y + search_window_px),
                    (self.sphere_slice_index - search_slices, self.sphere_slice_index + search_slices),
                ],
            )
            # alternatives left for future potential work
            # res = brute(contrast_f, ranges=[(col_x - search_window_px, col_x + search_window_px), (row_y - search_window_px, row_y + search_window_px), (unif_z - search_slices, unif_z + search_slices)], args=(array3d, radius, self.uniformity_value), Ns=search_window_px*2, full_output=False, finish=None)
            # res = differential_evolution(contrast_f, bounds=[(col_x - search_window_px, col_x + search_window_px), (row_y - search_window_px, row_y + search_window_px), (unif_z - search_slices, unif_z + search_slices)], args=(array3d, radius, self.uniformity_value), polish=False, x0=(col_x, row_y, unif_z), seed=1234)
            col, row, zed = res.x
            roi = SUVTomoROI(
                array3d=self.scaled_3d_array,
                x=col,
                y=row,
                z=zed,
                radius=radius,
                uniformity_baseline=self.backgnd['mean'],
                number=idx + 1,
            )
            rois[str(idx + 1)] = roi
        self.rois = rois

    def results(self) -> str:
        """Return a string representation of the results."""
        s = f"Tomographic Contrast results for {self.path.name}\n"
        s += f"Background baseline: {self.backgnd['mean']:.1f}\n"
        for idx, roi in self.rois.items():
            s += (f"Sphere {idx}: X={roi.x:.2f}, Y={roi.y:.2f}, Z={roi.z:.2f} Mean: {roi.mean_value:.2f}; " +
                  f"Mean Contrast: {roi.mean_contrast:.2f}; Max Contrast: {roi.max_hot_contrast:.2f}\n")
        return s

    def plot(self, show: bool = True) -> (list[Figure], list[Axes]):
        """Plot the uniformity frame, sphere ROI frame, and contrast vs sphere number."""
        # plot the ROIs
        roi_fig, roi_ax = plt.subplots()
        # show all ROIs on the most common sphere slice for simplicity
        median_slice = int(round(np.median([roi.z for roi in self.rois.values()])))
        roi_ax.imshow(self.stack.frames[median_slice].array, cmap="gray")
        for roi in self.rois.values():
            roi.plot_to(roi_ax)
        roi_ax.set_title(f"Sphere frame ({median_slice+1})")

        # plot the uniformity ROI
        color_map = colors.ListedColormap(['none', 'blue'])
        roi_ax.imshow(self.backgnd_roi, cmap=color_map, alpha=0.3)

        # plot the contrast vs sphere number
        cont_fig, cont_ax = plt.subplots()
        cont_ax.plot(
            [int(idx) for idx in self.rois.keys()],
            [roi.mean_contrast for roi in self.rois.values()],
            color="b",
            marker="o",
            label="Mean Contrast",
        )
        cont_ax.plot(
            [int(idx) for idx in self.rois.keys()],
            [roi.max_hot_contrast for roi in self.rois.values()],
            color="r",
            marker="o",
            label="Max Contrast",
        )
        cont_ax.set_xlabel("Sphere Number")
        cont_ax.set_ylabel("Contrast (Michelson * 100)")
        cont_ax.legend()
        cont_ax.grid(True)
        cont_ax.set_title("Contrast vs Sphere Number")
        if show:
            plt.show()
        return (roi_fig, cont_fig), (roi_ax, cont_ax)

    def publish_pdf(
        self,
        filename: str | Path,
        notes: str | None = None,
        metadata: dict | None = None,
        logo: Path | str | None = None
        ) -> None:
        """Publish (print) a PDF containing the analysis and quantitative results.

        Parameters
        ----------
        filename : (str, file-like object}
            The file to write the results to.
        notes : str, list of strings
            Text; if str, prints single line.
            If list of strings, each list item is printed on its own line.
        metadata : dict
            Extra data to be passed and shown in the PDF. The key and value will be shown with a colon.
            E.g. passing {'Author': 'Joe Soap', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: Joe Soap
            Unit: TrueBeam
            --------------
        logo: Path, str
            A custom logo to use in the PDF report. If nothing is passed, the default pylinac logo is used.
        """
        analysis_title = f"{self._model} Analysis"
        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)
        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        results_text = self.results().splitlines()
        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 22-idx*0.5))

        plt.clf()
        figs, axs = self.plot(show=False)
        # makes more sense to display the contrast graphs first
        axs[1].legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        figs[1].tight_layout()
        analysis_image = io.BytesIO()
        figs[1].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 3), dimensions=(15, 15), preserve_aspect_ratio=True)

        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        canvas.add_new_page()
        analysis_image = io.BytesIO()
        figs[0].savefig(analysis_image)
        canvas.add_image(analysis_image, location=(1, 13), dimensions=(15, 15), preserve_aspect_ratio=True)
        canvas.finish()
