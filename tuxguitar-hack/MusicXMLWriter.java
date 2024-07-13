package org.herac.tuxguitar.io.musicxml;

import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Result;
import javax.xml.transform.Source;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import org.herac.tuxguitar.gm.GMChannelRoute;
import org.herac.tuxguitar.gm.GMChannelRouter;
import org.herac.tuxguitar.gm.GMChannelRouterConfigurator;
import org.herac.tuxguitar.io.base.TGFileFormatException;
import org.herac.tuxguitar.io.musicxml.MusicXMLLyricWriter.MusicXMLMeasureLyric;
import org.herac.tuxguitar.song.managers.TGSongManager;
import org.herac.tuxguitar.song.models.TGBeat;
import org.herac.tuxguitar.song.models.TGChannel;
import org.herac.tuxguitar.song.models.TGDivisionType;
import org.herac.tuxguitar.song.models.TGDuration;
import org.herac.tuxguitar.song.models.TGMarker;
import org.herac.tuxguitar.song.models.TGMeasure;
import org.herac.tuxguitar.song.models.TGNote;
import org.herac.tuxguitar.song.models.TGNoteEffect;
import org.herac.tuxguitar.song.models.TGSong;
import org.herac.tuxguitar.song.models.TGString;
import org.herac.tuxguitar.song.models.TGTimeSignature;
import org.herac.tuxguitar.song.models.TGTrack;
import org.herac.tuxguitar.song.models.TGVoice;
import org.herac.tuxguitar.song.models.effects.TGEffectBend;
import org.herac.tuxguitar.song.models.effects.TGEffectBend.BendPoint;
import org.herac.tuxguitar.song.models.effects.TGEffectGrace;
import org.herac.tuxguitar.song.models.effects.TGEffectHarmonic;
import org.herac.tuxguitar.song.models.effects.TGEffectTremoloBar;
import org.herac.tuxguitar.song.models.effects.TGEffectTremoloBar.TremoloBarPoint;
import org.herac.tuxguitar.song.models.effects.TGEffectTremoloPicking;
import org.herac.tuxguitar.util.TGMusicKeyUtils;
import org.herac.tuxguitar.util.TGVersion;
import org.w3c.dom.Attr;
import org.w3c.dom.DOMImplementation;
import org.w3c.dom.Document;
import org.w3c.dom.DocumentType;
import org.w3c.dom.Node;

import com.sun.source.doctree.SerialFieldTree;

// Note: The order of elements is important
// see https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/

public class MusicXMLWriter {
	
	private static final String[] DURATION_NAMES = new String[]{ "whole", "half", "quarter", "eighth", "16th", "32nd", "64th", };
	
	private static final int DURATION_DIVISIONS = (int)TGDuration.QUARTER_TIME;
	
	private static final int[] DURATION_VALUES = new int[]{
		DURATION_DIVISIONS * 4, // WHOLE
		DURATION_DIVISIONS * 2, // HALF
		DURATION_DIVISIONS * 1, // QUARTER
		DURATION_DIVISIONS / 2, // EIGHTH
		DURATION_DIVISIONS / 4, // SIXTEENTH
		DURATION_DIVISIONS / 8, // THIRTY_SECOND
		DURATION_DIVISIONS / 16, // SIXTY_FOURTH
	};
	
	private TGSongManager manager;
	
	private OutputStream stream;
	
	private Document document;
	
	public MusicXMLWriter(OutputStream stream){
		this.stream = stream;
	}
	
	public void writeSong(TGSong song) throws TGFileFormatException{
		try {
			this.manager = new TGSongManager();
			this.document = newDocument();
			
			Node node = this.addNode(this.document,"score-partwise");
			this.addAttribute(node, "version", "4.0");
			this.writeHeaders(song, node);
			this.writeSong(song, node);
			this.saveDocument();
			
			this.stream.flush();
			this.stream.close();
		}catch(Throwable throwable){
			throw new TGFileFormatException("Could not write song!.",throwable);
		}
	}
	
	private void writeHeaders(TGSong song, Node parent){
		this.writeWork(song, parent);
		this.writeIdentification(song, parent);
	}
	
	private void writeWork(TGSong song, Node parent){
		this.addNode(this.addNode(parent,"work"),"work-title", song.getName());
	}
	
	private void writeIdentification(TGSong song, Node parent){
		Node identification = this.addNode(parent,"identification");
		this.addAttribute(this.addNode(identification,"creator",song.getAuthor()),"type","composer");
		this.addNode(this.addNode(identification,"encoding"), "software", "TuxGuitar " + TGVersion.CURRENT.getVersion());
	}
	
	private void writeSong(TGSong song, Node parent){
		this.writePartList(song, parent);
		this.writeParts(song, parent);
	}
	
	private void writePartList(TGSong song, Node parent){
		Node partList = this.addNode(parent,"part-list");
		
		GMChannelRouter gmChannelRouter = new GMChannelRouter();
		GMChannelRouterConfigurator gmChannelRouterConfigurator = new GMChannelRouterConfigurator(gmChannelRouter);
		gmChannelRouterConfigurator.configureRouter(song.getChannels());
		
		Iterator<TGTrack> tracks = song.getTracks();
		while(tracks.hasNext()){
			TGTrack track = (TGTrack)tracks.next();
			TGChannel channel = this.manager.getChannel(song, track.getChannelId());
			
			Node scoreParts = this.addNode(partList,"score-part");
			this.addAttribute(scoreParts, "id", "P" + track.getNumber());
			
			this.addNode(scoreParts, "part-name", track.getName());
			
			if( channel != null ){
				GMChannelRoute gmChannelRoute = gmChannelRouter.getRoute(channel.getChannelId());
				
				Node scoreInstrument = this.addAttribute(this.addNode(scoreParts, "score-instrument"), "id", "P" + track.getNumber() + "-I1");
				this.addNode(scoreInstrument, "instrument-name",channel.getName());
			
				Node midiInstrument = this.addAttribute(this.addNode(scoreParts, "midi-instrument"), "id", "P" + track.getNumber() + "-I1");
				this.addNode(midiInstrument, "midi-channel",Integer.toString(gmChannelRoute != null ? gmChannelRoute.getChannel1() + 1 : 16));
				this.addNode(midiInstrument, "midi-program",Integer.toString(channel.getProgram() + 1));
			}
		}
	}
	
	private void writeParts(TGSong song, Node parent){
		Iterator<TGTrack> tracks = song.getTracks();
		while(tracks.hasNext()){
			TGTrack track = (TGTrack)tracks.next();
			this.writeTrack(track, parent);
		}
	}
	
	private void writeTrack(TGTrack track, Node parent){
		Node part = this.addAttribute(this.addNode(parent,"part"), "id", "P" + track.getNumber());
		
		TGMeasure previous = null;
		
		MusicXMLLyricWriter lyricWriter = new MusicXMLLyricWriter(track);
		
		Iterator<TGMeasure> measures = track.getMeasures();
		while(measures.hasNext()){
			TGMeasure measure = (TGMeasure)measures.next();
			Node measureNode = this.addAttribute(this.addNode(part,"measure"), "number",Integer.toString(measure.getNumber()));
			
			this.writeMeasureAttributes(measureNode, measure, previous, track.isPercussion());

			this.writeDirection(measureNode, measure, previous);
			
			this.writeBarline(measureNode, measure);

			MusicXMLMeasureLyric[] measureLyrics = lyricWriter.generateLyricList(measure);

			// score
			boolean measureIsEmpty = true;
			for (int nVoice=0; nVoice<TGBeat.MAX_VOICES; nVoice++) {
				// assuming lyrics are attached to voice 0
				this.writeBeats(measureNode, measure, nVoice, measureIsEmpty, false, nVoice==0 ? measureLyrics : null);
				measureIsEmpty = false;
			}
			// tab
			if (!track.isPercussion()) {
				measureIsEmpty = true;
				backToMeasureStart(measureNode, measure);
				for (int nVoice=0; nVoice<TGBeat.MAX_VOICES; nVoice++) {
					this.writeBeats(measureNode, measure, nVoice, measureIsEmpty, true, null);
					measureIsEmpty = false;
				}
			}
			
			previous = measure;
		}
	}
	
	private void backToMeasureStart(Node parent, TGMeasure measure) {
		Node backupNode = this.addNode(parent, "backup");
		TGTimeSignature ts = measure.getTimeSignature();
		this.addNode(backupNode, "duration", String.valueOf((int)(TGDuration.QUARTER * DURATION_DIVISIONS * ts.getNumerator() / ts.getDenominator().getValue())));
	}
	
	private void writeBarline(Node parent, TGMeasure measure) {
		boolean needBarline = measure.isRepeatOpen() || (measure.getRepeatClose() > 0);
		
		// TODO: 
		// add, when available in tuxguitar; alternate repeat, bar-style, coda, wavy-line etc..
		// https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/barline/
		
		if (needBarline) {
			Node barLine = this.addNode(parent,"barline");
			
			if (measure.isRepeatOpen()) {
				Node repeat = this.addNode(barLine,"repeat");
				this.addAttribute(repeat, "direction", "forward");
			}
			
			if (measure.getRepeatClose() > 0) {
				Node repeat = this.addNode(barLine,"repeat");
				this.addAttribute(repeat, "direction", "backward");
				this.addAttribute(repeat, "times", Integer.toString(measure.getRepeatClose()));							
			}

			// TODO:
			// add, when available in tuxguitar, winged, after-jump
			// https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/repeat/

		}
	}

	private void writeMeasureAttributes(Node parent, TGMeasure measure, TGMeasure previous, boolean isPercussion){
		boolean divisionChanges = (previous == null);
		boolean keyChanges = (previous == null || measure.getKeySignature() != previous.getKeySignature());
		boolean clefChanges = (previous == null || measure.getClef() != previous.getClef());
		boolean timeSignatureChanges = (previous == null || !measure.getTimeSignature().isEqual(previous.getTimeSignature()));
		
		if (divisionChanges || keyChanges || clefChanges || timeSignatureChanges) {
			Node measureAttributes = this.addNode(parent,"attributes");
			if(divisionChanges){
				this.addNode(measureAttributes,"divisions",Integer.toString(DURATION_DIVISIONS));
			}
			if(keyChanges){
				this.writeKeySignature(measureAttributes, measure.getKeySignature());
			}
			if(timeSignatureChanges){
				this.writeTimeSignature(measureAttributes,measure.getTimeSignature());
			}
			if(clefChanges){
				this.writeClef(measureAttributes,measure.getClef(), isPercussion);
			}
			
			if (!isPercussion && (previous==null || measure.getNumber() == 1)) {
				this.writeTuning(measureAttributes, measure.getTrack(), measure.getKeySignature());
			}
		}
	}
	
	private void writeTuning(Node parent, TGTrack track, int keySignature){
		Node staffDetailsNode = this.addNode(parent,"staff-details");
		this.addAttribute(staffDetailsNode, "number", "2");
		this.addNode(staffDetailsNode, "staff-lines", Integer.toString( track.stringCount() ));
		for( int i = track.stringCount() ; i > 0 ; i --){
			TGString string = track.getString( i );
			Node stringNode = this.addNode(staffDetailsNode, "staff-tuning");
			this.addAttribute(stringNode, "line", Integer.toString( (track.stringCount() - string.getNumber()) + 1 ) );
			this.addAttribute(stringNode, "string", Integer.toString( string.getNumber() ));
            this.addAttribute(stringNode, "midiCode", Integer.toString(string.getValue()));
			

			this.writeNote(stringNode, "tuning-", string.getValue(), keySignature);
		}
	}
	
	private void writeNote(Node parent, String prefix, int value, int keySignature) {
		this.addNode(parent,prefix+"step", TGMusicKeyUtils.noteShortName(value,keySignature));
		int alteration = TGMusicKeyUtils.noteAlteration(value, keySignature);
		if(alteration != TGMusicKeyUtils.NATURAL){
			this.addNode(parent,prefix+"alter", ( alteration == TGMusicKeyUtils.SHARP ? "1" : "-1" ) );
		}
		this.addNode(parent,prefix+"octave", String.valueOf(TGMusicKeyUtils.noteOctave(value, keySignature)));
	}
	
	private void writeTimeSignature(Node parent, TGTimeSignature ts){
		Node node = this.addNode(parent,"time");
		this.addNode(node,"beats",Integer.toString(ts.getNumerator()));
		this.addNode(node,"beat-type",Integer.toString(ts.getDenominator().getValue()));
	}
	
	private void writeKeySignature(Node parent, int ks){
		int value = ks;
		if(value != 0){
			value = ( (((ks - 1) % 7) + 1) * ( ks > 7?-1:1));
		}
		Node key = this.addNode(parent,"key");
		this.addNode(key,"fifths",Integer.toString( value ));
	}
	
	private void writeClef(Node parent, int clef, boolean isPercussion){
		// first clef: score
		Node node = this.addNode(parent,"clef");
		if (!isPercussion) {
			this.addAttribute(node, "number", "1");
		}
		
		if (isPercussion) {
			this.addNode(node,"sign","percussion");
		}
		else if(clef == TGMeasure.CLEF_TREBLE){
			this.addNode(node,"sign","G");
			this.addNode(node,"line","2");
			this.addNode(node, "clef-octave-change", String.valueOf(-1));
		}
		else if(clef == TGMeasure.CLEF_BASS){
			this.addNode(node,"sign","F");
			this.addNode(node,"line","4");
			this.addNode(node, "clef-octave-change", String.valueOf(-1));
		}
		else if(clef == TGMeasure.CLEF_TENOR){
			this.addNode(node,"sign","G");
			this.addNode(node,"line","2");
		}
		else if(clef == TGMeasure.CLEF_ALTO){
			this.addNode(node,"sign","G");
			this.addNode(node,"line","2");
		}
		
		// second clef: tablature
		if (!isPercussion) {
			node = this.addNode(parent,"clef");
			this.addAttribute(node, "number", "2");
			this.addNode(node, "sign", "TAB");
		}
	}
	
	private void writeDirection(Node parent, TGMeasure measure, TGMeasure previous){
		boolean tempoChanges = (previous == null || measure.getTempo().getValue() != previous.getTempo().getValue());
		
		if(tempoChanges){
			Node direction = this.addAttribute(this.addNode(parent,"direction"),"placement","above");
			Node directionType = this.addNode(direction, "direction-type");
			Node metronome = this.addNode(directionType, "metronome");
			this.addNode(metronome, "beat-unit", "quarter");
			this.addNode(metronome, "per-minute", String.valueOf(measure.getTempo().getValue()));
		}
	}
	
	private void addHandEffects(Node parent, TGNote note) {
        TGNoteEffect effect = note.getEffect();
		int i;
		if (effect != null) {
            
			if (effect.isFadeIn()) {
				this.addNode(parent, "fadeIn");
			}
			if (effect.isLetRing()) {
				this.addNode(parent, "legato");
			}
			if (effect.isPopping()) {
				this.addNode(parent, "popping");
			}
            if (effect.isSlapping()) {
				this.addNode(parent, "slapping");
			} 
			if (effect.isTapping()) {
				this.addNode(parent, "tapping");
			}
            if (effect.isStaccato()) {
				this.addNode(parent,"staccato");
			}
            if (effect.isPalmMute()) {
				this.addNode(parent, "palm_mute");
			}
            if (effect.isHeavyAccentuatedNote()) {
				this.addNode(parent, "heavy_accentuated");
			}
			if (effect.isAccentuatedNote()) {
				this.addNode(parent, "accentuated");
			}
			if (effect.isGhostNote()) {
				this.addNode(parent, "ghost");
			}	
            if (effect.isHammer()) {
				this.addNode(parent, "hammer");
			}
            if (effect.isSlide()) {
				this.addNode(parent, "slide");
			}           
            if (effect.isVibrato()) {
				this.addNode(parent, "vibrato");	
			}
			if (effect.isDeadNote()) {
				this.addNode(parent, "dead");	
			}


            TGEffectBend bend = effect.getBend();
			if (bend != null) {
				List<BendPoint> bp_list = bend.getPoints();
				if (bp_list != null && !bp_list.isEmpty()) {
				    Node bend_node = this.addNode(parent,"bend");
                    for(i = 0; i < bp_list.size(); i++) {
						BendPoint bp = bp_list.get(i);
						int pos = bp.getPosition();
                        Node bp_node = this.addNode(bend_node,"bend_point");
						this.addAttribute(bp_node,"position", 
						    Integer.toString(pos) );
						this.addAttribute(bp_node,"value", 
						    Integer.toString(bp.getValue()) );
					}      
				} // end are there points
			}// end bend

			TGEffectTremoloBar tbar = effect.getTremoloBar();
			if (tbar != null) {
				List<TremoloBarPoint> tb_list = tbar.getPoints();
				if (tb_list != null && !tb_list.isEmpty()) {
					Node tb_node = this.addNode(parent,"tremolo_bar"); 
					for(i = 0; i < tb_list.size(); i++) {
						TremoloBarPoint bp = tb_list.get(i);
						Node bp_node = this.addNode(tb_node,"tb_point");
						this.addAttribute(bp_node,"position", 
						    Integer.toString(bp.getPosition()) );
						this.addAttribute(bp_node,"value", 
						    Integer.toString(bp.getValue()) );
					}
				}
			}

			TGEffectGrace grace = effect.getGrace();
			if (grace != null) {
				Node grace_node = this.addNode(parent,"grace");

                int dynamic = grace.getDynamic();
				int duration = grace.getDuration();
                int fret = grace.getFret();
                String onBeat = (grace.isOnBeat()) ? "true":"false";
				String dead = (grace.isDead()) ? "true":"false";

				this.addAttribute(grace_node,"fret",
				    Integer.toString(fret));
				this.addAttribute(grace_node,"duration",
			    	Integer.toString(duration));
				this.addAttribute(grace_node,"dynamic",
			    	Integer.toString(dynamic));
				this.addAttribute(grace_node,"transition",
			    	Integer.toString(grace.getTransition()) );

                this.addAttribute(grace_node, "onBeat", onBeat);
                this.addAttribute(grace_node, "dead", dead);
			}

			TGEffectHarmonic harmonic = effect.getHarmonic();
			if (harmonic != null) {
                Node harmonic_node = this.addNode(parent, "harmonic");
				this.addAttribute(harmonic_node, "natural", 
					(harmonic.isNatural()) ? "true": "false");
				this.addAttribute(harmonic_node, "pinched", 
					(harmonic.isPinch()) ? "true": "false" );
				this.addAttribute(harmonic_node, "semi",
					(harmonic.isSemi()) ? "true": "false" );	
			}			
		}
	}

	private void writeBeats(Node _parent, TGMeasure measure, int nVoice, boolean measureIsEmpty, boolean isTablature, MusicXMLMeasureLyric[] lyrics){
		int ks = measure.getKeySignature();
		int beatCount = measure.countBeats();
		int lyricIndex = 0;
		// store first rest beats of voice in list, before finding possibly a non-empty beat
		List<TGBeat> firstBeats = new ArrayList<TGBeat>();
		boolean wroteSomething = false;
		long lastWrittenNoteEnd = 0;	// tick of last (non-empty) beat corresponding to voice
		Node parent = (isTablature) ? this.addNode(_parent,"tablature") : _parent;

        if (isTablature && measure.hasMarker()) {
            TGMarker marker = measure.getMarker();
			this.addNode(parent, "marker", marker.getTitle());
		}


		for(int b = 0; b < beatCount; b ++){
			TGBeat beat = measure.getBeat( b );
			TGVoice voice = beat.getVoice(nVoice);

			if (voice.isRestVoice() && !wroteSomething) {
				firstBeats.add(beat);
				continue;
			}
			// here, something has been found to be written
			// need to rewind to measure start?
			if (!measureIsEmpty && !wroteSomething) {
				backToMeasureStart(parent, measure);
			}
			// need to insert rests before?
			if (!firstBeats.isEmpty()) {
				for (TGBeat restBeat : firstBeats) {
					insertRest(parent, restBeat.getVoice(nVoice).getDuration(), nVoice, isTablature);
				}
				firstBeats.clear();
			}
			if(voice.isRestVoice()){
				if (beat.getStart() >= lastWrittenNoteEnd) {
					insertRest(parent, voice.getDuration(), nVoice, isTablature);
				}
			} else {
				int noteCount = voice.countNotes();
				Node noteParent = parent;

                if (noteCount > 1) {
					noteParent = this.addNode(parent,"chord");

					this.addAttribute(noteParent, "stroke",
					    Integer.toString(beat.getStroke().getDirection()));
					this.addAttribute(noteParent, "value",
					    Integer.toString(beat.getStroke().getValue()));
				}                

				for(int n = 0; n < noteCount; n ++){
					TGNote note = voice.getNote( n );
					
					Node noteNode = this.addNode(noteParent,"note");
					
					int value = (beat.getMeasure().getTrack().getString(note.getString()).getValue() + note.getValue());
					
					//if(n > 0){
					//	this.addNode(noteNode,"chord");
					//}
					
					Node pitchNode = this.addNode(noteNode,"pitch");
					this.writeNote(pitchNode, "", value, ks);
					this.writeDurationAndVoice(noteNode, voice.getDuration(), note.isTiedNote(), nVoice);
					this.addNode(noteNode, "staff", isTablature ? "2" : "1");
					
					if (isTablature) {
						Node technicalNode = this.addNode(this.addNode(noteNode, "notations"), "technical");
						this.addNode(technicalNode,"fret", Integer.toString( note.getValue() ));
						this.addNode(technicalNode,"string", Integer.toString( note.getString() ));
                        this.addNode(technicalNode,"velocity", Integer.toString( note.getVelocity() ));
						
						//findme - add hand effects
						this.addHandEffects(technicalNode, note);
					
					} else if(n==0) {
						// Attach lyric to the first note
						try {
							MusicXMLMeasureLyric measureLyric = lyrics[lyricIndex++];
							writeLyric(noteNode, measureLyric);
						} catch (Exception e) {
							// ignore
							// can be out of bound? when there are more lyrics than text
							// can be null if there is an offset
						}
					}
					lastWrittenNoteEnd = beat.getStart() + voice.getDuration().getTime();
				}
				wroteSomething = true;
			}
		}
		// empty measure? If so, fill with rests
		if (!wroteSomething && measureIsEmpty && !firstBeats.isEmpty()) {
			for (TGBeat restBeat : firstBeats) {
				insertRest(parent, restBeat.getVoice(nVoice).getDuration(), nVoice, isTablature);
			}
		}
	}
	
	private void insertRest(Node parent, TGDuration duration, int nVoice, boolean isTablature) {
		Node noteRestNode = this.addNode(parent,"note");
		this.addNode(noteRestNode,"rest");
		this.writeDurationAndVoice(noteRestNode, duration, false, nVoice);
		this.addNode(noteRestNode, "staff", isTablature ? "2" : "1");
	}

	
	private void writeLyric(Node parent, MusicXMLMeasureLyric measureLyric) {
		if (measureLyric.text.length() > 0) {
			Node lyricNode = this.addNode(parent, "lyric");

			this.addNode(lyricNode,"syllabic", measureLyric.syllabic.toString());
			this.addNode(lyricNode,"text", measureLyric.text);
		}
	}
	
	private void writeDurationAndVoice(Node parent, TGDuration duration, boolean isTiedNote, int nVoice){
		int index = duration.getIndex();
		if( index >=0 && index <= 6 ){
			int value = (DURATION_VALUES[ index ] * duration.getDivision().getTimes() / duration.getDivision().getEnters());
			if(duration.isDotted()){
				value += (value / 2);
			}
			else if(duration.isDoubleDotted()){
				value += ((value / 4) * 3);
			}
			
			this.addNode(parent,"duration",Integer.toString(value));
			if(isTiedNote){
				this.addAttribute(this.addNode(parent,"tie"),"type","stop");
			}
			this.addNode(parent, "voice", String.valueOf(nVoice+1));

			this.addNode(parent,"type",DURATION_NAMES[ index ]);
			
			if(duration.isDotted()){
				this.addNode(parent,"dot");
			}
			else if(duration.isDoubleDotted()){
				this.addNode(parent,"dot");
				this.addNode(parent,"dot");
			}
			
			if(!duration.getDivision().isEqual(TGDivisionType.NORMAL)){
				Node divisionType = this.addNode(parent,"time-modification");
				this.addNode(divisionType,"actual-notes",Integer.toString(duration.getDivision().getEnters()));
				this.addNode(divisionType,"normal-notes",Integer.toString(duration.getDivision().getTimes()));
			}
		}
	}
	
	private Node addAttribute(Node node, String name, String value){
		Attr attribute = this.document.createAttribute(name);
		attribute.setNodeValue(value);
		node.getAttributes().setNamedItem(attribute);
		return node;
	}
	
	private Node addNode(Node parent, String name){
		Node node = this.document.createElement(name);
		parent.appendChild(node);
		return node;
	}
	
	private Node addNode(Node parent, String name, String content){
		Node node = this.addNode(parent, name);
		node.setTextContent(content);
		return node;
	}
	
	private Document newDocument() {
		try {
			DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
			DocumentBuilder builder = factory.newDocumentBuilder();
			Document document = builder.newDocument();
			return document;
		}catch(Throwable throwable){
			throwable.printStackTrace();
		}
		return null;
	}
	
	private void saveDocument() {
		try {
			TransformerFactory xformFactory = TransformerFactory.newInstance();
			Transformer idTransform = xformFactory.newTransformer();
			Source input = new DOMSource(this.document);
			Result output = new StreamResult(this.stream);
			idTransform.setOutputProperty(OutputKeys.INDENT, "yes");
			DOMImplementation domImpl = this.document.getImplementation();
			DocumentType docType = domImpl.createDocumentType("doctype", 
					"-//Recordare//DTD MusicXML 4.0 Partwise//EN",
					"http://www.musicxml.org/dtds/partwise.dtd");
			idTransform.setOutputProperty(OutputKeys.DOCTYPE_PUBLIC, docType.getPublicId());
			idTransform.setOutputProperty(OutputKeys.DOCTYPE_SYSTEM, docType.getSystemId());
			idTransform.transform(input, output);
		}catch(Throwable throwable){
			throwable.printStackTrace();
		}
	}
	

}
