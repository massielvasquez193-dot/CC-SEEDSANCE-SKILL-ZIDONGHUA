import subprocess, sys

os.chdir(r"d:\cc seedance skill zidonghua")
subprocess.run(["git", "config", "credential.helper", "store --file .git-credentials-temp"], shell=True)
result = subprocess.run(["git", "push", "-u", "origin", "master"], capture_output=True, text=True, shell=True)
print(result.stdout)
print(result.stderr, file=sys.stderr)
subprocess.run(["git", "config", "--unset", "credential.helper"], shell=True)
print("Exit:", result.returncode)
