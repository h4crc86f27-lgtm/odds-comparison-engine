import subprocess

is_running=False
try:
	output = subprocess.check_output(["pgrep","--list-full","python"])
	lines = output.decode("utf8").split("\n")
	for line in lines:
		if line.find("arb_monitor.py")>-1:
			is_running=True
			break
except:
	pass

if not is_running:
	print("starting monitor up..")
	subprocess.run(["/usr/bin/python3","/home/arb_bot/beta/arb_monitor.py"])
else:
	print("monitor is running")
