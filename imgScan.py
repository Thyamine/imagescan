import os
from os import path

import sys
import PIL
from PIL import Image
from PIL import ExifTags

import hashlib
import sqlite3
from sqlite3 import Error
from sqlite3 import IntegrityError

# Globals
depth = 0

dbFile = "./photos.db"
#imgDir = "/Volumes/files/GoogleDrive/Pictures/# Test"
imgDir = "/Users/USERNAME/Pictures"

conn =  None 

# *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***
#
# Database Commands
# 
# *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***
def create_connection(db_file):
    # create a database connection to a SQLite database     
    try:
        # If the database doesn't exist, create it, the main table, and the indices 
        if not os.path.isfile(db_file):            
            table = "CREATE TABLE 'images' ('hash' TEXT, 'path' TEXT, 'filename' TEXT, 'width' INTEGER, 'height' INTEGER, 'orientation' INTEGER, PRIMARY KEY('path','filename')) "

            index1 = 'CREATE INDEX "i_" ON "images" ("hash"	ASC)'
            index2 = 'CREATE INDEX "i_path" ON "images" ("path"	ASC,"filename"	ASC,"orientation"	ASC)'
            
            print ("New table!")
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute (table)
            conn.commit()
            
            print ("New indices!")
            cursor.execute(index1)
            cursor.execute(index2)
            conn.commit()
            conn.close()
            print ("Closed!")
            # End of Creation
            
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        return conn
        
    except Exception as e:
        print(e)

def insertImage(theHash, thePath, theFilename, theWidth, theHeight, theOrientation):
    global conn
    
    try:
        myImage = (theHash, thePath,theFilename, theWidth, theHeight, theOrientation)
        
        #sql = "insert into images (hash, path, filename, width, height, orientation) values ('" + theHash + "','" + thePath + "','" + theFilename + "'," + str(theWidth) + "," + str(theHeight) + ",'" + theOrientation + "')"
        sql = "insert into images values (?,?,?,?,?,?)"
        #print (" --", myImage)
        #print (" --", sql)
        
        cur = conn.cursor()
        cur.execute(sql, myImage)

        print (" -- Insert Image.")
        
        return 0
    except IntegrityError as e:
        print (" -- Database entry already exists.")
    except Exception as e:
        print(e)
        
def fetchAllImages(filter):
    global conn
    
    try:
        print (" -- Fetching All Images.")
        where = ""
        
        if filter != "":
            where = "where path like '%" + filter + "%' or filename like '%" + filter + "%' "
        
        sql = "select * from images " + where + "order by path, filename"
        
        cur = conn.cursor()
        images = cur.execute(sql)
        
        return images
    except Exception as e:
        print(e)
        
def fetchDuplicates():
    global conn
    
    try:
        print (" -- Searching for duplicate images in the system.")
        
        sql = "select t1.hash, totals, i.path, i.filename from (select hash, count(hash) as totals from images group by hash ) t1 left join images i on t1.hash = i.hash where t1.totals > 1 order by totals desc"
        cur = conn.cursor()
        images = cur.execute(sql)
        
        return images
    except Exception as e:
        print (e)
        
def fetchRandomImage(thePath):
    global conn
    
    try:
        if path == "":
            sql = "select randomFile from (select  path || '/' || filename as randomFile, random() as randomID from images) t1 order by randomID limit 1"
        else:
            sql = "select randomFile from (select  path || '/' || filename as randomFile, random() as randomID from images where path like '" + thePath + "%') t1 order by randomID limit 1"

        cur = conn.cursor()
        theFile = cur.execute(sql)

        return theFile
    except Exception as e:
        print (e)

    
def deleteImage(thePath, theFilename):
    global conn
    
    try:
        myImage = (thePath, theFilename)
        sql = "delete from images where path = ? and filename = ?"
        cur = conn.cursor()
        cur.execute(sql, myImage)
        
        print (" -- Deleted Image.")
        
        return 0
    except Exception as e:
        print (e)
        
def purgeAllImages():
    global conn
    
    try:
        sql = "delete from images"
        cur = conn.cursor()
        cur.execute(sql)
        
        print (" -- All images deleted.")
    except Exception as e:
        print (e)
            
# *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***
#
# Image Commands
#
# *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***

#
# img: the image object we want to inspect and manipulate
#
def correctRotation(img):
    #
    # Check orientation, and rotate if needed
    # This looks for EXIF data in the file and determines if the camera was rotated when the picture was taken
    # This can throw off the check we do for portrait vs landscape
    # 
    for orientation in ExifTags.TAGS.keys() : 
        if ExifTags.TAGS[orientation]=='Orientation' : break 

    try:
        exif=dict(img._getexif().items())

        if   exif[orientation] == 3 : 
            img=img.rotate(180, expand=True)
            #print(' -- 180')
        elif exif[orientation] == 6 : 
            img=img.rotate(270, expand=True)
            #print(' -- 270')
        elif exif[orientation] == 8 : 
            img=img.rotate(90, expand=True)
            #print(' -- 90')
        #else:
            #print(' -- 0')
    except:
        print(" -- File contains no EXIF data.")
    
    return img

def getHash(path):
    fileHash = hashlib.sha256()
    BLOCK_SIZE = 65536
    
    with open(path, 'rb') as f: # Open the file to read it's bytes
        fb = f.read(BLOCK_SIZE) # Read from the file. Take in the amount declared above
        while len(fb) > 0: # While there is still data being read from the file
            fileHash.update(fb) # Update the hash
            fb = f.read(BLOCK_SIZE) # Read the next block from the file  
    return fileHash.hexdigest()

def imageOrientation(img):
    orientation = ""
    
    w,h = img.size
    if h > w:
        orientation = "portrait"
    elif w > h:
        orientation = "landscape"
    elif h == w:
        orientation = "square"
        
    return orientation
    

def insertNewImagesIntoDatabase(directory):
    global depth
    
    dirList = os.listdir(directory)
    dirList.sort()

    pad = " "
    pad = pad.rjust(depth + 1, "-")
    
    for file in dirList:
        currentDirectory = ""
        
        # Recursive if needed
        fullFilePath = directory + "/" + file
        
        if os.path.isdir(directory + "/" + file):
            print("\n\n" + directory + "/" + file)
            depth = depth + 1
            insertNewImagesIntoDatabase(directory + "/" + file)
            depth = depth - 1
        
        # Process the file
        filename = os.fsdecode(file)
        filename = filename.upper()
        
        if filename.endswith(".GIF") or filename.endswith(".JPG") or filename.endswith(".JPEG") or filename.endswith(".PNG"): 

            img = Image.open(fullFilePath)
            img = correctRotation(img)
            w,h = img.size
            
            theHash = getHash(directory + "/" + file)
            theOrientation = imageOrientation(img)
        
            #print(pad + filename + " :: " + theHash + " :: " + str(w) + " x " + str(h) + " :: " + theOrientation)            
            insertImage(theHash, directory, filename, w, h, theOrientation)
            
            continue
        else:
            continue
            
def deleteOldImagesFromDatabase(directory):
    images = fetchAllImages()

    pad = " "
    pad = pad.rjust(depth + 1, "-")
    
    for image in images:
        # Recursive if needed
        fullFilePath = image[1] + "/" + image[2]

        if path.isfile(fullFilePath):
            print (" --", fullFilePath, " exists.")
        else:
            print (" --", fullFilePath, " is missing.  Purging from database.")
            deleteImage(image[1], image[2])
            
def printImages(images):
    print ("\n\nFilename, Width x Height, Orientation, Hash")
    
    currentDirectory = ""
    
    for image in images:
        if currentDirectory != image[1]:
            currentDirectory = image[1]
            print (image[1])
            
        print (" --", image[2], str(image[3]) + "x" + str(image[4]), image[5], image[0])
        
def printDuplicates(images):
    print ("\n\nFilename, Width x Height, Orientation, Hash")
    
    currentHash = ""
    
    for image in images: 
        if currentHash != image[0]:
            currentHash = image[0]
            print ("\n" + currentHash)
            
        print (" --", image[1], image[2], image[3])
       

# *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***
#
# MAIN
#
# *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***

if __name__ == '__main__':
    try:
        conn = create_connection(dbFile)
        cursor = conn.cursor()
        
        if len(sys.argv) <= 1:
            print ("\n\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
            print ("\n         Image Database v1\n")
            print ("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
            print ("\n")
            print ("The following parameters for the script will let you control what it does:")
            print ("  scan        - Scans the directory and subdirectoriese for all image types (JPG, JPEG, PNG) and inserts them into the database.  \n                This will not create duplicate entries, so can be run as often as you want.")
            print ("  show        - Show all the files in the database")
            print ("  show FILTER - Show all the files in the database that either the path or filename match the FILTER word")
            print ("  duplicates  - Show all the files in the database where the hash matches another file's hash.  ")
            print ("  prune       - Search the database and test every file to see if it still exists.  WARNING: the larger your database, the slower it is")
            print ("  purge       - Delete all files in the database.  You get one chance to not fuck up, be warned.  ")
            print ("\n\n")

        else:
            scriptAction = sys.argv[1]
            
            if scriptAction == "scan":
                print ("\n\nUpdating the database from the file system.")
                insertNewImagesIntoDatabase(imgDir)
                conn.commit()
                
            elif scriptAction == "show":
                images = ""
                
                if len(sys.argv) == 3:
                    images = fetchAllImages(sys.argv[2])
                else:
                    images = fetchAllImages("")
                    
                printImages(images)
                
            elif scriptAction == "random":
                images = ""
                
                if len(sys.argv) == 3:
                    image = fetchRandomImage(sys.argv[2])
                else:
                    image = fetchRandomImage("")
                    
                for i in image:
                    print (i[0])
                    
            elif scriptAction == "duplicates":
                print ("\n\nSearching the database for duplicates.")
                images = fetchDuplicates()
                
                printDuplicates(images)
                
                conn.commit()
                
            elif scriptAction == "prune":
                print ("\n\nPruning the database.")
                deleteOldImagesFromDatabase(imgDir)
                conn.commit()

            elif scriptAction == "purge":
                print ("\n\nDeleting all images from the database.")
                ask = input("Are you sure you want to delete all entries in the database? (yes/no)")
                if ask == "yes":
                    purgeAllImages()
                else:
                    print (" -- Action cancelled.")
                conn.commit()
        
    except Exception as e:
        print (e)
        
    finally:
        conn.close()

    
    
            