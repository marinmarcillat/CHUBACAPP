
*********************
The complete pipeline
*********************

*From raw image/video to geo-referenced 3D annotations*

Draft

Why 3D annotations?
===================

- Because it's more precise
- Because you can work with complex topographies
- Because you have access to topographic information (slope, roughness...)
- Because it's way cooler !

What you will need :
====================

Your data
*********

You will need:

- **Raw images or video**

Your images should overlap each other at least 50%. Try to avoid black images in your dataset.
Your video should not be too fast.

- **Navigation file**

This is required for the 3D reconstruction. If not provided, your reconstruction won't be dimensionaly accurate. Please refer to the `Matisse 3D manual <https://github.com/IfremerUnderwater/Matisse/blob/master/Config/help/MatisseHelp_EN.pdf>`_ for the structure of your navigation file.

- **Your camera intrinsics parameters**

This is required for the 3D reconstruction. See `Matisse 3D manual <https://github.com/IfremerUnderwater/Matisse/blob/master/Config/help/MatisseHelp_EN.pdf>`_ for more information.

If using Ifremer ROV, this is not necessary.

Software
*********

Every software needed is free and mostly open source. You will need:

- Matisse 3D
- Chubacapp
- An access to an instance of Biigle (biigle.de or `your own instance <https://biigle-admin-documentation.readthedocs.io/installation/>`_)

Optional but useful:

- 3D metrics (to visualize 3D annotations)
- Cloud compare (to visualize 3D models)

To download Matisse3D (2D and 3D mosaics): `Matisse3D <https://github.com/IfremerUnderwater/Matisse/releases>`_

To download 3D Metrics (3D models and annotations visualization): `3D Metrics <https://github.com/IfremerUnderwater/3DMetrics/releases>`_

Constructing the 3D model
=========================

1. Preprocess images using Matisse 3D Preprocessing tool

`Matisse 3D manual <https://github.com/IfremerUnderwater/Matisse/blob/master/Config/help/MatisseHelp_EN.pdf>`_

2. Reconstruct the 3D model using Matisse 3D

`Matisse 3D manual <https://github.com/IfremerUnderwater/Matisse/blob/master/Config/help/MatisseHelp_EN.pdf>`_

Get your disjoint images for annotation
=======================================

Using the same images that you used for 3D reconstruction :

1. If necessary, correct your navigation file using your 3D model

If your navigation isn't precise, you might want to correct it using the camera positions computed during the
reconstruction phase. You can do this using CHUBACAPP tab ... .

2. If necessary, remove blurry images

To avoid having to annotate blurry images, you can remove the blurriest images of your dataset using this CHUBACAPP tab:

3. Select disjoint images using your reprojection

This CHUBACAPP algorithm will reproject the outline of your images on the 3D model using ray-casting,
compute which of these are in contact and select non overlapping images.
This process can be slow, as the reprojection and the contact detection algorithm are complex.

You will get an selected image dataset ready to annotate.

Annotate your images using Biigle
=================================

Annotate the dataset using Biigle.

Manual annotations
******************

Automatic annotations
*********************

Coming soon !

Reproject
=========

Reproject using the  :ref:`reprojection tab <reprojection target>`:

Enjoy your 3D annotations !
===========================



