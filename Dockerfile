FROM ubuntu:xenial

MAINTAINER lars.claussen <lars.claussen@nelen-schuurmans.nl>

# Change the date to force rebuilding the whole image
ENV REFRESHED_AT 2018-03-02

# system dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
&& add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable \
&& apt-get update && apt-get install -y \
   curl \
   git \
   libhdf5-serial-dev \
   libnetcdf-dev \
   netcdf-bin \
   python-dev \
   python-gdal \
&& rm -rf /var/lib/apt/lists/*

# There are issues with upgrading python-pip managed by apt.
RUN curl -s https://bootstrap.pypa.io/get-pip.py | python

WORKDIR /code
COPY requirements* /code/
RUN pip install -r requirements.txt
RUN pip install -r requirements_dev.txt
COPY . /code/
RUN pip install --editable .[geo,results]
