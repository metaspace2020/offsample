# Recognizing off-sample mass spectrometry images with Convolutional Neural Networks

## Requirements

* Ubuntu >= 14.04
* Conda >= 4.5.11
* Ideally Nvidia GPU

## Setup

* Clone repository
* Create conda environment

```
cd CNN
conda env create -n offsample-fastai --file fastai-env.yml
conda activate offsample-fastai
```

* If Jupyter is already installed add a new kernel

```
python -m ipykernel install --user --name offsample-fastai --display-name "offsample-fastai"
```

* Otherwise install Jupyter into the environment.

## Run

* Start Jupyter and open `train_fastai_on_gs.ipynb`

## Pretrained Model

A model pretrained with [fastai](https://docs.fast.ai) library is provided on the
[release page](https://github.com/metaspace2020/offsample/releases/tag/0.1)
under `model.fai` name