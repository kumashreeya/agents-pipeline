"""
Mutation Score Measurement using mutmut.
"""
import subprocess
import os
import re
import shutil


def measure_mutation_score(code_file, test_file, timeout=120):
    code_dir = os.path.dirname(os.path.abspath(code_file))
    code_name = os.path.basename(code_file)
    test_name = os.path.basename(test_file)

    setup_file = os.path.join(code_dir, "setup.cfg")
    wrote_setup = False
    if not os.path.exists(setup_file):
        with open(setup_file, "w") as f:
            f.write(f"[mutmut]\npaths_to_mutate={code_name}\ntests_dir=./\ntest_command=python -m pytest {test_name} -x -q --tb=no\n")
        wrote_setup = True

    try:
        result = subprocess.run(
            ["mutmut", "run"],
            capture_output=True, text=True,
            timeout=timeout, cwd=code_dir
        )

        output = result.stdout + "\n" + result.stderr

        # Parse the emoji-based output format:
        # 10/10  🎉 7 🫥 0  ⏰ 0  🤔 0  🙁 3  🔇 0  🧙 0
        killed = 0
        survived = 0
        timeout_count = 0
        suspicious = 0
        total = 0

        for line in output.split("\n"):
            # Look for the summary line with emojis
            if "🎉" in line:
                parts = line.strip()
                # Extract killed (🎉)
                m = re.search(r'🎉\s*(\d+)', parts)
                if m: killed = int(m.group(1))
                # Extract survived (🙁)
                m = re.search(r'🙁\s*(\d+)', parts)
                if m: survived = int(m.group(1))
                # Extract timeout (⏰)
                m = re.search(r'⏰\s*(\d+)', parts)
                if m: timeout_count = int(m.group(1))
                # Extract suspicious (🤔)
                m = re.search(r'🤔\s*(\d+)', parts)
                if m: suspicious = int(m.group(1))
                # Extract total from X/X pattern
                m = re.search(r'(\d+)/(\d+)', parts)
                if m: total = int(m.group(2))

        if total == 0:
            total = killed + survived + timeout_count + suspicious
        score = round(killed / total, 4) if total > 0 else 0

        return {
            "metric": "mutation_score",
            "score": score,
            "killed": killed,
            "survived": survived,
            "timeout": timeout_count,
            "suspicious": suspicious,
            "total_mutants": total,
        }

    except subprocess.TimeoutExpired:
        return {"metric": "mutation_score", "score": 0, "error": f"timed out after {timeout}s", "total_mutants": 0}
    except Exception as e:
        return {"metric": "mutation_score", "score": 0, "error": str(e), "total_mutants": 0}
    finally:
        if wrote_setup and os.path.exists(setup_file):
            os.remove(setup_file)
        cache_dir = os.path.join(code_dir, ".mutmut-cache")
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir, ignore_errors=True)
