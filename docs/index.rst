=======================================
Welcome to HyperMapp3r's documentation! 
=======================================

.. HyperMapp3r documentation master file, created by
   sphinx-quickstart on Fri Dec 14 15:34:18 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


*HyperMapp3r* (pronounced hypermapper) is a CNN-based segmentation algorithm of White Matter Hyperintensity(WMH) segmentation
using MRI images from BrainLab.
It can deal with brains with extensive atrophy and segments the wmh in seconds.
It uses a T1-weighted, FLAIR, and brain mask images as the inputs and segments.

We recommend using HyperMapp3r with the Docker or Singularity containers we provide 
but it can also be installed locally. See our 
:doc:`installation instructions <./install>` for more information.

Copyright (C) 2020 AICONSLab.

.. image:: images/wmh_pipeline.png
    :width: 800px
    :alt: Graph abstract
    :align: center

    
.. toctree::
   :maxdepth: 2
   :caption: Contents:

   before_install 
   install 
   beginner
   wmh_seg    
   docker 



