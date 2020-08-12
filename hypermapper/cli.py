#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# coding: utf-8

import argcomplete
import argparse
import logging
import os
import sys
import warnings

from hypermapper import __version__
from hypermapper import gui
from hypermapper.segment import hypermapper
from hypermapper.convert import filetype
from hypermapper.preprocess import biascorr, trim_like
from hypermapper.qc import seg_qc
from hypermapper.stats import summary_wmh_vols
from hypermapper.utils.path_manager import add_paths

warnings.simplefilter("ignore")
# warnings.simplefilter("ignore", RuntimeWarning)
# warnings.simplefilter("ignore", FutureWarning)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = "3"


# --------------
# functions


def run_filetype(args):
    filetype.main(args)


def run_hypermapper(args):
    hippmapper.main(args)


def run_wmh_seg_summary(args):
    summary_wmh_vols.main(args)


def run_seg_qc(args):
    seg_qc.main(args)


def run_utils_biascorr(args):
    biascorr.main(args)


def run_trim_like(args):
    trim_like.main(args)

# --------------
# parser


def get_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    # --------------

    # seg white matter hyperintensity (WMH)
    hyper_parser = hypermapper.parsefn()
    parser_seg_hyper = subparsers.add_parser('seg_wmh', add_help=False, parents=[hyper_parser],
                                            help="Segment white matter hyperintensity (WMH) using a trained CNN",
                                            usage=hyper_parser.usage)
    parser_seg_hyper.set_defaults(func=run_hypermapper)

    # --------------

    # seg qc
    seg_qc_parser = seg_qc.parsefn()
    parser_seg_qc = subparsers.add_parser('seg_qc', add_help=False, parents=[seg_qc_parser],
                                          help="Create tiled mosaic of segmentation overlaid on structural image",
                                          usage=seg_qc_parser.usage)
    parser_seg_qc.set_defaults(func=run_seg_qc)

    # --------------

    # utils biascorr
    biascorr_parser = biascorr.parsefn()
    parser_utils_biascorr = subparsers.add_parser('bias_corr', add_help=False, parents=[biascorr_parser],
                                                  help="Bias field correct images using N4",
                                                  usage=biascorr_parser.usage)
    parser_utils_biascorr.set_defaults(func=run_utils_biascorr)

    # --------------

    # filetype
    filetype_parser = filetype.parsefn()
    parser_filetype = subparsers.add_parser('filetype', add_help=False, parents=[filetype_parser],
                                            help="Convert the Analyse format to Nifti",
                                            usage=filetype_parser.usage)
    parser_filetype.set_defaults(func=run_filetype)

    # --------------

    # wmh vol seg
    wmh_vol_parser = summary_wmh_vols.parsefn()
    parser_stats_wmh = subparsers.add_parser('stats_wmh', add_help=False, parents=[wmh_vol_parser],
                                            help="Generates volumetric summary of WMH segmentations",
                                            usage=wmh_vol_parser.usage)
    parser_stats_wmh.set_defaults(func=run_wmh_seg_summary)

    # --------------

    # trim like
    trim_parser = trim_like.parsefn()

    parser_trim_like = subparsers.add_parser('trim_like', help='Trim or expand image in same space like reference',
                                             add_help=False, parents=[trim_parser],
                                             usage='%(prog)s -i [ img ] -r [ ref ] -o [ out ] \n\n'
                                                   'Trim or expand image in same space like reference')
    parser_trim_like.set_defaults(func=run_trim_like)

    # --------------------

    # version
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s {version}'.format(version=__version__))

    return parser


# --------------
# main fn

def main(args=None):
    """ main cli call"""
    if args is None:
        args = sys.argv[1:]

    parser = get_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)

    if hasattr(args, 'func'):

        # set filename, file path for the log file
        log_filename = args.func.__name__.split('run_')[1]
        if hasattr(args, 'subj'):
            if args.subj:
                log_filepath = os.path.join(args.subj, 'logs', '{}.log'.format(log_filename))

            elif hasattr(args, 't1w'):
                if args.t1w:
                    log_filepath = os.path.join(os.path.dirname(args.t1w), 'logs', '{}.log'.format(log_filename))

        else:
            log_filepath = os.path.join(os.getcwd(), '{}.log'.format(log_filename))

        os.makedirs(os.path.dirname(log_filepath), exist_ok=True)

        # log keeps console output and redirects to file
        root = logging.getLogger('interface')
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        handler = logging.FileHandler(filename=log_filepath)
        handler.setFormatter(formatter)
        root.addHandler(handler)

        with add_paths():  # context manager added to account for adding paths
            args.func(args)

    else:
        gui.main()


if __name__ == '__main__':
    main()
