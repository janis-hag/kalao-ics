import subprocess
from subprocess import PIPE, STDOUT

input = f"""
loadfits "cube12_12_60000_v10mps_1ms.fits" imc
readshmim dm01disp04
streamburst imc dm01disp04 1000
exitCLI
"""
cp = subprocess.run(["milk"], input=input, encoding='utf8', stdout=PIPE,
                    stderr=STDOUT)

print("=========================== STDOUT")

print(cp.stdout)

print("=========================== STDERR")

print(cp.stderr)
