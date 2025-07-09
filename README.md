# UK Oil Pipeline

Pipeline created to extract the dataset "Supply and use of crude oil, natural gas liquids and feedstocks" from
https://www.gov.uk/government/statistics/oil-and-oil-products-section-3-energy-trends. The data is taken from the
"Quarters" tab in the source document.

## Installing
1. Download the repository from https://github.com/cathays/uk_oil_pipeline
2. Navigate to the save location of the repo and run ```python setup.py install```
3. This should install the package alongside the requirements of running the package

## Running
Installing this package allows use of the command ```runetl```. This package takes one argument, allowing the user to specify where to save the data. An example command to run the 
pipeline would be ```runetl C:\Users\Louis\Documents```. Do not include any trailing slashes in the argument.
