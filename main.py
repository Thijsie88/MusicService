from __future__ import unicode_literals
from re import L
from yt_dlp import YoutubeDL
import shutil
import requests
import os
import time
import sys
from pathlib import Path

class MyLogger(object):
    def debug(self, msg):   # print debug
        print(msg)
        #pass

    def warning(self, msg): # print warnings
        print(msg)
        #pass

    def error(self, msg):   # always print errors
        print(msg)

# shows progress of the downloads
def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')

file_format = str(os.getenv('FILEFORMAT')) or '%(playlist)s/%(title)s-%(id)s.%(ext)s'

print(file_format)

# Configure YouTube DL options
ydl_opts = {
    'writethumbnail': True,
    'no_write_playlist_metafiles': True,                            # do not save playlist data, like playlist .png
    'format': 'bestaudio[asr<=44100]/best[asr<=44100]/bestaudio',   # using asr 44100 as max, this mitigates exotic compatibility issues with certain mediaplayers, and allow bestaudio as a fallback for direct mp3s
    'postprocessors': [{    
        'key': 'FFmpegExtractAudio',                                # use FFMPEG and only save audio
        'preferredcodec': 'mp3',                                    # convert to MP3 format
        #'preferredquality': '192',                                 # with not specifying a preffered quality, the original bitrate will be used, therefore skipping one unnecessary conversion and keeping more quality
        },
        {'key': 'EmbedThumbnail',},                                     # embed the Youtube thumbnail with the MP3 as coverart.
        {
            'key': 'FFmpegMetadata',
            'add_metadata': True,
        },
    ],
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
    'outtmpl': './music/' + file_format,     # save music to the /music folder. and it's corrosponding folder which will be named after the playlist name
    'simulate': False,                                              # to dry test the YT-DL, if set to True, it will skip the downloading. Can be True/False
    'cachedir': False,                                              # turn off caching, this should mitigate 403 errors which are commonly seen when downloading from Youtube
    'download_archive': './config/downloaded',                      # this will update the downloads file which serves as a database/archive for which songs have already been downloaded, so it don't downloads them again
    'nocheckcertificates': True,                                     # mitigates YT-DL bug where it wrongly examins the server certificate, so therefore, ignore invalid certificates for now, to mitigate this bug
}

# reads and saves playlist URL's in a list
def getPlaylistURLs():
    with open('./config/playlists') as file:
        lines = [line.rstrip() for line in file]
    return(lines)

# downloads the playlists with the specified options in ydl_opts
def downloadPlaylists(ydl_opts, lines):
    with YoutubeDL(ydl_opts) as ydl:
                ydl.download(lines)

# creates directories in the cloud based on the local directory structure
def create_folders(localDirectory):
    
    # for every local directory create a directory at the users remote cloud directory
    for localDirectory, dirs, files in os.walk(localDirectory):
        for subdir in dirs:
            
            # construct URl to make calls to
            print(os.path.join(localDirectory, subdir))

            # remove first / from the string to correct the formatting of the URL
            formatRemoteDir = remoteDirectory[1:]

            fullurl = url + formatRemoteDir + "/" + subdir

            # first check if the folder already exists
            existCheck = requests.get(fullurl, auth=(username, password))

            # if the folder does not yet exist (everything except 200 code) then create that directory
            if not existCheck.status_code == 200:
                
            # create directory and do error handling, when an error occurs, it will print the error information and stop the script from running
                try:
                    r = requests.request('MKCOL', fullurl, auth=(username, password))
                    print("")
                    print(r.text)
                    print("Created directory: ")
                    print(r.url)
                    r.raise_for_status()
                except requests.exceptions.HTTPError as erra:           # handle 4xx and 5xx HTTP errors
                    print("HTTP Error: ",erra)
                    raise SystemExit(erra)  
                except requests.exceptions.ConnectionError as errb:     # handle network problems, DNS, refused connections
                    print("Error Connecting: ",errb)
                    raise SystemExit(erra)
                except requests.exceptions.Timeout as errc:             # handle requests that timed out
                    print("Timeout Error: ",errc)
                    raise SystemExit(erra)
                except requests.exceptions.TooManyRedirects as eerd:    # handle too many redirects, when a webserver is wrongly configured
                    print("Too many redirects, the website redirected you too many times: ")
                    raise SystemExit(eerd)
                except requests.exceptions.RequestException as erre:    # handle all other exceptions which are not handled exclicitly
                    print("Something went wrong: ",erre)
                    raise SystemExit(erre)
            
            # if directory exists print message that is exists and it will skip it
            else:
                print("Directory already exists, skipping: " + fullurl)

    print("Finished creating directories")

# after the neccessary directories have been created we can start to put the music into the folders
# iterates over files and uploads them to the corrosponding directory in the cloud
def upload_music(remoteDirectory):
    
    for root, dirs, files in os.walk(localDirectory):
        for filename in files:
            
            # get full path to the file (example: 'music/example playlist/DEAF KEV - Invincible [NCS Release].mp3')
            path = os.path.join(root, filename)
            
            # removes the first 6 characters "music/" from the path, beacause that piece of the path is not needed and should be ignored
            reduced_path = path[6:]

            # get the folder name in which the file is located (example: 'example playlist')
            subfoldername = os.path.basename(os.path.dirname(reduced_path))
            
            # remove first / from the string to correct the formatting of the URL
            formatRemoteDir = remoteDirectory[1:]

            # construct the full url so we can PUT the file there
            fullurl = url + formatRemoteDir + "/" + subfoldername + "/" + filename
            
            # first check if the folder already exists
            existCheck = requests.get(fullurl, auth=(username, password))
            
            # if the file does not yet exist (everything except 200 code) then create that file
            if not existCheck.status_code == 200:
            # error handling, when an error occurs, it will print the error and stop the script from running
                try:

                    # configure header, set content-type as mpeg and charset to utf-8 to make sure that filenames with special characters are not being misinterpreted
                    headers = {'Content-Type': 'audio/mpeg; charset=utf-8', }
                    
                    # make the put request, this uploads the file
                    r = requests.put(fullurl, data=open(path, 'rb'), headers=headers, auth=(username, password))
                    print("")
                    print(r.text)
                    print("Uploading file: ")
                    print(r.url)
                    r.raise_for_status()
                except requests.exceptions.HTTPError as erra:           # handle 4xx and 5xx HTTP errors
                    print("HTTP Error: ",erra)
                    raise SystemExit(erra)  
                except requests.exceptions.ConnectionError as errb:     # handle network problems, DNS, refused connections
                    print("Error Connecting: ",errb)
                    raise SystemExit(erra)
                except requests.exceptions.Timeout as errc:             # handle requests that timed out
                    print("Timeout Error: ",errc)
                    raise SystemExit(erra)
                except requests.exceptions.TooManyRedirects as eerd:    # handle too many redirects, when a webserver is wrongly configured
                    print("Too many redirects, the website redirected you too many times: ")
                    raise SystemExit(eerd)
                except requests.exceptions.RequestException as erre:    # handle all other exceptions which are not handled exclicitly
                    print("Something went wrong: ",erre)
                    raise SystemExit(erre)
            
            # if file exists print message that is exists and it will skip it
            else:
                print("File already exists, skipping: " + fullurl)
    
    print("Finished uploading music files")

# when the script makes it this far, all went good, and local MP3's can now be deleted
# when uploading the files is done, the local music folder should be cleared to save space
# this clears the local music folder so MP3's do not pile up locally, there is no point in storing them anymore since they have been uploaded to cloud storage already
def clear_local_music_folder():
    dir = './music/'
    for files in os.listdir(dir):
        path = os.path.join(dir, files)
        try:
            shutil.rmtree(path)
        except OSError:
            os.remove(path)
    print("Finished clearing local music directory")

if __name__ == '__main__':
    # get the OS enviroment variabels and save them to local variabels
    # these enviroment variabels get passed by the docker run command and default variables are passed through the Dockerfile
    localDirectory = 'music'                                   # 'music' always use music as local, this can't be changed at the moment, due to some hardcoding
    uploadFiles = str(os.getenv('UPLOADFILES')).lower()        # whether to upload files to 
    url = str(os.getenv('URL'))                                # WebDAV URL
    remoteDirectory = str(os.getenv('DIRECTORY'))              # WebDAV directory where you want to save your music
    username = str(os.getenv('USERNAME'))                      # WebDAV username
    password = str(os.getenv('PASSWORD'))                      # WebDAV password
    interval = int(os.getenv('INTERVAL'))*60                   # How often the the program should check for updated playlists, (did it times 60 to put it into seconds, so users can put it in minutes)
    cleanFiles = str(os.getenv('CLEANFILES')).lower()          # whether to clean files from music cache
    
    # welcome message
    print("Started Music Service")

    # print Python version for informational purposes
    print("Python version: "+ sys.version)

    # endless loop which will repeat every x minutes determined by the interval variable
    while True:
        print("")
        print("Fetching playlist URL's...")
        lines = getPlaylistURLs()
        print(lines)
        
        print("")
        print("Downloading playlists...")
        downloadPlaylists(ydl_opts, lines)

        print("")
        print('Creating cloud folder structure based on local directories...')
        create_folders(localDirectory)
        
        print("")
        if uploadFiles != 'false':
            print('Uploading music into the cloud folders...')
            upload_music(remoteDirectory)
        else:
            print('Uploading disabled via config.')
        
        print("")
        if cleanFiles != 'false':
            print("Clearing local MP3 files since they are no longer needed...")
            clear_local_music_folder()
        else:
            print('Clearing local files disabled via config.')
        
        # script will run again every x minutes based on user input (INTERVAL variable)
        # default is set to 5 minutes, users can put in whatever they like to overrule the defaulft value
        # if a user only wants to run the scripts one time (development purposes or whatnot) the number 0 can be used to do that
        print("")
        if not interval == 0:
            print("Music Service ran successfully")
            print("Run again after " + str(int(interval/60)) + " minute(s)")
            time.sleep(interval)
        else:
            print("Music Service ran one time successfully")
            print("Finished running Music Service")
            sys.exit()
