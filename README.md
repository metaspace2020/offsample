# Recognizing off-sample mass spectrometry images

This repository is devoted to a computational project on recognizing off-sample images in the field of imaging mass spectrometry. The project is carried out by the [Alexandrov team](https://www.embl.de/research/units/scb/alexandrov/) at EMBL Heidelberg. We used public data from [METASPACE](http://metaspace2020.eu) to create a gold standard set of ion images, as well as developed and evaluated several methods for recognizing off-sample ion images.

Team:
- [Katja Ovchinnikova](http://ovchinnikova.me/): gold standard preparation, method development
- [Vitaly Kovalev](https://github.com/intsco): CNN and DL method development
- [Lachlan Stuart](https://github.com/LachlanStuart): web development
- [Theodore Alexandrov](https://www.embl.de/research/units/scb/alexandrov/members/index.php?s_personId=CP-60020464): supervision

## Creating gold standard ion images

### Using public METASPACE datasets

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

### Gold standard

The images can be downloaded from AWS S3
```sh
wget https://s3-eu-west-1.amazonaws.com/sm-off-sample/GS.tar.gz
tar -xf GS.tar.gz
```

## CNN methods

We trained Convolutinal Neural Networks using Fastai and PyTorch libraries.
The best performance we achieved using Resnet50 CNN pretrained on Imagenet.

## DHB matrix clusters

We have generated DHB matrix clusters according to [(Keller and Li, 2000)](./DHB%20matrix%20clusters/Keller%20and%20Li%2C%202000.pdf). This resulted in 353 molecular formulas available [here](./DHB%20matrix%20clusters/DHB%20mc%20mol%20formulas%2C%20predicted.csv).

## Future steps

We are planning to integrate the best methods into [https://metaspace2020.eu](https://metaspace2020.eu).

## Acknowledgements

TODO: Acknowledging the users contributed the public datasets used in this project

## License

Unless specified otherwise in file headers or LICENSE files present in subdirectories, all files in this repository are licensed under the [Apache 2.0 license](LICENSE).
