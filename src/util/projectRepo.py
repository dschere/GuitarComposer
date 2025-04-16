"""
Simple managment scheme for projects for GC.

<home>/GuitarComposerUserdata
      /GuitarComposerUserdata/songs/<title>.dat
      /GuitarComposerUserdata/live-capture/<name>/
       audio capture
"""
import os
import glob
from singleton_decorator import singleton
import pickle
import logging

from models.song import Song
from models.track import Track

USER_DIR = os.environ['HOME']+"/GuitarComposerUserdata"
USER_SONG_DIR = USER_DIR+"/songs"
USER_LIVE_CAPTURE_DIR = USER_DIR+"/live-capture"


@singleton
class ProjectRepo:
    def __init__(self):
        if not os.access(USER_DIR, os.F_OK):
            os.mkdir(USER_DIR)
            os.mkdir(USER_SONG_DIR)
            os.mkdir(USER_LIVE_CAPTURE_DIR)

        self.titles = set()
        for songpath in glob.glob(USER_SONG_DIR+"/*.data"):
            title = songpath.split("/")[-1][:-len(".data")]
            self.titles.add(title)

        self.song_selected = None 
        self.track_selected = None 

    def set_current_song(self, s: Song): 
        self.song_selected = s 

    def get_current_song(self):
        return self.song_selected 
    
    def set_current_track(self, t: Track):
        self.track_selected = t

    def get_current_track(self):
        return self.track_selected     

    def getTitles(self):
        return self.titles

    def load_song(self, title: str):
        fn = USER_SONG_DIR+"/"+title+".data"
        return pickle.loads(open(fn, 'rb').read())

    def delete_song(self, title):
        if title in self.titles:
            fn = USER_SONG_DIR+"/"+title+".data"
            if os.access(fn, os.F_OK):
                os.remove(fn)
                self.titles.remove(title)
            else:
                logging.info(f"{fn} does not exist")
        else:
            logging.info("title '%s' not in %s" % (title, str(self.titles)))

    def save_song(self, song_model: Song):
        fn = USER_SONG_DIR + "/" + song_model.title + ".data"
        data = pickle.dumps(song_model)
        open(fn, 'wb').write(data)


if __name__ == '__main__':
    pr = ProjectRepo()
    s = Song()
    s.title = "noname"
    pr.delete_song(s.title)
    if s.title not in pr.getTitles():
        pr.save_song(s)
        t = pr.load_song(s.title)
        assert (t.title == s.title)
        pr.delete_song(s.title)
        assert (s.title not in pr.getTitles())
