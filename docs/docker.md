# Docker / Singularity

If you intend to use Singularity, scroll down to the Singularity section. Otherwise, the steps to use the image in Docker can be found below.

## Before using Docker image for HyperMapp3r

If you want to use Docker to run HyperMapp3r, you must first install Docker on your system. While the installation method differs per system, instructions can be found for the following:

- [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
- [Windows](https://docs.docker.com/docker-for-windows/install/)
- [Mac](https://docs.docker.com/docker-for-mac/)

Once Docker is installed, open the docker terminal and test it with the command

    docker run hello-world


## Pulling HyperMapp3r's Docker image

While you can download various Docker images, for the sake of this tutorial pull the HyperMpp3r image

    docker pull mgoubran/hypermapper:latest

Verify that the image was pulled successfully by checking all images on your system

    docker images


## Running the Docker image

If you have installed Docker for the first time. and have verified that the `hello-world` image was running, then HippMapper can be run on your syste.

The simplest way to run the container is:

    docker run -it mgoubran/hypermapper seg_wmh -t1 /hypermapper/data/test_case/t1.nii.gz -fl /hypermapper/data/test_case/fl.nii.gz -m /hypermapper/data/test_case/mask.nii.gz

To run the Docker container in an interactive shell, run

    docker run --rm -v {enter/path/here}:/root -it --entrypoint /bin/bash mgoubran/hypermapper



## Using HyperMapper on Singularity

Docker images can still be used on Singularity. This is especially good if you are processing images using Compute Canada clusters. The following instructions are based on the steps provided on the [Compute Canada wiki](https://docs.computecanada.ca/wiki/Singularity).

Load the specific Singularity module you would like to use.

    module load singularity/3.5

Although hypermapper is stored as a Docker image, it can be built in singularity by calling:

    singularity build hypermapper.sif docker://mgoubran/hypermapper

To ensure that the Docker image has been built in Singularity, run

    singularity exec hypermapper.sif hypermapper --help


