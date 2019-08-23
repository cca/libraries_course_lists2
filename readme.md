# Libraries Course Lists 2.0

Brand new, redesigned course list handling for VAULT courtesy of Workday Student.

## Setup

```sh
> # make a python3 virtualenv & install dependencies
> virtualenv -p python3 .
> pip install -r requirements.txt
```

## Usage

```
usage: app.py [-h] [-c] [--course-lists] [-d] file

Create VAULT taxonomies from JSON course data.

positional arguments:
  file                 course list JSON file

optional arguments:
  -h, --help           show this help message and exit
  -c, --clear          only clear the given semester taxonomy term, do not
                       create new terms
  --course-lists       only create terms in course list taxonomies, ignore
                       others
  -d, --downloadtaxos  download fresh taxonomies from VAULT (do not use JSON
                       list in /data dir)
```

The taxonomies JSON is stored in data/taxonomies.json. If you create a new taxonomy related to course lists or course information, you'll need to rerun `python app.py --downloadtaxos` to refresh the JSON.

## LICENSE

[ECL Version 2.0](https://opensource.org/licenses/ECL-2.0)
