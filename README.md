# Recognizing off-sample mass spectrometry images with machine and deep learning

This repository is devoted to a computational project on recognizing so-called off-sample images in imaging mass spectrometry data. The project is carried out by the [Alexandrov team](https://www.embl.de/research/units/scb/alexandrov/) at EMBL Heidelberg. We used public data from [METASPACE](http://metaspace2020.eu) to create a gold standard set of ion images, as well as developed and evaluated several methods for recognizing off-sample ion images.

For more information, please see our recent paper [Ovchinnikova et al. (2020) BMC Bioinformatics](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-020-3425-x).

Team:
- [Katja Ovchinnikova](http://ovchinnikova.me/): biclustering and molecular co-localization method development, gold standard preparation
- [Vitaly Kovalev](https://github.com/intsco): deep learning method development
- [Lachlan Stuart](https://github.com/LachlanStuart): development of the TagOff web app
- [Theodore Alexandrov](https://www.embl.de/research/units/scb/alexandrov/members/index.php?s_personId=CP-60020464): supervision, gold standard preparation

## Creating gold standard ion images

### Using public METASPACE datasets

We used public datasets from [METASPACE](http://metaspace2020.eu), a community-populated knowledge base of metabolite images. Please see the section Acknowledgements acknowledging contributors of the used data.

### Web app for tagging ion images

TagOff was rapidly prototyped using the [METASPACE codebase](https://github.com/metaspace2020/metaspace/) as a foundation,
allowing its back-end, image display and annotation filtering to be reused.
The TagOff-specific changes can be found [in this commit range](https://github.com/metaspace2020/offsample/compare/0f772124...3ed8b524).

It can be run by [starting the METASPACE webapp](./TagOff/metaspace/webapp/README.md),
then navigating to http://localhost:8999/#/imageclassifier?db=HMDB-v4&user=your_name&max=10000&ds=2016-12-07_07h59m24s.
The querystring of the URL encodes the filter criteria used to select the annotations.
New criteria can be created and copied from [the Annotations page of METASPACE](https://metaspace2020.eu/annotations).
Two other parameters exist: `max` and `user`. `max` limits the number of annotations shown, and `user` accepts a name
which is added to the image labels, allowing multiple people to independently label the same image.

After annotations have been made, the data can be exported with:
```sh
sqlite3 -header -csv ./metaspace/webapp/imageclassification.sqlite "select * from imageclassifications" > ./metaspace/webapp/dist/results.csv
```

## Data

Copy and paste the commands below into a terminal  

### Gold standard ion images

To download and unpack an archive with the images
```
wget -qO - https://github.com/metaspace2020/offsample/releases/download/0.2/GS.tar.gz | tar -xvz
```

### Gold standard ion images predictions

To download and unpack an archive with the images grouped by a predicted class as well as predicted probabilities
```
wget -qO - https://github.com/metaspace2020/offsample/releases/download/0.2/gs_predictions.tar.gz | tar -xvz
```

### METASPACE knowledge base

```
wget -qO - https://s3-eu-west-1.amazonaws.com/sm-off-sample/pixel-annot-export-v0.10.tar.gz | tar -xvz
```

## CNN methods

We trained Convolutional Neural Networks using Fastai and PyTorch libraries.
The best performance we achieved using Resnet50 CNN pretrained on Imagenet. More details [here](CNN/README.md)

### Model REST API Implementation

The model was wrapped into a web service and deployed as a part of [Metaspace](https://metaspace2020.eu).
The service implementation is available on [GitHub](https://github.com/metaspace2020/metaspace/tree/master/metaspace/off-sample)

## DHB matrix clusters

We have generated DHB matrix clusters according to [(Keller and Li, 2000)](./DHB%20matrix%20clusters/Keller%20and%20Li%2C%202000.pdf). This resulted in 353 molecular formulas available [here](./DHB%20matrix%20clusters/DHB%20mc%20mol%20formulas%2C%20predicted.csv).

## Future steps

We are planning to integrate the best methods into [https://metaspace2020.eu](https://metaspace2020.eu).

## Citation
Would like to cite this project in a scientific publication? Please cite [Ovchinnikova et al. (2020) BMC Bioinformatics](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-020-3425-x).

## Acknowledgements

We thank the contributors of all public data to METASPACE and particularly those whose data was selected for the gold standard: Sarah Aboulmagd, Michael Becker, Dhaka Bhandari, Mark Bokhart, Berin Boughton, Shane Ellis, Mathieu Gaudin, Erin Gemperline, Cristina Gonzalez Lopez, Richard Goodwin, Anne Mette Handler, Bram Heijs, Sophie Jacobsen, Christian Janfelt, Emrys Jones, Patrik Kadesch, Pegah Khamehgir-Silz, Mario Kompauer, Lingjun Li, Manuel Liebeke, Michael Linscheid, James McKenzie, David Muddiman, Andrew Palmer, József Pánczél, Marina Reuter, Livia S. Eberlin, Veronika Saharuka, Marta Sans, Julian Schneemann, Kumar Sharma, Bernhard Spengler, Nicole Strittmatter, Zoltan Takats, Dusan Velickovic, Eric Weaver, Guanshi Zhang. The work was supported by the funding from the EU Horizon2020 project METASPACE (No. 634402), NIH NIDDK project KPMP, ERC Consolidator project METACELL (No. 773089).

## License

Unless specified otherwise in file headers or LICENSE files present in subdirectories, all files in this repository are licensed under the [Apache 2.0 license](LICENSE).
