# imagescan

I wrote this as a follow up to a previous script for selecting a random image from a directory.  That version worked 'enough', but was not perfect.  I updated this version to support additional actions from the CLI, and with a SQLITE backend to allow for more robust queries and persistence between runs.

  scan        - Scans the directory and subdirectoriese for all image types (JPG, JPEG, PNG) and inserts them into the database.  
                This will not create duplicate entries, so can be run as often as you want.
                
  show        - Show all the files in the database
  
  show FILTER - Show all the files in the database that either the path or filename match the FILTER word
  
  duplicates  - Show all the files in the database where the hash matches another file's hash.  
  
  prune       - Search the database and test every file to see if it still exists.  WARNING: the larger your database, the slower it is
  
  purge       - Delete all files in the database.  You get one chance to not fuck up, be warned.  

