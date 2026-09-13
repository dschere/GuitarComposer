![Project Screenshot](doc/images/app.png)

# GuitarComposer
Music composition application  

Guitar Composer is a music composition software aimed at guitar players. Its ultimate goal is to provide per track and event per note effects using a full featured filter graph. The ability to blend different instruments to mimic the polyphonic nature of the guitar in which you can play the same note using different strings to provide color for the notes. GC has the ability to create virtual guitars in which combinations of instruments are assigned to each string, such as making the high E string be a combination of 20% orchestral harp, 10% bell and 70% steel string guitar. 

## Current state

Although 0.1.0 some basic functionality exists: 

- A synth which I reworked from the TingSoundFount library https://github.com/schellingb/TinySoundFont to add per track sound effects using a filter graph that allows for arbitrary ladspa effects to be combined in a audio graph.
![Project Screenshot](doc/images/filter-graph.png)

- It has a preview screen (An idea I got from TuxGuitar) where the user can test out presets and see scales.
![Project Screenshot](doc/images/fretboard-scales.png)

- A directory explorer. Each piece of music is represented as a tree structure. with read track being a branch and a song being a collection of branches. 

- A music editor that is keyboard centric like a MS-Work document (Control-C/V/X copy-paste) the user edits tablature and notes appear on the staff.
![Project Screenshot](doc/images/editor.png)

- Toolbar that controls dynamic, duration etc. This can also be controlled by the keyboard.   

There are bugs at this stage of development. As a solo project I will work the best I can to fix bugs but I have a day job. 

# Editor

The goal of the tablature editor is to work more or less like MS-word. The user navigates a cursor that edits the tab. The keyboard can be used to set the duration and velocity of the notes. Numbers 0-9 are used to enter the fret number for the string.   

|keycode     |name          |type        | description                                                      |
|------------|--------------|------------|------------------------------------------------------------------|
|<space bar> |Rest          | rest       | Music rest set the current diration                              |
|0-9         |Fret Number   | note       | Sets the a number 0-24 in tablature and staff note               |
|w           |Whole Note    | duration   | after pressed all notes/rests are whole duration                 |
|h           |Half Note     | duration   | after pressed all notes/rests are half duration                  | 
|q           |Quarter Note  | duration   | after pressed all notes/rests are quarter duration               | 
|e           |Eight Note    | duration   | after pressed all notes/rests are eight duration                 | 
|s           |16th Note     | duration   | after pressed all notes/rests are 16th duration                  | 
|T           |32nd Note     | duration   | after pressed all notes/rests are 32nd duration                  | 
|S           |64th Note     | duration   | after pressed all notes/rests are 64th duration                  | 
|.           |dotted        | duration   | dotted note/rest add 50% to current duration                     |
|;           |double dotted | duration   | dotted note/rest add 75% to current duration                     | 
|Control-Z   |undo          | state      | undo last action                                                 |
|Control-Y   |redo          | state      | redo last action                                                 |
|Control-C   |copy          | state      | copy selection, use control -> or <- to select notes/rests first |
|Control-V   |paste         | state      | paste selection                                                  |
|Control-V   |cur           | state      | cur selection                                                    |
| \[         |open repeat   | repeat     | toggle starting measure open repeat                              |
| \]         |close repeat  | repeat     | toggle end end repeat numberic control used to number repaats    |
| p,m,f      |dynamic       | dynamic    | Typing p,m,f to spell out dynamics  fff,ff,f,mf,mp,p,pp,pp       |



# filter graph 


## Installation, build and run

- source venv/bin/activate
- pip install -r requirements.txt
- ./setup.py build
- ./setup.py install
- python -m guitar_composer.app 

