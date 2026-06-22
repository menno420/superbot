#!/usr/bin/env python3
"""
Merge-conflict simulation for the active-work claim ledger.

Compares three physical layouts under REALISTIC concurrent-session edit
patterns, using ACTUAL `git merge` to detect conflicts (not a model of git):

  status_quo : one shared file, append/remove on two shared lists
  per_sector : 5 files (S1..S5), session edits only its sector's file
  per_claim  : one file per session (claims/<branch>.md), created+deleted

Concurrency model: sessions have overlapping lifetimes. Each session forks a
branch from main's CURRENT head when it OPENS, commits its open-edit, runs
while OTHER sessions merge into main, then commits its close-edit and merges
back. Conflicts are counted at merge time -- exactly the real failure mode.

Sector weights are taken from the real active-work.md distribution
(S1 dominant ~55%), so same-sector clustering is faithful.
"""
import os, subprocess, random, tempfile, shutil, sys, collections

SECTOR_WEIGHTS = {"S1": 0.55, "S2": 0.12, "S3": 0.15, "S4": 0.08, "S5": 0.10}

def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo, *args],
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {args} failed:\n{r.stdout}\n{r.stderr}")
    return r

def init_repo(layout):
    repo = tempfile.mkdtemp(prefix="claimsim_")
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "sim@test")
    git(repo, "config", "user.name", "sim")
    git(repo, "config", "commit.gpgsign", "false")
    if layout == "status_quo":
        write(repo, "active-work.md",
              "# Active work\n\n## Active claims\n\n<!--CLAIMS-->\n\n## Recently cleared\n\n<!--CLEARED-->\n")
    elif layout == "per_sector":
        for s in SECTOR_WEIGHTS:
            write(repo, f"aw_{s}.md",
                  f"# {s} active\n\n## Active claims\n\n<!--CLAIMS-->\n\n## Recently cleared\n\n<!--CLEARED-->\n")
    elif layout == "per_claim":
        os.makedirs(os.path.join(repo, "claims"), exist_ok=True)
        write(repo, "claims/.keep", "")
    git(repo, "add", "-A"); git(repo, "commit", "-qm", "init")
    return repo

def write(repo, rel, content):
    p = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True) if os.path.dirname(p) else None
    with open(p, "w") as f: f.write(content)

def read(repo, rel):
    with open(os.path.join(repo, rel)) as f: return f.read()

def append_in_section(repo, rel, marker, line):
    txt = read(repo, rel)
    txt = txt.replace(marker, line + "\n" + marker)
    write(repo, rel, txt)

def remove_line(repo, rel, line):
    txt = read(repo, rel)
    txt = txt.replace(line + "\n", "")
    write(repo, rel, txt)

def do_open(repo, layout, sess, sector):
    line = f"- `{sess}` claim ({sector})"
    if layout == "status_quo":
        append_in_section(repo, "active-work.md", "<!--CLAIMS-->", line)
    elif layout == "per_sector":
        append_in_section(repo, f"aw_{sector}.md", "<!--CLAIMS-->", line)
    elif layout == "per_claim":
        write(repo, f"claims/{sess}.md", line + "\n")
    git(repo, "add", "-A"); git(repo, "commit", "-qm", f"open {sess}")

def do_close(repo, layout, sess, sector):
    line = f"- `{sess}` claim ({sector})"
    cleared = f"- `{sess}` DONE ({sector})"
    if layout == "status_quo":
        remove_line(repo, "active-work.md", line)
        append_in_section(repo, "active-work.md", "<!--CLEARED-->", cleared)
    elif layout == "per_sector":
        remove_line(repo, f"aw_{sector}.md", line)
        append_in_section(repo, f"aw_{sector}.md", "<!--CLEARED-->", cleared)
    elif layout == "per_claim":
        os.remove(os.path.join(repo, f"claims/{sess}.md"))
    git(repo, "add", "-A"); git(repo, "commit", "-qm", f"close {sess}")

def merge_to_main(repo, branch):
    """Merge branch into main; return True if conflict occurred."""
    git(repo, "checkout", "-q", "main")
    r = git(repo, "merge", "--no-ff", "--no-edit", branch, check=False)
    if r.returncode != 0:
        # conflict: abort and force-take branch so the sim can continue
        git(repo, "merge", "--abort", check=False)
        git(repo, "merge", "-q", "--no-ff", "--no-edit", "-X", "theirs", branch, check=False)
        return True
    return False

def pick_sector(rng):
    r = rng.random(); c = 0.0
    for s, w in SECTOR_WEIGHTS.items():
        c += w
        if r <= c: return s
    return "S1"

def run_trial(layout, n_sessions, concurrency, rng):
    repo = init_repo(layout)
    try:
        git(repo, "branch", "-M", "main")
    except Exception:
        pass
    sessions = [(f"sess{i:03d}", pick_sector(rng)) for i in range(n_sessions)]
    open_branches = []   # list of (branch, sess, sector)
    conflicts = 0; merges = 0
    idx = 0
    def open_one():
        nonlocal idx
        sess, sector = sessions[idx]; idx += 1
        br = f"b_{sess}"
        git(repo, "checkout", "-q", "main")
        git(repo, "checkout", "-q", "-b", br)
        do_open(repo, layout, sess, sector)
        open_branches.append((br, sess, sector))
    def close_one():
        nonlocal conflicts, merges
        br, sess, sector = open_branches.pop(0)
        git(repo, "checkout", "-q", br)
        do_close(repo, layout, sess, sector)
        merges += 1
        if merge_to_main(repo, br): conflicts += 1
    # fill the pipeline, then steady-state: close oldest, open next
    while idx < n_sessions:
        if len(open_branches) < concurrency:
            open_one()
        else:
            close_one()
    while open_branches:
        close_one()
    shutil.rmtree(repo, ignore_errors=True)
    return merges, conflicts

def main():
    rng = random.Random(1234)
    n_sessions = 60          # ~ the observed claim volume
    trials = 8
    print(f"sessions/trial={n_sessions}  trials={trials}  "
          f"sector_weights={SECTOR_WEIGHTS}\n")
    for concurrency in (2, 3, 5):
        print(f"=== concurrency = {concurrency} simultaneous open sessions ===")
        for layout in ("status_quo", "per_sector", "per_claim"):
            tot_m = tot_c = 0
            for t in range(trials):
                m, c = run_trial(layout, n_sessions, concurrency,
                                 random.Random(rng.random()))
                tot_m += m; tot_c += c
            rate = tot_c / tot_m * 100 if tot_m else 0
            print(f"  {layout:11s}: {tot_c:4d} conflicts / {tot_m:4d} merges "
                  f"= {rate:5.1f}% conflict rate")
        print()

if __name__ == "__main__":
    main()
