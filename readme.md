# Libraries Course Lists 2.0

Brand new, redesigned course list handling for VAULT courtesy of Workday Student. The app creates an ORM of sorts around the openEQUELLA APIs, with objects for Groups, Taxonomies, and Taxonomy Terms, that lets us manipulate data easily.

## Setup

1. Set up a python virtual environment & install dependencies (requests)

```sh
> pipenv --three
> pipenv shell
> pipenv install
```

1. Obtain a VAULT OAuth token for API use, copy example.config.py to config.py, then add the token to it. You can also change the logging configuration here if you so choose.

1. Obtain access to CCA Integrations data in Google Cloud (contact Integration Engineer). There should be JSON files present for employees, students, and courses for current semesters.

## Usage

The main app should work now but has yet to be used to create taxonomies in VAULT. Thus far only unit tests have been performed.

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

The taxonomies JSON is stored in data/taxonomies.json (not all their terms, just taxonomy names and identifiers). If you create a new taxonomy related to course lists or course information, e.g. if a new academic program is created, you'll need to rerun `python app.py --downloadtaxos` to refresh the JSON.

`python faculty_groups.py data/data.json` will create many text file lists of faculty usernames in the "data" directory. Each file is named after the LDAP group that the accounts belong to.

`python make_informer_csv.py data/data.json 2019FA` will create an "\_informer.csv" spreadsheet of course information, where data.json is the Workday JSON course information and "2019FA" is the current semester's short code. We can deprecate this script once the main app is in use.

## Testing

```sh
> pipenv run cover # run tests
> pipenv run report # coverage report
> coverage html # generate HTML in htmlcov/ that shows which lines aren't tested
```

Add tests to the "test" folder and name them like "test_FILENAME" where FILENAME is roughly the name of the module that's being tested. This ensures `unittest` can discover them and makes it easier to see what tests still need to be written. You may need to create fixtures in both VAULT and the local filesystem to write some tests. Prefer using a fake, created datum to testing against production data that naturally changes.

## LICENSE

[ECL Version 2.0](https://opensource.org/licenses/ECL-2.0)
