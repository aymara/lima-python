## 0.5.0b3 - 20221012

* More unit tests with several analyzers

## 0.5.0b2 - 20221012

* Unit tests with coverage at 100% for main API

## 0.5.0b1 - 20221006

* New API inspired by spaCy
  Most important parts of Lima (equivalent to Language), Doc, Span and Token are implemented.
* Complete model management API
* API documentation on readthedocs (https://lima-python.readthedocs.io/en/port-to-qt6/)
* Unit tests with coverage (currently 80%)

## 0.4.1 - 20220728

* abi3-based wheel usable on all python >= 3.7, < 4

## 0.4.0 - 20220720

* Switch to MIT license

## 0.3.5 - 20220217

* Make Lima class a callable which returns a PyCoNLL object
* analyzeText now returns a string to allow the use of dumpers other than the CoNLL one
* version number now centralized in a file

## 0.3.4 - 20220205

* Add meta parameter to API

## 0.3.3 - 20220205

* Named entities features in output
* Export and use user configuration
* Improve packaging process

## 0.3.2

* Named entities in UD languages

## 0.3.1

* Change API to allow separated config and resources user dirs

## 0.3.0

* First working C++ binding
