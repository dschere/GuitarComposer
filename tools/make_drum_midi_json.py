# Data source.
# https://musescore.org/sites/musescore.org/files/General%20MIDI%20Standard%20Percussion%20Set%20Key%20Map.pdf

# Key# Note Drum Sound
raw_data = """35 B0 Acoustic Bass Drum    
59 B2 Ride Cymbal 2
36 C1 Bass Drum 1           
60 C3 Hi Bongo
37 C#1 Side Stick           
61 C#3 Low Bongo
38 D1 Acoustic Snare        
62 D3 Mute Hi Conga
39 Eb1 Hand Clap            
63 Eb3 Open Hi Conga
40 E1 Electric Snare        
64 E3 Low Conga
41 F1 Low Floor Tom         
65 F3 High Timbale
42 F#1 Closed Hi-Hat        
66 F#3 Low Timbale
43 G1 High Floor Tom        
67 G3 High Agogo
44 Ab1 Pedal Hi-Hat         
68 Ab3 Low Agogo
45 A1 Low Tom               
69 A3 Cabasa
46 Bb1 Open Hi-Hat          
70 Bb3 Maracas
47 B1 Low-Mid Tom           
71 B3 Short Whistle
48 C2 Hi Mid Tom            
72 C4 Long Whistle
49 C#2 Crash Cymbal 1       
73 C#4 Short Guiro
50 D2 High Tom              
74 D4 Long Guiro
51 Eb2 Ride Cymbal 1        
75 Eb4 Claves
52 E2 Chinese Cymbal        
76 E4 Hi Wood Block
53 F2 Ride Bell             
77 F4 Low Wood Block
54 F#2 Tambourine           
78 F#4 Mute Cuica
55 G2 Splash Cymbal         
79 G4 Open Cuica
56 Ab2 Cow Bell              
80 Ab4 Mute Triangle
57 A2 Crash Cymbal 2        
81 A4 Open Triangle"""

midi_drum_groups = {
    "Bass": [],
    "Cymbal": [],
    "Conga": [],
    "Tom": [],
    "Snare": [],
    "Hi-Hat": [],
    "Block": [],
    "Triangle": [],
    "Guiro": [],
    "Agogo": [],
    "Bell": [],
    "Cuica": [],
    "Timbale": [],
    "Bongo": [],
    "Misc": []
}

for line_tokens in [line.split() for line in raw_data.split("\n")]:
    midi_code = int(line_tokens[0])
    desc_tokens = line_tokens[2:]
    item = [midi_code, " ".join(desc_tokens)]
    found = False
    for group_name, item_list in midi_drum_groups.items():
        if group_name in desc_tokens:
            item_list.append(item) # type: ignore
            found = True
            break
    if not found: 
       midi_drum_groups["Misc"].append(item)

import json

text = json.dumps(midi_drum_groups, sort_keys=True, indent=4)
print(text)