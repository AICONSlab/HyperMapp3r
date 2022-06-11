===============
# Local Install
=============== 

## Python
For the main required Python packages (numpy, scipy, etc.) we recommend using
[Anaconda for Python 3.6](https://www.continuum.io/downloads)


## ANTs & Convert3D (c3d)

If either ANTs or c3d are not installed on your machine, run `install_depends.sh`, located in the project directory. The required software will be installed in the `depends` directory.  If you are intrested to install c3d on MacOS or Windows, you can dowanlod it from [this link](http://www.itksnap.org/pmwiki/pmwiki.php?n=Downloads.C3D).

## Installing package and dependencies for HippMapp3r locally

1. Clone repository

        git clone https://github.com/AICONSlab/HyperMapp3r.git HyperMapp3r

        (or install zip file and uncompress)

        cd HyperMapp3r

    If you want to create a virtual environment where HyperMapp3r can be run,

        conda create -n hypermapper python=3.6 anaconda
        source activate hypermapper
    
    To end the session, deactivate the environment
    
        source deactivate
    
    To delete the environment,
    
        conda env remove --name hypermapper

2. Install dependencies
    
        pip install git+https://www.github.com/keras-team/keras-contrib.git
    
    If the computer you are using has a GPU:
        
        pip install -e .[hypermapper_gpu]

    If not:
    
        pip install -e .[hypermapper]

3. Test the installation by running

        hypermapper --help
        
   To confirm that the command line function works, and
   
        hypermapper
        
   To launch the interactive GUI.

## Download deep models

Download the models from [this link](https://drive.google.com/drive/folders/1QS3t01jMSJq6zAfjMDu1AzufplGjLODR) and place them in the `models` directory

## For tab completion
    pip3 install argcomplete
    activate-global-python-argcomplete

## Updating HyperMapp3r
To update HyperMapp3r, navigate to the directory where HyperMapp3r was cloned and run

    git pull
    pip install -e .[{option}] -process-dependency-links
    
where "option" is dependent on whether or not you have a GPU (see package installation steps above)
