"""Upload repo to GitHub using API"""
import subprocess, os, json, base64, requests

TOKEN = open(".git-credentials-temp").read().strip().split(":")[-1].split("@")[0]
OWNER = "massielvasquez193-dot"
REPO = "CC-SEEDSANCE-SKILL-ZIDONGHUA"
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json"}
API = "https://api.github.com"

# Check repo exists
r = requests.get(f"{API}/repos/{OWNER}/{REPO}", headers=HEADERS)
print(f"Repo check: {r.status_code}")

# If repo is empty, create initial commit via API
# Get list of tracked files
files = subprocess.check_output(["git", "ls-files"], text=True).strip().split("\n")
print(f"Files: {len(files)}")

# Create blobs
blobs = {}
for f in files:
    content = open(f, "rb").read()
    r = requests.post(f"{API}/repos/{OWNER}/{REPO}/git/blobs", headers=HEADERS,
                      json={"content": base64.b64encode(content).decode(), "encoding": "base64"})
    if r.status_code == 201:
        blobs[f] = r.json()["sha"]
        print(f"  blob: {f} -> {blobs[f][:8]}")
    else:
        print(f"  FAIL: {f} -> {r.status_code} {r.text[:100]}")

print(f"Created {len(blobs)} blobs")

# Create tree
tree_items = [{"path": f, "mode": "100644", "type": "blob", "sha": sha} for f, sha in blobs.items()]
r = requests.post(f"{API}/repos/{OWNER}/{REPO}/git/trees", headers=HEADERS,
                  json={"tree": tree_items})
if r.status_code == 201:
    tree_sha = r.json()["sha"]
    print(f"Tree: {tree_sha}")
else:
    print(f"Tree FAIL: {r.status_code} {r.text}")
    exit(1)

# Create commit
r = requests.post(f"{API}/repos/{OWNER}/{REPO}/git/commits", headers=HEADERS,
                  json={"message": "Initial commit: CC Seedance Skill Zidonghua - TikTok AI Factory",
                        "tree": tree_sha})
if r.status_code == 201:
    commit_sha = r.json()["sha"]
    print(f"Commit: {commit_sha}")
else:
    print(f"Commit FAIL: {r.status_code} {r.text}")
    exit(1)

# Update ref
r = requests.patch(f"{API}/repos/{OWNER}/{REPO}/git/refs/heads/master", headers=HEADERS,
                   json={"sha": commit_sha})
print(f"Ref update: {r.status_code}")
if r.status_code not in [200, 201]:
    print(r.text)
else:
    print("=== UPLOAD SUCCESSFUL ===")
