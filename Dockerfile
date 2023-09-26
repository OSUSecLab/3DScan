# Use an official Ubuntu as a parent image
FROM ubuntu:22.04

# Set the workspace directory
ARG workspace=/opt
RUN mkdir -p $workspace
WORKDIR $workspace

# Install required packages and dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    unzip \
    gcc \
    make \
    python3-pip \
    zlib1g-dev


# Clone the repository and download dependencies
RUN git clone https://github.com/OSUSecLab/3DScan
RUN wget "https://github.com/OSUSecLab/3DScan/releases/download/dependents/AssetStudio.executable.zip"
RUN wget "https://github.com/OSUSecLab/3DScan/releases/download/dependents/wine.drive.zip"
RUN wget "https://github.com/OSUSecLab/3DScan/releases/download/dependents/wine.source.zip"
RUN unzip AssetStudio.executable.zip && rm AssetStudio.executable.zip
RUN unzip wine.drive.zip && rm wine.drive.zip
RUN unzip wine.source.zip && rm wine.source.zip

ENV PATH="${workspace}/wine-source:${PATH}"

RUN wget "https://dl.winehq.org/wine/wine-mono/8.0.0/wine-mono-8.0.0-x86.msi"
RUN wine64 msiexec /i wine-mono-8.0.0-x86.msi
RUN rm wine-mono-8.0.0-x86.msi

# Create a symbolic link for libpng
RUN wget https://download.sourceforge.net/libpng/libpng-1.5.13.tar.gz
RUN tar -xf libpng-1.5.13.tar.gz
RUN rm libpng-1.5.13.tar.gz
RUN cd libpng-1.5.13 && ./configure && make && make install
RUN ln -s /usr/local/lib/libpng15.so.15 /usr/lib/x86_64-linux-gnu/libpng15.so.15

RUN python3 -m pip install scipy psutil

# Start the container with a tail command to keep it running
CMD tail -f /dev/null