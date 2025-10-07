# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2025
# SPDX-License-Identifier: Licence.txt:

import math

import numpy as np
from linaqa_types import supported_modalities


class Imager:
    def __init__(self, datasets):
        self.datasets = datasets
        self._index = 0

        # check if dataset has an image
        if (datasets[0].Modality in supported_modalities) and hasattr(datasets[0], 'PixelData'):
            self._window_width = 1000
            self._window_center = 0
            self._invflag = False

            # Dataset has 3D volume
            if hasattr(datasets[0], "NumberOfFrames") and (int(datasets[0].NumberOfFrames) > 1):
                self.size = (int(datasets[0].Rows), int(datasets[0].Columns), int(datasets[0].NumberOfFrames))
            # Datasets have 2D planes
            else:
                self.size = (int(datasets[0].Rows), int(datasets[0].Columns), len(datasets))

            # CT 3D dataset
            if (hasattr(datasets[0], "PixelSpacing") and
               hasattr(datasets[0], "SliceThickness") and
               (datasets[0].SliceThickness is not None) and
               (datasets[0].SliceThickness != '')):
                self.spacings = (float(datasets[0].PixelSpacing[0]),
                                 float(datasets[0].PixelSpacing[1]),
                                 float(datasets[0].SliceThickness))
            # 2D dataset
            elif hasattr(datasets[0], "ImagePlanePixelSpacing"):
                self.spacings = (float(datasets[0].ImagePlanePixelSpacing[0]),
                                 float(datasets[0].ImagePlanePixelSpacing[1]),
                                 float(1))
            else:
                self.spacings = (1, 1, 1)

            self._index = int(self.size[2]/2)

            self.axes = (np.arange(0.0, (self.size[0] + 1) * self.spacings[0], self.spacings[0]),
                         np.arange(0.0, (self.size[1] + 1) * self.spacings[1], self.spacings[1]),
                         np.arange(0.0, (self.size[2] + 1) * self.spacings[2], self.spacings[2]))

            # Load pixel data
            self.load_pixel_data(datasets)
            self.auto_window()

    def load_pixel_data(self, datasets):
        # standard set of 2D images
        if datasets[0].pixel_array.ndim == 2:
            self.values = np.zeros(self.size, dtype='int32')
            for i, d in enumerate(datasets):
                # Also performs rescaling. 'unsafe' since it converts from float64 to int32
                np.copyto(self.values[:, :, i], d.pixel_array, 'unsafe')
        # colour image 3 sample RGB per pixel
        elif (datasets[0].pixel_array.ndim == 3) and (hasattr(datasets[0], "SamplesPerPixel")) and (datasets[0].SamplesPerPixel == 3):
            self.values = np.zeros((self.size[0], self.size[1], len(datasets)), dtype='int32')
            for i, d in enumerate(datasets):
                # Convert RBG image to Grayscale
                np.copyto(self.values[:, :, i], np.dot(d.pixel_array[...,:3], [0.2989, 0.5870, 0.1140]), 'unsafe')
        # multi-frame image or 3D image
        elif datasets[0].pixel_array.ndim == 3:
            self.values = datasets[0].pixel_array.transpose(1, 2, 0)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        if value < 0:
            value = 0
        if value >= self.size[2]:
            value = self.size[2] - 1
        self._index = value

    @property
    def window_width(self):
        return self._window_width

    @window_width.setter
    def window_width(self, value):
        self._window_width = max(value, 1)

    @property
    def window_center(self):
        return self._window_center

    @window_center.setter
    def window_center(self, value):
        self._window_center = value

    @property
    def invflag(self):
        return self._invflag

    @invflag.setter
    def invflag(self, value: bool):
        self._invflag = value

    def get_image(self, index):
        if hasattr(self, "values") and self.values is not None:
            # int32 true values (HU or brightness units)
            img = self.values[:, :, index]

            # Vectorized windowing using boolean masks
            w_left = (self._window_center - self._window_width / 2)
            w_right = (self._window_center + self._window_width / 2)
            mask_0 = img < w_left
            mask_1 = img > w_right
            mask_2 = np.invert(mask_0 + mask_1)

            # Cast to RGB image so that QImage can handle it
            rgb_array = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint32)
            if self._invflag:
                rgb_array[:, :, 0] = rgb_array[:, :, 1] = rgb_array[:, :, 2] = \
                    mask_1 * 0 + mask_0 * 255 + mask_2 * (255 * (w_right - img) / (w_right - w_left))
            else:
                rgb_array[:, :, 0] = rgb_array[:, :, 1] = rgb_array[:, :, 2] = \
                    mask_0 * 0 + mask_1 * 255 + mask_2 * (255 * (img - w_left) / (w_right - w_left))

            # flatten RGB array to RGB32
            res = (255 << 24 | rgb_array[:, :, 0] << 16 | rgb_array[:, :, 1] << 8 | rgb_array[:, :, 2])
            return res

    def get_current_image(self):
        return self.get_image(self.index)

    def auto_window(self):
        win_max = np.max(self.values)
        win_min = np.min(self.values)
        self._window_width = win_max-win_min
        self._window_center = (win_max + win_min)//2

    def sum_images(self):
        # collapse the images into one image.
        if (self.values is not None) and (self.values.ndim == 3):
            # create floating point matrix same size as values
            fpvalues = np.array(self.values, dtype=float)
            # for each image rescale pixel values to calibrated units.
            for i, ds in enumerate(self.datasets):
                slope = ds.RescaleSlope if hasattr(ds, 'RescaleSlope') else 1
                intercept = ds.RescaleIntercept if hasattr(ds, 'RescaleIntercept') else 0
                sign = ds.PixelIntensityRelationship if hasattr(ds, 'PixelIntensityRelationship') \
                    else math.copysign(1, slope)
                fpvalues[:, :, i] = fpvalues[:, :, i]*slope + intercept
            image_sum = np.sum(fpvalues, axis=2)
            if sign == 1:   # if sign=1 pixel values increase with x-ray intensity
                # get slope to rescale values to max int16
                intercept = np.min(image_sum)
                slope = (np.max(image_sum) - intercept)/np.iinfo(np.uint16).max
            else:           # if sign = -1 pixel values decrease with x-ray intensity
                intercept = np.max(image_sum)
                slope = (np.min(image_sum) - intercept)/np.iinfo(np.uint16).max
            image_sum = (image_sum - intercept)/slope
            self.datasets[0].PixelData = image_sum.astype(np.uint16, casting='unsafe').tobytes()
            self.size = (int(self.datasets[0].Rows), int(self.datasets[0].Columns), 1)
            self.values = image_sum.reshape(int(self.datasets[0].Rows),  int(self.datasets[0].Columns), 1)
            # A rescale relationship must be established even if it didn't exist before
            if not hasattr(self.datasets[0], 'PixelIntensityRelationship'):
                self.datasets[0].PixelIntensityRelationship = 'LIN'
            if not hasattr(self.datasets[0], 'PixelIntensityRelationshipSign'):
                self.datasets[0].PixelIntensityRelationshipSign = int(sign)
            self.datasets[0].RescaleSlope = slope
            self.datasets[0].RescaleIntercept = intercept
            self.datasets[0].RescaleType = 'CU'
            for image in self.datasets[1:]:
                self.datasets.remove(image)
            self.index = 0
            self.auto_window()

    def avg_images(self):
        # collapse the images into one image.
        if (self.values is not None) and (self.values.ndim == 3):
            image_sum = np.sum(self.values, axis=2)
            image_sum = image_sum/self.size[2]
            self.datasets[0].PixelData = image_sum.astype(np.uint16, casting='unsafe').tobytes()
            self.size = (int(self.datasets[0].Rows), int(self.datasets[0].Columns), 1)
            self.values = image_sum.reshape(int(self.datasets[0].Rows),  int(self.datasets[0].Columns), 1)
            for image in self.datasets[1:]:
                self.datasets.remove(image)
            self.index = 0
            self.auto_window()

    def scale_images(self, factor: float):
        if self.values is not None:
            self.values = self.values*factor
            if self.datasets[0].pixel_array.ndim == 3:
                self.datasets[0].PixelData = self.values.astype(np.uint16, casting='unsafe').tobytes()
            else:
                for i, image in enumerate(self.datasets):
                    image.PixelData = self.values[:, :, i].astype(np.uint16, casting='unsafe').tobytes()
            self.auto_window()

