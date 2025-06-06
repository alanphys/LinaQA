"""
=========================================================================
Extra functionality for pylinac classes. Merge into pylinac at some stage
=========================================================================
"""
import io
# Author: AC Chamberlain

import textwrap
from pathlib import Path
from matplotlib import pyplot as plt
from pylinac.nuclear import MaxCountRate, PlanarUniformity
from pylinac.core import pdf

class MyMaxCountRate(MaxCountRate):
    _model = "Maximum Count Rate"

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
            canvas.add_text(text="Notes:", location=(1, 4.5), font_size=14)
            canvas.add_text(text=notes, location=(1, 4))

        for idx, text in enumerate(results_text):
            canvas.add_text(text=text, location=(2.0, 22-idx*0.5))
        canvas.add_image(analysis_images, location=(1, 5), dimensions=(18, 18))
        canvas.finish()


class MyPlanarUniformity(PlanarUniformity):
    _model = "Planar Uniformity"

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
            canvas.add_text(text="Notes:", location=(1, 4.5), font_size=14)
            canvas.add_text(text=notes, location=(1, 4))

        figs, axs = self.plot(show=False)
        for key, result in self.frame_results.items():
            if key != "1":
                canvas.add_new_page()
            canvas.add_text(
                text=f"Frame {key}:",
                location=(2.0, 22.0))
            canvas.add_text(
                text=f"UFOV integral uniformity: {result['ufov'].integral_uniformity:.2f}%",
                location=(2.0, 21.5))
            canvas.add_text(
                text=f"UFOV differential uniformity {result['ufov'].differential_uniformity:.2f}%",
                location=(2.0, 21.0))
            canvas.add_text(
                text=f"CFOV integral uniformity: {result['cfov'].integral_uniformity:.2f}%",
                location=(2.0, 20.5))
            canvas.add_text(
                text=f"CFOV differential uniformity {result['cfov'].differential_uniformity:.2f}%",
                location=(2.0, 20.0))

            analysis_image = io.BytesIO()
            figs[int(key) - 1].savefig(analysis_image)
            canvas.add_image(analysis_image, location=(1, 4), dimensions=(18, 18))
        canvas.finish()