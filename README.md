Status "Master" branch:
[![Documentation Status](https://readthedocs.org/projects/xctools/badge/?version=master)](https://xctools.readthedocs.io/en/master/?badge=master) [![Build Status](https://travis-ci.org/ogosselet/xctools.svg?branch=master)](https://travis-ci.org/ogosselet/xctools)

Status "Dev" branch:
[![Documentation Status](https://readthedocs.org/projects/xctools/badge/?version=dev)](https://xctools.readthedocs.io/en/dev/?badge=dev) [![Build Status](https://travis-ci.org/ogosselet/xctools.svg?branch=dev)](https://travis-ci.org/ogosselet/xctools)

XCTools
-------

A set of python modules & class created to build applications around NOTAM & Airspace information.

The primary target is the paragliding community but other recreational flight activities might find our XCTools usefull.

XCTools are used in the backend of our website [FlyXC.Tools](http://www.flyxc.tools/) but are generic enough to be usefull for other type of application and services.

[Project documentation](https://xctools.readthedocs.io/en/latest/)

---

> **Disclaimer:** I am not a professional software developper. XCTools is an hobby project
> that allows me to learn more about Python and some of the development best practices out of personnal
> interrest. 
> I develop XCTools during my daily commute in the train.
> I am open for comments & contributions to improve the features and the quality of the project.

---

# Getting started

## Pulling down the container from Docker-hub

You can fetch the latest Docker container build like so (duration may vary with the available bandwidth):
```bash
docker pull flyxctools/xctools-cli
```
 

<a href="https://asciinema.org/a/232455?speed=2&autoplay=1&rows=20&cols=120" target="_blank"><img src="https://asciinema.org/a/232455.svg" height="300em;"/></a>

## Running the Docker container

Running the container will allow you to interact with the latest xctools version (always packed with container):
```bash
docker run -it flyxctools/xctools-cli /usr/bin/zsh
```


<a href="https://asciinema.org/a/232458?speed=2&autoplay=1&rows=20&cols=120" target="_blank"><img src="https://asciinema.org/a/232458.svg"  height="300em;"/></a>

