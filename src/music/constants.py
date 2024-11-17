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
    

Dynamic = _Dynamic()
Duration = _Duration()