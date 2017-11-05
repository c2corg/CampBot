# CampBot

Bot framework for camptocamp.org

## Installation

```batch
    pip install campbot
```

## Command line usage

### Migrate BBCodes

```batch
   campbot remove_bbcode <ids_file> --login=<login> --password=<password> [--delay=<seconds>] [--batch]
```

* *ids_files :* path to a file thtat contains document's ids to migrate. Format is : 
```
id1 | w
id2 | r
```

* *batch :* do not ask confirmation before saving a document. Use very carefully
* *delay :* delay in second between each request. Defaut is 1 seconds.


  
### Check poll voters

Check that voters in a poll forum has at least one contribution during last 180 days

```batch
     campbot heck_voters <message_url> --login=<login> --password=<password>
```

<message_url> is the url of the massage that contains the poll you need to check



