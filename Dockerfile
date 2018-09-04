FROM ubuntu:xenial

MAINTAINER lars.claussen <lars.claussen@nelen-schuurmans.nl>

# Change the date to force rebuilding the whole image.
ENV REFRESHED_AT 2018-03-02

# http://click.pocoo.org/5/python3/#python-3-surrogate-handling
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

ARG DEBIAN_FRONTEND=noninteractive

# Add ubuntugis PPA. A recent GDAL version is required by the GPKG driver.
# NB: Package software-properties-common has python3 as a dependency.
RUN apt-get update && apt-get install -y software-properties-common \
&& add-apt-repository -y ppa:ubuntugis/ppa \
&& rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    curl \
    libgdal-dev \
    libhdf5-serial-dev \
    libnetcdf-dev \
    netcdf-bin \
    python3-dev \
&& rm -rf /var/lib/apt/lists/*

# Avoid issues with upgrading an apt-managed pip.
RUN curl -s https://bootstrap.pypa.io/get-pip.py | python3

WORKDIR /code
COPY requirements* /code/
RUN pip install --no-cache-dir -r requirements.txt -r requirements_dev.txt
