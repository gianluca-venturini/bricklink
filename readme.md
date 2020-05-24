## Bricklink optimization script
Optimize buying individual parts on Bricklink using Mixed Integer Programming.

## Load parts and listings from XML
python bricklink.py --load --parts data/tetresque.xml

## Optimize listings
python bricklink.py --optimize

## Insert in carts
python bricklink.py --buy --cart 1234