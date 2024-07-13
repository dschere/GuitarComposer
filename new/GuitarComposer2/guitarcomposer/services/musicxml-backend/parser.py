import xml.etree.ElementTree as ET
import sys

from guitarcomposer.model.instrument import instrument
from guitarcomposer.model.track import track as track_model
import  guitarcomposer.model.track_events as tevt

class MusicXmlParser:

    def _get_part_list(self, root):
        """ return a list of instrumments used for the score """
        part_list_node = root.find('part-list')
        score_parts = part_list_node.findall('score-part')
        parts_map = {}

        for score_part in score_parts:
            ins = instrument(
                id = score_part.attrib['id'],
                pgm = score_part.find('midi-instrument').find('midi-program').text,
                name = score_part.find('score-instrument').find('instrument-name').text
            )
            parts_map[ins.id] = ins
        return parts_map
    
    def _get_tuning(self, root, parts_map):
        "get the tuning from the first measure of each part"
        parts = root.findall('part')
        tracks = {}
        for part_node in parts:
            part_id = part_node.attrib['id']
            track = track_model(id=part_id)
            track.ins = parts_map[part_id]
            tuning_nodes = part_node.findall('measure')[0].find('attributes').find('staff-details').findall('staff-tuning')
            for t_node in tuning_nodes:
                str_num = int(t_node.attrib['string'])
                midi_val = int(t_node.attrib['midiCode'])
                track.tuning[str_num] = midi_val 
            tracks[track.id] = track
        return tracks    
    
    def _get_linear_measures(self, part_node):
        """walk through a list of measure nodes and
           unrevel all the repeat loops so we have measures
           in a single vector. 
        """
        measures = part_node.findall('measure')
        result = []
        repeat_stack = []
    
        for (i,m) in enumerate(measures):
            
            barline_node = m.find('barline')
            if barline_node:
                repeat_nodes = barline_node.findall('repeat')
                # single measure || start end || repeat loop
                if len(repeat_nodes) > 1:
                    # this is a single measure repeat, look for the 'times'
                    # attribute with a direction fo 'backwards' and generate
                    # repeats
                    n = int(repeat_nodes[1].attrib['times']) + 1
                    for _ in range(n):
                        result.append(m)

                elif repeat_nodes[0].attrib['direction'] == "forward":
                    repeat_stack.append(i)
                    result.append(m)

                elif repeat_nodes[0].attrib['direction'] == "backward":
                    # n times to repeat 
                    n = int(repeat_nodes[0].attrib['times'])
                    # get the last start repeat
                    start_n = repeat_stack.pop()

                    # add the current measure and increment count.
                    result.append(m)

                    x = measures[start_n:i+1]
                    for _ in range(n):
                        result += x  
            else:
                result.append(m)

        return result
    
    def _generate_track_events(self, mnodes, track):

        def getBpm(m):
            try:
                return int(m.find('direction').find('direction-type').find('metronome').find('per-minute').text)
            except:
                return None
            
        def getDuration(note_elm, bpm, divisions):
            tg_dur = int(note_elm.find('duration').text)
            return (60.0/bpm) * (tg_dur/divisions)
            

        def parse_note(note_elm, bpm, divisions):
            isRest = False
            for x in note_elm:
                if x.tag == 'rest':
                    isRest = True
                    break

            if isRest:
                n = tevt.rest()
            else:
                n = tevt.note()
                t = note_elm.find('notations').find('technical')
                n.fret = int(t.find('fret').text)
                n.g_string = int(t.find('string').text)
                n.dynamic = int(t.find('velocity').text)
            n.duration = getDuration(note_elm, bpm, divisions)
            
            return n
        
        def parse_chord(chord_elm, bpm, divisions):
            c = tevt.chord()
            c.stroke = {
                "-1": "down",
                "1": "up",
            }.get(chord_elm.attrib['stroke'],None)
            if c.stroke:
                c.stroke_duration = (60.0/bpm) * (int(chord_elm.attrib['value']) / 4.0)
            
            for e in chord_elm:
                if e.tag == "note":
                    n = parse_note(e, bpm, divisions)
                    if not c.duration:
                        c.duration = n.duration
                    c.notes.append(n)

            return c
            
 
        te_list = []         
        elapsed = 0.0
        bpm = getBpm(mnodes[0])
        divisions = float(mnodes[0].find('attributes').find('divisions').text)
        
        for c in mnodes[0]:
            if c.tag == 'tablature':
                for e in c:
                    if e.tag == "note":
                        te_list.append(parse_note(e, bpm, divisions))
                    elif e.tag == "chord":
                        te_list.append(parse_chord(e, bpm, divisions))    
                    else:
                        print((e,"(%s) not processed" % e.tag))

        return te_list 

    def setup(self, root):
        "create a set of tracks for the song"

        # 'parts' are instruments 
        parts_map = self._get_part_list(root)
        # go through the first measure of each part to determine the
        # tuning for each track.
        tracks = self._get_tuning(root, parts_map)

        #_get_measures(self, part_node)
        for part in root.findall('part'):
            id = part.attrib['id']
            track = tracks[id]

            # create a linear list of measures and unravelling all
            # the repeats.
            mnodes = self._get_linear_measures(part)
            
            # convert all notes, chords, rests and commands
            # into track events. 
            track.events = self._generate_track_events(mnodes, track) 
            
        return tracks

    def parse(self, filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        return self.setup(root) 
        

if __name__ == '__main__':
    filename = sys.argv[1]

    tracks = MusicXmlParser().parse(filename)
    print(tracks)