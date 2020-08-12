#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# coding: utf-8

import os
import sys
import glob
from datetime import datetime
from pathlib import Path
import argcomplete
import argparse
import numpy as np
import nibabel as nib
import subprocess
from nilearn.image import reorder_img, resample_img, resample_to_img, math_img
from hypermapper.deep.predict import run_test_case
from hypermapper.utils import endstatement
from hypermapper.preprocess import biascorr, trim_like
from hypermapper.qc import seg_qc
from nipype.interfaces.fsl import maths
from nipype.interfaces.c3 import C3d
from termcolor import colored

os.environ['TF_CPP_MIN_LOG_LEVEL'] = "3"

###########################################       Functions        #####################################################
def parsefn():
    parser = argparse.ArgumentParser(usage='%(prog)s -s [ subj ] \n\n'
                                           "Segment WMH using a trained CNN")

    optional = parser.add_argument_group('optional arguments')

    optional.add_argument('-s', '--subj', type=str, metavar='', help="input subject")
    optional.add_argument('-fl', '--flair', type=str, metavar='', help="input Flair")
    optional.add_argument('-t1', '--t1w', type=str, metavar='', help="input T1-weighted", )
    optional.add_argument('-t2', '--t2w', type=str, metavar='', help="input T2-weighted")
    optional.add_argument('-m', '--mask', type=str, metavar='', help="brain mask")
    optional.add_argument('-o', '--out', type=str, metavar='', help="output prediction")
    optional.add_argument("-ign_ort", "--ign_ort",  action='store_true',
                          help="ignore orientation if tag is wrong")
    optional.add_argument('-n', '--num_mc', type=int, metavar='', help="number of Monte Carlo Dropout samples", default=20)
    optional.add_argument('-th', '--thresh', type=float, metavar='', help="threshold", default=0.5)
    optional.add_argument('-f', '--force', help="overwrite existing segmentation", action='store_true')

    return parser


def parse_inputs(parser, args):
    if isinstance(args, list):
        args = parser.parse_args(args)
    argcomplete.autocomplete(parser)

    # check if subj or t1w are given
    if (args.subj is None) and (args.t1w is None):
        sys.exit('subj (-s) or t1w (-t1) must be given')

    subj_dir = os.path.abspath(args.subj) if args.subj is not None else os.path.abspath(os.path.dirname(args.t1w))
    subj = os.path.basename(subj_dir)
    print('\n input subject:', subj)

    t1 = args.t1w if args.t1w is not None else '%s/%s_T1_nu.nii.gz' % (subj_dir, subj)
    assert os.path.exists(t1), "%s does not exist ... please check path and rerun script" % t1

    fl = args.flair if args.flair is not None else '%s/%s_T1acq_nu_FL.nii.gz' % (subj_dir, subj)
    assert os.path.exists(fl), "%s does not exist ... please check path and rerun script" % fl

    t2 = args.t2w if args.t2w is not None else '%s/%s_T1acq_nu_T2.nii.gz' % (subj_dir, subj)
    # assert os.path.exists(t2), "%s does not exist ... please check path and rerun script" % t2

    mask = args.mask if args.mask is not None else '%s/%s_T1acq_nu_HfBd.nii.gz' % (subj_dir, subj)
    assert os.path.exists(mask), "%s does not exist ... please check path and rerun script" % mask

    out = args.out if args.out is not None else None

    num_mc = args.num_mc

    thresh = args.thresh

    ign_ort = True if args.ign_ort else False

    force = True if args.force else False
    return subj_dir, subj, t1, fl, t2, mask, out, num_mc, thresh, ign_ort, force

def orient_img(in_img_file, orient_tag, out_img_file):
    c3 = C3d()
    c3.inputs.in_file = in_img_file
    c3.inputs.args = "-orient %s" % orient_tag
    c3.inputs.out_file = out_img_file
    c3.run()

def check_orient(in_img_file, r_orient, l_orient, out_img_file):
    """
    Check image orientation and re-orient if not in standard orientation (RPI or LPI)
    :param in_img_file: input_image
    :param r_orient: right ras orientation
    :param l_orient: left las orientation
    :param out_img_file: output oriented image
    """
    res = subprocess.run('c3d %s -info' % in_img_file, shell=True, stdout=subprocess.PIPE)
    out = res.stdout.decode('utf-8')
    ort_str = out.find('orient =') + 9
    img_ort = out[ort_str:ort_str + 3]

    cp_orient = False
    if (img_ort != r_orient) and (img_ort != l_orient):
        print("\n Warning: input image is not in RPI or LPI orientation.. "
              "\n re-orienting image to standard orientation based on orient tags (please make sure they are correct)")

        if img_ort == 'Obl':
            img_ort = out[-5:-2]
            orient_tag = 'RPI' if 'R' in img_ort else 'LPI'
        else:
            orient_tag = 'RPI' if 'R' in img_ort else 'LPI'
        print(orient_tag)
        orient_img(in_img_file, orient_tag, out_img_file)
        cp_orient = True
    return cp_orient


def cutoff_img(in_file, cutoff_percents, out_file):
    print("\n thresholding ...")
    img = nib.load(in_file)
    data = img.get_data()
    cutoff_low = np.percentile(data, cutoff_percents)
    cutoff_high = np.percentile(data, 100 - cutoff_percents)
    print(cutoff_low)
    print(cutoff_high)
    new_data = data.copy()
    new_data[new_data > cutoff_high] = cutoff_high
    new_data[new_data < cutoff_low] = cutoff_low
    nib.save(nib.Nifti1Image(new_data, img.affine), out_file)


def normalize_sample_wise_img(in_file, out_file):
    image = nib.load(in_file)
    img = image.get_data()
    # standardize intensity for data
    print("\n standardizing ...")
    std_img = (img - img.mean()) / img.std()
    nib.save(nib.Nifti1Image(std_img, image.affine), out_file)

def image_mask(img, mask, img_masked):
    print("\n skull stripping ...")
    c3 = C3d()
    c3.inputs.in_file = img
    c3.inputs.args = "%s -multiply" % mask
    c3.inputs.out_file = img_masked
    c3.run()

def image_binarize(img, img_bin):
    print("\n binarize ...")
    c3 = C3d()
    c3.inputs.in_file = img
    c3.inputs.args = "-binarize -holefill 1 0"
    c3.inputs.out_file = img_bin
    c3.run()

def image_standardize(img, mask, img_std):
    print("\n standardization ...")
    c3 = C3d()
    c3.inputs.in_file = img
    file_shape = nib.load(img).shape
    nx = int(file_shape[0] / 2.2)
    ny = int(file_shape[1] / 2.2)
    nz = int(file_shape[2] / 2.2)
    c3.inputs.args = "%s -nlw %sx%sx%s %s -times -replace nan 0" % (mask, nx, ny, nz, mask)
    # c3.inputs.args = "%s -nlw 60x60x50 %s -times -replace nan 0" % (mask, mask)
    c3.inputs.out_file = img_std
    c3.run()

# def resample_trim(img, img_resampled, interp=1, voxels=5):
#     print("\n resmapling and cropping ...")
#     c3 = C3d()
#     c3.inputs.in_file = img
#     c3.inputs.args = "-int %s -resample-mm 0.6x0.6x1mm -trim %svox" % (interp, voxels)
#     c3.inputs.out_file = img_resampled
#     c3.run()
#
# def resample_trim_like(img, img_resampled, img_ref, interp=1):
#     print("\n resmapling and cropping ...")
#     c3 = C3d()
#     c3.inputs.in_file = img
#     c3.inputs.args = "-int %s -resample-mm 0.6x0.6x1mm -as res %s -push res -reslice-identity" % (interp, img_ref)
#     c3.inputs.out_file = img_resampled
#     c3.run()

def trim(in_img_file, out_img_file, voxels=1):
    print("\n cropping ...")
    c3 = C3d()
    c3.inputs.in_file = in_img_file
    c3.inputs.args = "-trim %svox" % voxels
    c3.inputs.out_file = out_img_file
    c3.run()

def trim_like(in_img_file, ref_img_file, out_img_file, interp=1):
    print("\n cropping ...")
    c3 = C3d()
    c3.inputs.in_file = ref_img_file
    c3.inputs.args = "-int %s %s -reslice-identity" % (interp, in_img_file)
    c3.inputs.out_file = out_img_file
    c3.run()

def resample(img, x, y, z, out, interp=0):
    print("\n resmapling ...")
    c3 = C3d()
    c3.inputs.in_file = img
    c3.inputs.args = "-int %s -resample %sx%sx%s" % (interp, x, y, z)
    c3.inputs.out_file = out
    c3.run()

def resample_like(img, ref, out, interp=0):
    print("\n resmapling ...")
    c3 = C3d()
    c3.inputs.in_file = ref
    c3.inputs.args = "-int %s %s -reslice-identity" % (interp, img)
    c3.inputs.out_file = out
    c3.run()

def copy_orient(in_img_file, ref_img_file, out_img_file):
    print("\n copy orientation ...")
    c3 = C3d()
    c3.inputs.in_file = ref_img_file
    c3.inputs.args = "%s -copy-transform -type uchar" % in_img_file
    c3.inputs.out_file = out_img_file
    c3.run()

###########################################        Main        #########################################################
def main(args):
    parser = parsefn()
    subj_dir, subj, t1, fl, t2, mask, out, num_mc, thresh, ign_ort, force = parse_inputs(parser, args)
    cp_orient = False

    if out is None:
        prediction = '%s/%s_T1acq_nu_wmh_pred.nii.gz' % (subj_dir, subj)
        prediction_std_orient = '%s/%s_T1acq_nu_wmh_pred_std_orient.nii.gz' % (subj_dir, subj)
    else:
        prediction = out
        prediction_std_orient = "%s/%s_std_orient.nii.gz" % (subj_dir, os.path.basename(out).split('.')[0])

    prediction_prob = '%s/%s_wmh_prob.nii.gz' % (subj_dir, subj)

    if os.path.exists(prediction) and force is False:
        print(colored("\n %s already exists" % prediction, 'green'))
    else:
        start_time = datetime.now()

        file_path = os.path.realpath(__file__)
        hyper_dir = Path(file_path).parents[2]

        model_name = 'wmh_mcdp_multi'
        model_json = '%s/models/%s_model.json' % (hyper_dir, model_name)
        model_weights = '%s/models/%s_model_weights.h5' % (hyper_dir, model_name)

        assert os.path.exists(model_json), "%s does not exits ... please download and rerun script" % model_json
        assert os.path.exists(model_weights), "%s does not exits ... please download and rerun script" % model_weights

        # pred preprocess dir
        pred_dir = '%s/pred_process_wmh' % os.path.abspath(subj_dir)
        if not os.path.exists(pred_dir):
            os.mkdir(pred_dir)

        #pred_dir_mcdp = '%s/pred_process_wmh_mcdp' % os.path.abspath(subj_dir)
        # if not os.path.exists(pred_dir_mcdp):
        #     os.mkdir(pred_dir_mcdp)

        ############################## new method #############################################
        print(colored("\n pre-processing.......", 'green'))

        # standardize intensity and mask data
        c3 = C3d()
        training_mods = ["t1", "fl"]
        test_seqs = [t1, fl]

        # std orientations
        r_orient = 'RPI'
        l_orient = 'LPI'

        # check orientation t1 and mask
        t1_ort = "%s/%s_std_orient.nii.gz" % (subj_dir, os.path.basename(t1).split('.')[0])
        if ign_ort is False:
            cp_orient = check_orient(t1, r_orient, l_orient, t1_ort)
        in_t1 = t1_ort if os.path.exists(t1_ort) else t1

        mask_ort = "%s/%s_std_orient.nii.gz" % (subj_dir, os.path.basename(mask).split('.')[0])
        if ign_ort is False:
            cp_orient_m = check_orient(mask, r_orient, l_orient, mask_ort)
        in_mask = mask_ort if os.path.exists(mask_ort) else mask

        for s, seq in enumerate(test_seqs):
            print(colored("\n pre-processing %s" % os.path.basename(seq).split('.')[0], 'green'))

            # check orientation
            seq_ort = "%s/%s_std_orient.nii.gz" % (subj_dir, os.path.basename(seq).split('.')[0])
            if training_mods[s] != 't1':
                if ign_ort is False:
                    cp_orient_seq = check_orient(seq, r_orient, l_orient, seq_ort)
            in_seq = seq_ort if os.path.exists(seq_ort) else seq

            # masked
            seq_masked = "%s/%s_masked.nii.gz" % (pred_dir, os.path.basename(seq).split('.')[0])
            image_mask(in_seq, in_mask, seq_masked)

            # # binarized
            # seq_bin = "%s/%s_masked_bin.nii.gz" % (pred_dir, os.path.basename(seq).split('.')[0])
            # image_binarize(seq_masked, seq_bin)

            # # standardized
            # seq_std = "%s/%s_masked_standardized.nii.gz" % (pred_dir, os.path.basename(seq).split('.')[0])
            # image_standardize(seq_masked, seq_bin, seq_std)

            # cropped and standardized
            if training_mods[s] == 't1':
                seq_res_trim = '%s/t1_masked_cropped.nii.gz' % pred_dir
                # resample_trim(seq_std, seq_res_trim, interp=1, voxels=1)
                trim(seq_masked, seq_res_trim, voxels=1)
                # standardized
                seq_std = "%s/t1_masked_cropped_standardized.nii.gz" % pred_dir
                normalize_sample_wise_img(seq_res_trim, seq_std)
            else:
                seq_res_trim = '%s/fl_masked_cropped.nii.gz' % pred_dir
                img_ref = '%s/t1_masked_cropped.nii.gz' % pred_dir
                # resample_trim_like(seq_std, seq_res_trim, img_ref, interp=1)
                trim_like(seq_masked, img_ref, seq_res_trim, interp=1)
                # standardized
                seq_std = "%s/fl_masked_cropped_standardized.nii.gz" % pred_dir
                normalize_sample_wise_img(seq_res_trim, seq_std)

        t1_new = '%s/t1_masked_cropped_standardized.nii.gz' % pred_dir
        fl_new = '%s/fl_masked_cropped_standardized.nii.gz' % pred_dir
        test_seqs_new = [t1_new, fl_new]
        pred_shape = [160, 160, 160]
        t1_img = nib.load(t1_new)
        test_data = np.zeros((1, len(training_mods), pred_shape[0], pred_shape[1], pred_shape[2]),
                             dtype=t1_img.get_data_dtype())

        # resample t1
        res_t1_file = '%s/%s_resampled.nii.gz' % (pred_dir, os.path.basename(t1_new).split('.')[0])
        resample(t1_new, pred_shape[0], pred_shape[1], pred_shape[2], res_t1_file, interp=1)

        for s, seq in enumerate(test_seqs_new):
            if training_mods[s] != 't1':
                # resample images
                seq_res = '%s/%s_resampled.nii.gz' % (pred_dir, os.path.basename(seq).split('.')[0])
                resample(seq, pred_shape[0], pred_shape[1], pred_shape[2], seq_res, interp=1)
            else:
                seq_res = res_t1_file

            if not os.path.exists(seq_res):
                print("\n pre-processing %s" % training_mods[s])
                c3.run()
            res_data = nib.load(seq_res)
            test_data[0, s, :, :, :] = res_data.get_data()

        res = nib.load(res_t1_file)
        #############################################################################################
        print(colored("\n predicting WMH segmentation using MC Dropout with %s samples" %num_mc, 'green'))

        pred_s = np.zeros((num_mc, pred_shape[0], pred_shape[1], pred_shape[2]), dtype=res.get_data_dtype())

        for sample_id in range(num_mc):
            print(sample_id)
            pred = run_test_case(test_data=test_data, model_json=model_json, model_weights=model_weights,
                                 affine=res.affine, output_label_map=True, labels=1)
            pred_s[sample_id, :, :, :] = pred.get_data()
            #nib.save(pred, os.path.join(pred_dir_mcdp, "wmh_pred_%s.nii.gz" % sample_id))

        # computing mean
        pred_mean = pred_s.mean(axis=0)
        pred = nib.Nifti1Image(pred_mean, res.affine)

        pred_prob = os.path.join(pred_dir, "wmh_prob.nii.gz")
        nib.save(pred, pred_prob)

        pred_th_name = os.path.join(pred_dir, "wmh_pred.nii.gz")
        pred_th = math_img('img > %s' % thresh, img=pred)
        nib.save(pred_th, pred_th_name)

        # resample back
        pred_res = resample_to_img(pred_prob, nib.load(in_t1), interpolation="linear")
        pred_prob_name = os.path.join(pred_dir, "%s_%s_pred_prob.nii.gz" % (subj, model_name))
        nib.save(pred_res, pred_prob_name)

        pred_res_th = math_img('img > %s' % thresh, img=pred_res)
        pred_name = os.path.join(pred_dir, "%s_%s_pred.nii.gz" % (subj, model_name))
        nib.save(pred_res_th, pred_name)

        #############################################################################################
        # copy original orientation to final prediction
        if ign_ort is False and cp_orient:
            nib.save(pred_res_th, prediction_std_orient)
            copy_orient(pred_name, t1, prediction)

            copy_orient(pred_prob_name, t1, prediction_prob)
        else:
            nib.save(pred_res_th, prediction)
            nib.save(pred_res, prediction_prob)

        print(colored("\n generating mosaic image for qc", 'green'))
        # seg_qc.main(['-i', '%s' % fl, '-s', '%s' % prediction, '-g', '5', "-m", "75"])
        seg_qc.main(['-i', '%s' % fl_new, '-s', '%s' % prediction])

        endstatement.main('WMH prediction', '%s' % (datetime.now() - start_time))

if __name__ == "__main__":
    main(sys.argv[1:])