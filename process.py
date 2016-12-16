import subprocess

p = None
msg = 'christmas'

def start():
    global msg
    global p

    if (p is not None):
        stop()
    p = subprocess.Popen(["/usr/local/bin/lights", msg])
    #p = subprocess.Popen(["top"])
    return


def stop():
    global p
    p.terminate()
    p = None
    return


def message(message):
    global msg
    msg = message
    return