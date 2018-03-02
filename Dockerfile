FROM ubuntu:xenial

MAINTAINER lars.claussen <lars.claussen@nelen-schuurmans.nl>

# Change the date to force rebuilding the whole image
ENV REFRESHED_AT 2018-03-02

# system dependencies
RUN apt-get update && apt-get install -y \
    git \
    python-pip \
    python-gdal \
&& rm -rf /var/lib/apt/lists/*

RUN pip install -U pip
WORKDIR /code
COPY requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt
COPY . /code
