# Lipid Brain Atlas Explorer documentation 

<p align="center"><img src="readme/brain.gif" alt="animated" /></p>

## Overview

The Lipid Brain Atlas Explorer is a Python Dash web-application developped as part of the **Lipid Brain Atlas project**, led by the [Lipid Cell Biology lab (EPFL)](https://www.epfl.ch/labs/dangelo-lab/) and the [Laboratory of Brain Development and Biological Data Science (EPFL)](https://www.epfl.ch/labs/nsbl/). It is thought as a graphical user interface to assist the inspection and the analysis of a large mass-spectrometry dataset of lipids distribution at micrometric resolution across the entire mouse brain. We hope that this application will be of great help to query the Lipid Brain Atlas to guide your hypotheses and experiments, and more generally to achieve a better understanding of the cellular mechanisms involving lipids that are fundamental for nervous system development and function.

## Data

<p align="center"><img src="assets/ressources/data_acquisition.png" width="300" /></p>

To update

## Alignment to the Allen Brain Atlas

To update

<p align="center"><img src="assets/ressources/slice_cleaning.png" width="900" /></p>

## Use and deployment

The app is compatible with Python 3.8 and is guaranteed to work until version 3.9.5. 

Required packages can be installed with: 

```pip install -r requirements.txt```

Warning: The Dash version version MUST BE <=2.5.1, otherwise, bug may be present with long_callbacks.

The app can be run locally using the command:

```python main.py```

The first time the app is executed, if the shelve database (in the folder data/app_data/) doesn't exist, it will have to be built from scratch. This means that all the app precomputations will take place, which can take ~1 day of computation.

The app can be deployed on a server with Gunicorn (here with 4 threads and only 1 worker to avoid using too much RAM):

```gunicorn main:server -b:8077 --worker-class gevent --threads 4 --workers=1```

In both cases, it will be accesible with a browser at http://localhost:8077.



## Technical documentation

The technical documentation of the app is available [here](https://lbae-doc.epfl.ch/).




## Citing

If this app has been useful to your research work, you can cite our paper: XXX

## About

The app (frontend and backend) was developed by Colas Droin under the supervision of Gioele La Manno and Giovanni d'Angelo, as part of the Lipid Brain Atlas project. The final version was updated by Luca Fusar Bassini and Francesca Venturi.
