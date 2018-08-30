FROM ubuntu:xenial

MAINTAINER lars.claussen <lars.claussen@nelen-schuurmans.nl>

# Change the date to force rebuilding the whole image.
ENV REFRESHED_AT 2018-03-02

# Add ubuntugis PPA. A recent GDAL version is required by the GPKG driver.
RUN apt-get update && apt-get install -y software-properties-common \
&& add-apt-repository -y ppa:ubuntugis/ppa \
&& rm -rf /var/lib/apt/lists/*

# System dependencies.
RUN apt-get update && apt-get install -y \
    curl \
    libhdf5-serial-dev \
    libnetcdf-dev \
    netcdf-bin \
    python-dev \
&& rm -rf /var/lib/apt/lists/*

# Avoid issues with upgrading an apt-managed pip.
RUN curl -s https://bootstrap.pypa.io/get-pip.py | python

WORKDIR /code
COPY requirements* /code/
RUN pip install -r requirements.txt
RUN pip install -r requirements_dev.txt
COPY . /code/
RUN pip install --editable .[geo,results]
