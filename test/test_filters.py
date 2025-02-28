import gcsynth, time

data = {"sfpaths": ["/home/david/proj/GuitarComposer/data/sf/27mg_Symphony_Hall_Bank.SF2"]}
gcsynth.start(data)
chan = 0

path = "/usr/lib/ladspa/guitarix_echo.so"
label = "guitarix_echo"

print(gcsynth.filter_query(path, label))

gcsynth.filter_add(chan, path, label)
print(f"enable filter {label}")
gcsynth.filter_set_control_by_name(0, label, "release", 100.0)
gcsynth.filter_set_control_by_name(0, label, "time", 2000.0)

gcsynth.filter_enable(chan, label)
        
gcsynth.noteon(0, 60, 100)
time.sleep(10.0)

"""
gcsynth.noteon(0, 63, 100)
time.sleep(1.0)

gcsynth.noteon(0, 65, 100)
time.sleep(1.0)

time.sleep(5)
"""

gcsynth.stop()

