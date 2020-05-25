## Bricklink optimization script
Optimize buying individual parts on Bricklink using Mixed Integer Programming.

## Load parts and listings from XML
python bricklink.py --load --parts data/tetresque.xml

### Exluded parts
if a part should not be present you can use `--exclude` e.g. `--exclude 3706,86,1`

## Optimize listings
python bricklink.py --optimize

## Insert in carts
python bricklink.py --buy --cart 1234