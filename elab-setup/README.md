Elab Machine and Instance Preparation Scripts
=============================================

This directory contains two scripts for preparing a new Ubuntu machine to be
ready for deploying E-Labsheet instances with Nginx web server and gunicorn.

* Run `./prepare-machine.sh` as root to install all necessary software packages
* Run `./prepare-instance.sh` to create a set of scripts and instructions for
  deploying a new instance of e-Labsheet.

Both scripts accept the `--docker` option for creating Docker images.
(See the [elab-docker project](https://gitlab.com/cjaikaeo/elab-docker).)