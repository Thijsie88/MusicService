# schedule stuff
import schedule
import time
from downloadMusic import downloadmusic

# function which will keep an interval time for each playlist/song in the background
# this will be used to check if the playlist/song needs to be downloaded again
# if the interval time has passed, then the playlist/song will be downloaded again
# this will be used to keep the music up to date
# this only schedules jobs for playlists that already exist in the database on boot
def scheduleJobs(Music):
    # get all the playlists/songs
    music_list = Music.query.all()

    # iterate over the playlists/songs
    for music in music_list:
        # get the interval value for each playlist/song
        interval = music.interval

        # https://github.com/dbader/schedule
        # https://schedule.readthedocs.io/en/stable/
        schedule.every(interval).minutes.do(downloadmusic,music.id).tag(music.id)
        print("Interval set for:", music.title, interval, "minutes")

    print('here are all jobs', schedule.get_jobs())

# schedule jobs for newly added playlists/songs
def scheduleNewJobs(music_id, title, interval):
    # get the data for the newly added playlist/song
    #newPlaylistData = Music.query.filter_by(id=music_id).first()
    # get the interval value for the newly added playlist/song
    #interval = newPlaylistData.interval
    # schedule the job for the newly added playlist/song
    schedule.every(interval).minutes.do(downloadmusic,music_id).tag(music_id)
    print("Interval set for:", title, interval, "minutes")

# delete scheduled jobs when they are no longer needed
def deleteJobs(music_id):    
    schedule.clear(music_id)
    print("Deleted job for:", music_id)

# this functions runs in a seperate thread to monitor scheduled jobs and run them when needed
def run_schedule(app_context):
    app_context.push()
    # run the schedule in the background
    while True:
        schedule.run_pending()
        time.sleep(1)