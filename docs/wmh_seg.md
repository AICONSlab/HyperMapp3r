# Segmentation tutorials

## GUI

Watch this video tutorial:

[![IMAGE ALT TEXT](https://img.youtube.com/vi/QF-1oIQ4eRA/0.jpg)](https://youtu.be/QF-1oIQ4eRA "Hipp Seg")

-----

Or follow the steps below:

After opening the HyperMapper GUI, click "WMH" under the "Segmentation" tab. Wait for a new pop-up window to appear. The window should look like the image below.

![](images/hypermapper_seg_wmh_popup.png)

Click "Select t1w" and chose your T1 image. Click "Run".
Type your desired output name in the "out" box.
Your output file will automatically appear in your t1w folder.


## Command Line

    hippmapper seg_wmh
    
    optional arguments:
    -h, --help            show this help message and exit
    -s , --subj           input subject
    -fl dir, --flair dir  input Flair
    -t1 , --t1w           input T1-weighted
    -t2 , --t2w           input T2-weighted
    -m , --mask           brain mask
    -o , --out            output prediction
    -ign_ort, --ign_ort   ignore orientation if tag is wrong
    -n , --num_mc         number of Monte Carlo Dropout samples
    -th , --thresh        threshold
    -f, --force           overwrite existing segmentation
    
    Examples:
    hypermapper seg_wmh -s subjectname -b
    hypermapper seg_wmh -t1 subject_T1_nu.nii.gz fl subject_T1acq_nu_FL.nii.gz -m subject_T1acq_nu_HfB.nii.gz -o subject_wmh_pred.nii.gz

The output should look like this.:

![](images/3d_snap.png)
