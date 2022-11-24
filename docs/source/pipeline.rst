
*********************
The complete pipeline
*********************

*From raw image/video to geo-referenced 3D annotations*

Not yet ready

Why 3D annotations?
===================

Because it's way cooler !

What you will need :
====================

Your data
*********

You will need:

- Raw images or video

Your images should overlap each other at least 50%. Try to avoid black images in your dataset.
Your video should not be too fast.

- Navigation file

This is required for the 3D reconstruction. If not provided, your reconstruction won't be dimensionaly accurate. Please refer to the `Matisse 3D manual <https://github.com/IfremerUnderwater/Matisse/blob/master/Config/help/MatisseHelp_EN.pdf>`_ for the structure of your navigation file.

- Your camera intrinsics parameters

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

For images:

For videos:

2. Reconstruct the 3D model using Matisse 3D



Get your disjoint images for annotation
=======================================

1. Correct your navigation file using your 3D model

2. If necessary, remove blurry images

3. Generate a 2D disjoint mosaic (Temporary)

Annotate your images using Biigle
=================================

Manual annotations
******************

Automatic annotations
*********************

Reproject
=========

Enjoy your 3D annotations !
===========================


