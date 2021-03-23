# Use a Linux Distro as a parent image
FROM ubuntu:16.04

# Set up
RUN apt-get update && apt-get install -y git wget build-essential g++ gcc cmake curl clang && \
    apt-get install -y libfreetype6-dev apt-utils pkg-config vim gfortran && \
    apt-get install -y binutils make linux-source unzip && \
    apt install -y libsm6 libxext6 libfontconfig1 libxrender1 libgl1-mesa-glx && \
    apt-get install -y python3-pip python3-dev && \
    cd /usr/local/bin/ && \
    ln -s /usr/bin/python3 python && \
    pip3 install --upgrade pip==20.3.4 && \
    cd ~

# Install c3d
RUN wget https://downloads.sourceforge.net/project/c3d/c3d/Nightly/c3d-nightly-Linux-x86_64.tar.gz && \
    tar -xzvf c3d-nightly-Linux-x86_64.tar.gz && mv c3d-1.1.0-Linux-x86_64 /opt/c3d && \
    rm c3d-nightly-Linux-x86_64.tar.gz
ENV PATH /opt/c3d/bin:${PATH}

# FSL
# Installing Neurodebian packages FSL
# RUN wget -O- http://neuro.debian.net/lists/xenial.us-tn.full | tee /etc/apt/sources.list.d/neurodebian.sources.list
# RUN apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9

# Install FSL
RUN apt-get update && apt-get install -y fsl

ENV FSLDIR="/usr/share/fsl/5.0" \
    FSLOUTPUTTYPE="NIFTI_GZ" \
    FSLMULTIFILEQUIT="TRUE" \
    POSSUMDIR="/usr/share/fsl/5.0" \
    LD_LIBRARY_PATH="/usr/lib/fsl/5.0:$LD_LIBRARY_PATH" \
    FSLTCLSH="/usr/bin/tclsh" \
    FSLWISH="/usr/bin/wish" \
    POSSUMDIR="/usr/share/fsl/5.0"

ENV PATH="/usr/lib/fsl/5.0:${PATH}"

# Install ANTs
ENV ANTSPATH /opt/ANTs
RUN mkdir -p /opt/ANTs && \
    curl -sSL "https://dl.dropbox.com/s/2f4sui1z6lcgyek/ANTs-Linux-centos5_x86_64-v2.2.0-0740f91.tar.gz" \
    | tar -xzC $ANTSPATH --strip-components 1
ENV PATH=${ANTSPATH}:${PATH}

# Install all needed packages based on pip installation
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY . .

# Download models, store in directory
RUN mkdir -p /src/icvmapp3r/models /src/hypermapp3r/models && \
#     wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1r_TyA65nJoH7Dt2S6oZEluakAgWbPn3_' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1r_TyA65nJoH7Dt2S6oZEluakAgWbPn3_" -O /src/hypermapp3r/models/wmh_mcdp_multi_model_weights.h5 && \
#     rm -rf /tmp/cookies.txt && \
#     wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1fU566Xtr6KuQ4oT3XWG3s84f6IG2yYfO' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1fU566Xtr6KuQ4oT3XWG3s84f6IG2yYfO" -O /src/hypermapp3r/models/wmh_mcdp_multi_model.json && \
#     rm -rf /tmp/cookies.txt && \

    wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1TDHy6dyuD3CmUPcYJZSHmtOfNEFNhPO4' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1TDHy6dyuD3CmUPcYJZSHmtOfNEFNhPO4" -O /src/hypermapp3r/models/wmh_mcdp_224iso_multi_model_weights.h5 && \
    rm -rf /tmp/cookies.txt && \
    wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1u60w2CzcvMk9JeEFvoCSixoKwLHEaPyQ' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1u60w2CzcvMk9JeEFvoCSixoKwLHEaPyQ" -O /src/hypermapp3r/models/wmh_mcdp_224iso_multi_model.json && \
    rm -rf /tmp/cookies.txt


# Run hypermapper when the container launches
# ENTRYPOINT ["/bin/bash"]

