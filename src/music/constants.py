from singleton_decorator import singleton
@singleton
class _Duration:
    "duration in beats"
    WHOLE = 4.0
    HALF = 2.0
    QUARTER = 1.0
    EIGHT = 0.5
    SIXTEENTH = 0.25
    THRISTYSECOND = 0.125
    SIXTYFORTH = 0.0625


@singleton
class _Dynamic:
    PPP = 16
    PP = 33
    P = 49
    MP = 64
    MF = 80
    F = 96
    FF = 112
    FFF = 127
    DEF = -1 # use the default for the track or MP

    def tooltip(self, v):
        return {
            self.FFF: "fortississimo: very very loud",
            self.FF : "fortissimo: very loud",
            self.F  : "forte: loud",
            self.MF : "mezzo-forte: moderately loud",
            self.MP : "mezzo-piano: moderately quiet",
            self.P  : "piano: quiet",
            self.PP : "pianissimo: very quiet",
            self.PPP: "pianississimo: very very quiet"
        }.get(v,f"midi {v} value")
    
    def short_text(self, v):
        from view.editor.glyphs.common import FORTE_SYMBOL, MEZZO_SYMBOL, PIANO_SYMBOL
        return {
            self.FFF: FORTE_SYMBOL * 3,
            self.FF : FORTE_SYMBOL * 2,
            self.F  : FORTE_SYMBOL,
            self.MF : MEZZO_SYMBOL + FORTE_SYMBOL,
            self.MP : MEZZO_SYMBOL + PIANO_SYMBOL,
            self.P  : PIANO_SYMBOL,
            self.PP : PIANO_SYMBOL * 2,
            self.PPP: PIANO_SYMBOL * 3
        }.get(v,str(v))
    

Dynamic = _Dynamic()
Duration = _Duration()