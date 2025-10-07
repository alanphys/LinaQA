"""
=========================================================================
Extra functionality for pylinac classes. Merge into pylinac at some stage
=========================================================================
"""
import enum
# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2025
# SPDX-License-Identifier: Licence.txt:

import io
import os
import textwrap
from pathlib import Path
from matplotlib import pyplot as plt
from pydicom import Dataset

# We need to monkey patch NMImageStack to accept a dataset. This is bad practice, very bad, but the only
# workaround I have at the moment.
from pylinac.core.image import DicomImage, NMImageStack
import functools


def patch_nm_image_stack():
    original_init = NMImageStack.__init__

    @functools.wraps(original_init)
    def enhanced_init(self, path: str | Path | list[Dataset]):
        if isinstance(path[0], Dataset):
            self.path = path
            self.metadata = path[0]
            self.frames = []
            for ds in path:
                if ds.Modality not in ['NM', 'PT']:
                    raise TypeError('The file is not a NM or PET image')
                full_array = ds.pixel_array
                # we may have a single dataset with multiple frames
                if hasattr(ds, 'NumberOfFrames') and (ds.NumberOfFrames > 1):
                    for i in range(ds.NumberOfFrames):
                        array = full_array[i]
                        img = DicomImage.from_dataset(ds)
                        img.array = array
                        self.frames.append(img)
                # or we may have multiple images with one frame
                else:
                    img = DicomImage.from_dataset(ds)
                    img.array = full_array
                    self.frames.append(img)
        else:
            original_init(self, path)

    NMImageStack.__init__ = enhanced_init


# apply the patch
patch_nm_image_stack()

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
    CenterOfRotation)
from pylinac.core import pdf


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
            E.g. passing {'Author': 'James', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: James
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
            E.g. passing {'Author': 'James', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: James
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
            E.g. passing {'Author': 'James', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: James
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
            E.g. passing {'Author': 'James', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: James
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
            E.g. passing {'Author': 'James', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: James
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
            E.g. passing {'Author': 'James', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: James
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
            E.g. passing {'Author': 'James', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: James
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
            E.g. passing {'Author': 'James', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: James
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
            E.g. passing {'Author': 'James', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: James
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
