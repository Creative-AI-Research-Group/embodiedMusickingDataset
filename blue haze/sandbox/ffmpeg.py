from subprocess import Popen
cmd = ['ffmpeg', '-f', 'dshow', '-i', 'video=HUE HD Camera', 'out.avi']
p = Popen(cmd)
p.terminate()
