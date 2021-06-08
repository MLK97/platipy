# Copyright 2020 University of New South Wales, University of Sydney, Ingham Institute

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pathlib

import numpy as np
import SimpleITK as sitk

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from matplotlib import rcParams


def generate_animation_from_image_sequence(
    image_list,
    output_file="animation.gif",
    fps=10,
    contour_list=False,
    scalar_list=False,
    figure_size_in=6,
    image_cmap=plt.cm.get_cmap("Greys_r"),
    contour_cmap=plt.cm.get_cmap("jet"),
    scalar_cmap=plt.cm.get_cmap("magma"),
    image_window=[-1000, 800],
    scalar_min=False,
    scalar_max=False,
    scalar_alpha=0.5,
    image_origin="lower",
):
    """Generates an animation from a list of images, with optional scalar overlay and contours.

    Args:
        image_list (list (SimpleITK.Image)): A list of SimpleITK (2D) images.
        output_file (str, optional): The name of the output file. Defaults to "animation.gif".
        fps (int, optional): Frames per second. Defaults to 10.
        contour_list (list (SimpleITK.Image), optional): A list of SimpleITK (2D) images
            (overlay as scalar field). Defaults to False.
        scalar_list (list (SimpleITK.Image), optional): A list of SimpleITK (2D) images
            (overlay as contours). Defaults to False.
        figure_size_in (int, optional): Size of the figure. Defaults to 6.
        image_cmap (matplotlib.colors.ListedColormap, optional): Colormap to use for the image.
            Defaults to plt.cm.get_cmap("Greys_r").
        contour_cmap (matplotlib.colors.ListedColormap, optional): Colormap to use for contours.
            Defaults to plt.cm.get_cmap("jet").
        scalar_cmap (matplotlib.colors.ListedColormap, optional): Colormap to use for scalar field.
            Defaults to plt.cm.get_cmap("magma").
        image_window (list, optional): Image intensity window (mininmum, range).
            Defaults to [-1000, 800].
        scalar_min (bool, optional): Minimum scalar value to show. Defaults to False.
        scalar_max (bool, optional): Maximum scalar value to show. Defaults to False.
        scalar_alpha (float, optional): Alpha (transparency) for scalar field. Defaults to 0.5.
        image_origin (str, optional): Image origin. Defaults to "lower".

    Raises:
        RuntimeError: If ImageMagick isn't installed you cannot use this function!
        ValueError: The list of images must be of type SimpleITK.Image

    Returns:
        matplotlib.animation: The animation.
    """

    # We need to check for ImageMagick
    # There may be other tools that can be used
    rcParams["animation.convert_path"] = r"/usr/bin/convert"
    convert_path = pathlib.Path(rcParams["animation.convert_path"])

    if not convert_path.exists():
        raise RuntimeError("To use this function you need ImageMagick.")

    if not all(isinstance(i, sitk.Image) for i in image_list):
        raise ValueError("Each image must be a SimpleITK image (sitk.Image).")

    # Get the image information
    x_size, y_size = image_list[0].GetSize()
    x_spacing, y_spacing = image_list[1].GetSpacing()

    asp = y_spacing / x_spacing

    # Define the figure
    figure_size = (figure_size_in, figure_size_in * (asp * y_size) / (1.0 * x_size))
    fig, ax = plt.subplots(1, 1, figsize=(figure_size))

    # Display the first image
    # This will be updated
    display_image = ax.imshow(
        sitk.GetArrayFromImage(image_list[0]),
        aspect=asp,
        interpolation=None,
        origin=image_origin,
        cmap=image_cmap,
        clim=(image_window[0], image_window[0] + image_window[1]),
    )

    # We now deal with the contours
    # These can be given as a list of sitk.Image objects or a list of dicts {"name":sitk.Image}
    if contour_list is not False:

        if not isinstance(contour_list[0], dict):
            plot_dict = {"_": contour_list[0]}
            contour_labels = False
        else:
            plot_dict = contour_list[0]
            contour_labels = True

        color_map = contour_cmap(np.linspace(0, 1, len(plot_dict)))

        for index, (contour_name, contour) in enumerate(plot_dict.items()):

            display_contours = ax.contour(
                sitk.GetArrayFromImage(contour),
                colors=[color_map[index]],
                levels=[0],
                linewidths=2,
            )

            display_contours.collections[0].set_label(contour_name)

        if contour_labels:
            approx_scaling = figure_size_in / (len(plot_dict.keys()))
            ax.legend(
                loc="upper left",
                bbox_to_anchor=(0.05, 0.95),
                fontsize=min([10, 16 * approx_scaling]),
            )

    if scalar_list is not False:

        if scalar_min is False:
            scalar_min = np.min([sitk.GetArrayFromImage(i) for i in scalar_list])
        if scalar_max is False:
            scalar_max = np.max([sitk.GetArrayFromImage(i) for i in scalar_list])

        display_scalar = ax.imshow(
            np.ma.masked_outside(sitk.GetArrayFromImage(scalar_list[0]), scalar_min, scalar_max),
            aspect=asp,
            interpolation=None,
            origin=image_origin,
            cmap=scalar_cmap,
            clim=(scalar_min, scalar_max),
            alpha=scalar_alpha,
            vmin=scalar_min,
            vmax=scalar_max,
        )

    ax.axis("off")
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

    # The animate function does (you guessed it) the animation
    def animate(i):

        # Update the imaging data
        nda = sitk.GetArrayFromImage(image_list[i])
        display_image.set_data(nda)

        # TO DO - add in code for scalar overlay
        if contour_list is not False:
            try:
                ax.collections = []
            except ValueError:
                pass

            if not isinstance(contour_list[i], dict):
                plot_dict = {"_": contour_list[i]}
            else:
                plot_dict = contour_list[i]

            color_map = contour_cmap(np.linspace(0, 1, len(plot_dict)))

            for index, contour in enumerate(plot_dict.values()):

                ax.contour(
                    sitk.GetArrayFromImage(contour),
                    colors=[color_map[index]],
                    levels=[0],
                    linewidths=2,
                )

        if scalar_list is not False:
            nda = sitk.GetArrayFromImage(scalar_list[i])
            display_scalar.set_data(np.ma.masked_outside(nda, scalar_min, scalar_max))

        return (display_image,)

    # create animation using the animate() function with no repeat
    my_animation = animation.FuncAnimation(
        fig,
        animate,
        frames=np.arange(0, len(image_list), 1),
        interval=10,
        blit=True,
        repeat=False,
    )

    # save animation at 30 frames per second
    my_animation.save(output_file, writer="imagemagick", fps=fps)

    return my_animation
