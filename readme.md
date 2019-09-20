# Libraries Course Lists 2.0

Brand new, redesigned course list handling for VAULT courtesy of Workday Student.

NOTE: this project is blocked by openequella/openEQUELLA#1192 since we cannot create data on taxonomy terms, which is a requirement for us (used in several places including in notification workflows). The project is still used to create fake "Informer" CSVs to feed into the old [cca/libraries_course_lists](https://github.com/cca/libraries_course_lists) scripts as well as to generate faculty LDAP group lists.

## Setup

```sh
> # make a python3 virtualenv & install dependencies
> virtualenv -p python3 .
> pip install -r requirements.txt
> # I use virtualfish though, so it's actually more like this
> vf new cl2
> pip install -r requirements.txt
```

## Usage

`python faculty_groups.py data/data.json` will create many text file lists of faculty usernames in the "data" directory. Each file is named after the LDAP group that the people belong to.

`python make_informer_csv.py data/data.json 2019FA` will create an "\_informer.csv" spreadsheet of course information, where data.json is the Workday JSON course information and 2019FA is the current semester's short code.

----

This is the main app, which isn't working yet due to the openEQUELLA bug.

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
