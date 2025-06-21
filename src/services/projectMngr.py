"""
A small service that manages projects. For now this is just
pickling Song models. If complexity increases at least this
object will provide a place for the code to grow.
"""
import pickle
import marshal
import os
from typing import Dict, List, Tuple

from singleton_decorator import singleton
from PyQt6.QtCore import QObject, QSettings
from PyQt6.QtWidgets import QFileDialog, QWidget, QMessageBox

from view.events import Signals
from models.song import Song


@singleton
class ProjectManager(QObject):
    
    project_dir_key = "ProjectManager.project_dir"
    opened_projects_key = "ProjectManager.opened_projects_key"

    def on_load_settings(self, settings: QSettings):
        if settings.contains(self.project_dir_key):
            self.project_dir = settings.value(self.project_dir_key)

        if settings.contains(self.opened_projects_key):
            s = settings.value(self.opened_projects_key)
            self.opened_projects = marshal.loads(s)

    def on_save_settings(self, settings: QSettings):
        settings.setValue(self.project_dir_key, self.project_dir)
        s = marshal.dumps(self.opened_projects)
        settings.setValue(self.opened_projects_key, s)


    def save_as_dialog(self, song: Song):
        file_name, _ = QFileDialog.getOpenFileName(
            None,
            "Select a song name",
            self.project_dir,  # Initial directory (empty = current directory)
            "All Files (*);;"  # File filters
        )
        if len(file_name) > 0:
            try:
                with open(file_name, 'wb') as file:  
                    pickle.dump(song, file)
            except pickle.PickleError as e:
                errmsg = f"Error loading {file_name} " + str(e)
                QMessageBox.critical(
                    None,
                    "Error",
                    errmsg,
                    QMessageBox.StandardButton.Ok
                )
            finally:
                song.filename = file_name
                self.project_dir = os.path.dirname(file_name)
                self.opened_projects[song.title] = song.filename 

    def save_song(self, song: Song):
        if len(song.filename) > 0:
            with open(song.filename, 'wb') as file:  
                pickle.dump(song, file)
        else:
            self.save_as_dialog(song)

    def delete_song(self, song: Song):
        if os.access(song.filename, os.F_OK):
            if song.filename in self.opened_projects:
                del self.opened_projects[song.filename]
            os.remove(song.filename)

    def titles(self) -> List[str]:
        r = list(self.opened_projects.keys())    
        r.sort()
        return r

    def open_song_using_title(self, title) -> Song | None:
        file_name = self.opened_projects.get(title)   
        song = None 
        if file_name:
            song = self.open_song_using_filename(file_name)
        return song

    def open_song_using_filename(self, file_name) -> Song | None:
        errmsg = None
        song = None

        if not os.access(file_name, os.F_OK):
            errmsg = f"File {file_name} is inaccessible, please check permissions"
        else:
            try:
                # load saved work
                with open(file_name, 'rb') as file:  # 'rb' for reading in binary mode
                    song = pickle.load(file)
            except FileNotFoundError:
                errmsg = f"File {file_name} not found"
            except pickle.PickleError as e:
                errmsg = f"Error loading {file_name} " + str(e)
            
            if errmsg:
                QMessageBox.critical(
                    None,
                    "Error",
                    errmsg,
                    QMessageBox.StandardButton.Ok
                )
            else:
                assert(song)
                self.project_dir = os.path.dirname(file_name)
                self.opened_projects[song.title] = song.filename            

        return song

    def open_song_using_dialog(self, parent : QWidget | None = None) -> Song | None:
        "Use the QFileDialog to open and and load a saved song"
        song = None
        file_name, _ = QFileDialog.getOpenFileName(
            parent,
            "Select a Song Song",
            self.project_dir,  # Initial directory (empty = current directory)
            "All Files (*);;"  # File filters
        )
        if len(file_name) > 0:
            song = self.open_song_using_filename(file_name)

        return song
    
    
    def __init__(self):
        super().__init__()

        self.project_dir = os.environ['HOME'] + os.sep + 'Documents'
        # title -> filename
        self.opened_projects : Dict[str,str] = {}

        Signals.load_settings.connect(self.on_load_settings)
        Signals.save_settings.connect(self.on_save_settings)


