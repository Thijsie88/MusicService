# using the latest Python image
FROM python:latest

# any working directory can be chosen as per choice like '/' or '/home' etc
WORKDIR /

# to COPY the remote file at working directory in container
COPY example-config ./config
COPY example-music ./music
COPY main.py ./
COPY requirements.txt ./

# install Python module requirements
RUN pip install -r requirements.txt

# update the enviroment
RUN apt-get update

# install ffmpeg, this is needed for .m4a/.mp4 to mp3 conversion
RUN apt-get install ffmpeg -y

# configure default environment variabels
# Python buffers it log output, this created a delayed output on the console
# to mitigate slow log ouput of the application, disable the buffer with:
ENV PYTHONUNBUFFERED=1
# by default the script will use 5, which means that the script will rerun every 5 minutes
# users can overrule the default by simply providing their own INTERVAL variable
ENV INTERVAL=5
# default format for saving files to, supports yt_dlp formatting
ENV FILEFORMAT="%(playlist)s/%(title)s-%(id)s.%(ext)s"
# default to true to upload files, can be overridden by users
ENV UPLOADFILES=true
# default to true to clean files, can be overridden by users
ENV CLEANFILES=true
# run the Music Service with Python
CMD [ "python", "./main.py"]