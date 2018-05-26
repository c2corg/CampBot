# CampBot

Bot framework for camptocamp.org

## Installation

```batch
    pip install campbot
```

## Command line usage

### Export recent contribution

This command will load all contributions made in the last 24 hours

```batch
    campbot contribs
```

Optional arguments : 

* `-starts=2017-12-07` : will export all contributions after this date (included)
* `-ends=2017-12-07` : will export all contributions before this date (excluded)
* `--out=data.csv` : out file name, default value is `contributions.csv`


### Check and fix recent changes
Check that last day modifications pass these tests : 
  
* History is filled
* No big deletions
* And all patterns present in the first message of topic where report should be posted

```batch
campbot check_rc --login=<login> --password=<password> [--delay=<seconds>]
```
  
  
### Export data

Export to a csv file all documents given by camptocamp URL

```batch
campbot export <url>
```

<url> is a camptocamp url, like https://www.camptocamp.org/routes#a=523281



