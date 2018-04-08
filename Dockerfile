FROM ubuntu:xenial

MAINTAINER lars.claussen <lars.claussen@nelen-schuurmans.nl>

# Change the date to force rebuilding the whole image
ENV REFRESHED_AT 2018-03-02

# system dependencies
RUN apt-get update && apt-get install -y \
    git \
    python-pip \
    python-gdal \
    libhdf5-serial-dev \
    netcdf-bin \
    libnetcdf-dev \
    software-properties-common \
&& rm -rf /var/lib/apt/lists/*

RUN add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable && apt update && apt upgrade -y

RUN pip install --upgrade pip
WORKDIR /code
COPY requirements_dev.txt /code/requirements_dev.txt
RUN pip install --use-wheel -r requirements_dev.txt
COPY requirements.txt /code/requirements.txt
COPY . /code
RUN pip install --use-wheel --editable /code/.[geo]
