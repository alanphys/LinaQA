"""
=========================================================================
Extra functionality for pylinac classes. Merge into pylinac at some stage
=========================================================================
"""
# Author: AC Chamberlain

import io
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
                    raise TypeError('The file is not a NM or PET aaimage')
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

from pylinac.nuclear import MaxCountRate, PlanarUniformity, TomographicUniformity, TomographicResolution
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
        analysis_images = io.BytesIO()
        self.plot(show=False)
        plt.savefig(analysis_images)
        results_text = self.results().splitlines()

        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)
        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 22-idx*0.5))
        canvas.add_image(analysis_images, location=(1, 3), dimensions=(18, 18))
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
        analysis_images = io.BytesIO()
        self.plot(show=False)
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        plt.tight_layout()
        plt.savefig(analysis_images, bbox_inches='tight')
        results_text = self.results().splitlines()

        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)
        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 22-idx*0.5))
        canvas.add_image(analysis_images, location=(1, 3), dimensions=(18, 18))
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
        results_text = self.results().splitlines()

        canvas = pdf.PylinacCanvas(filename, page_title=analysis_title, metadata=metadata, logo=logo)
        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 2.5), font_size=12)
            canvas.add_text(text=notes, location=(1, 2))

        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 22-idx*0.5))

        figs, axs = self.plot()
        axs[0].legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        figs[0].tight_layout()
        analysis_image = io.BytesIO()
        figs[0].savefig(analysis_image, bbox_inches='tight')
        canvas.add_image(analysis_image, location=(1, 3), dimensions=(15, 15), preserve_aspect_ratio=True)

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