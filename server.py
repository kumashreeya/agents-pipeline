"""
Flask server connecting dashboard to pipeline.
"""
import json
import os
import time
import threading
from flask import Flask, jsonify, request, send_file

app = Flask(__name__)

experiment_state = {
    "status": "idle",
    "progress": "",
    "results": [],
}

@app.route('/')
def dashboard():
    return send_file('dashboard.html')

@app.route('/api/status')
def status():
    return jsonify(experiment_state)

@app.route('/api/run', methods=['POST'])
def run_experiment_api():
    data = request.json
    from_p = data.get('from', 0)
    to_p = data.get('to', 4)
    max_iter = data.get('max_iterations', 3)

    if experiment_state["status"] == "running":
        return jsonify({"error": "Experiment already running"}), 400

    experiment_state["status"] = "running"
    experiment_state["progress"] = "Starting..."
    experiment_state["results"] = []

    thread = threading.Thread(target=_run_experiment, args=(from_p, to_p, max_iter), daemon=True)
    thread.start()

    return jsonify({"message": f"Started on HumanEval/{from_p} to HumanEval/{to_p}"})

def _run_experiment(from_p, to_p, max_iter):
    try:
        from human_eval.data import read_problems
        from workflows.workflow_a import build_workflow_a
        from workflows.workflow_b import build_workflow_b
        from workflows.workflow_c import build_workflow_c

        problems = read_problems()
        workflows = [
            ("A_sequential", build_workflow_a),
            ("B_iterative", build_workflow_b),
            ("C_gated", build_workflow_c),
        ]

        task_ids = [f"HumanEval/{i}" for i in range(from_p, to_p + 1)]
        total_runs = len(task_ids) * len(workflows)
        current_run = 0

        for task_id in task_ids:
            problem = problems[task_id]
            for wf_name, wf_builder in workflows:
                current_run += 1
                experiment_state["progress"] = f"Running {wf_name} on {task_id} ({current_run}/{total_runs})"
                print(f"[SERVER] {experiment_state['progress']}")

                state = {
                    "task_id": task_id, "prompt": problem["prompt"],
                    "entry_point": problem["entry_point"],
                    "code": "", "code_file": "", "syntax_valid": False,
                    "quality_verdict": "", "quality_score": 0, "quality_feedback": "",
                    "quality_plan": {}, "quality_measurements": {},
                    "test_pass_rate": 0, "test_coverage": 0,
                    "test_total": 0, "test_passed": 0, "test_smells": 0, "test_flaky": False,
                    "correct": False,
                    "iteration": 0, "max_iterations": max_iter, "total_tokens": 0,
                    "ai_dead_code": 0, "ai_hallucinated_imports": 0, "ai_duplicates": 0,
                }

                start = time.time()
                try:
                    wf = wf_builder()
                    result = wf.invoke(state)
                    elapsed = round(time.time() - start, 1)
                    experiment_state["results"].append({
                        "workflow": wf_name, "task_id": result["task_id"],
                        "iterations": result["iteration"], "correct": result["correct"],
                        "quality_verdict": result["quality_verdict"],
                        "quality_score": result["quality_score"],
                        "test_pass_rate": result["test_pass_rate"],
                        "test_passed": result["test_passed"], "test_total": result["test_total"],
                        "test_coverage": result["test_coverage"],
                        "test_smells": result.get("test_smells", 0),
                        "ai_dead_code": result.get("ai_dead_code", 0),
                        "ai_hallucinated_imports": result.get("ai_hallucinated_imports", 0),
                        "ai_duplicates": result.get("ai_duplicates", 0),
                        "time_seconds": elapsed, "error": None,
                    })
                    print(f"[SERVER] Done: correct={result['correct']}, quality={result['quality_verdict']}, time={elapsed}s")
                except Exception as e:
                    elapsed = round(time.time() - start, 1)
                    print(f"[SERVER] Error in {wf_name}: {e}")
                    experiment_state["results"].append({
                        "workflow": wf_name, "task_id": task_id,
                        "iterations": 0, "correct": False,
                        "quality_verdict": "ERROR", "quality_score": 0,
                        "test_pass_rate": 0, "test_passed": 0, "test_total": 0,
                        "test_coverage": 0, "test_smells": 0,
                        "ai_dead_code": 0, "ai_hallucinated_imports": 0, "ai_duplicates": 0,
                        "time_seconds": elapsed, "error": str(e),
                    })

        os.makedirs("experiment_results", exist_ok=True)
        with open("experiment_results/latest.json", "w") as f:
            json.dump(experiment_state["results"], f, indent=2, default=str)

        experiment_state["status"] = "done"
        experiment_state["progress"] = f"Completed {total_runs} runs"
        print(f"[SERVER] Experiment complete!")

    except Exception as e:
        experiment_state["status"] = "error"
        experiment_state["progress"] = f"Error: {str(e)}"
        print(f"[SERVER] Experiment error: {e}")

@app.route('/api/results')
def get_results():
    if os.path.exists("experiment_results/latest.json"):
        with open("experiment_results/latest.json", 'r') as f:
            return jsonify(json.load(f))
    return jsonify(experiment_state["results"])

@app.route('/api/results/list')
def list_results():
    d = "experiment_results"
    if not os.path.exists(d):
        return jsonify([])
    return jsonify(sorted([f for f in os.listdir(d) if f.endswith('.json')]))

@app.route('/api/results/<filename>')
def get_result_file(filename):
    p = os.path.join("experiment_results", filename)
    if os.path.exists(p):
        with open(p, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    print("Dashboard server starting...")
    print("Open http://127.0.0.1:5000 in your browser")
    print()
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
