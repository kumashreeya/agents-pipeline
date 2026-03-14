"""
Agent Self-Evaluation — measures how well the quality agent predicts correctness.
Builds confusion matrix, precision, recall, F1 for the quality agent's judgments.
This is a meta-evaluation: evaluating the evaluator.
"""
import json
import os


def evaluate_quality_agent(results):
    """
    Given experiment results, build a confusion matrix for the quality agent.
    Compares quality_verdict against actual correctness.
    
    PASS verdict + correct code = True Positive (agent correctly approved good code)
    PASS verdict + wrong code   = False Positive (agent approved bad code — DANGEROUS)
    FAIL verdict + wrong code   = True Negative (agent correctly rejected bad code)
    FAIL verdict + correct code = False Negative (agent rejected good code — WASTEFUL)
    """

    confusion = {'TP': 0, 'FP': 0, 'TN': 0, 'FN': 0}
    details = []

    for r in results:
        verdict = r.get('quality_verdict', 'UNKNOWN')
        correct = r.get('correct', False)

        # Map verdicts: PASS = positive, everything else = negative
        agent_says_good = verdict == 'PASS'

        if agent_says_good and correct:
            category = 'TP'
        elif agent_says_good and not correct:
            category = 'FP'
        elif not agent_says_good and not correct:
            category = 'TN'
        else:
            category = 'FN'

        confusion[category] += 1
        details.append({
            'task_id': r.get('task_id', '?'),
            'workflow': r.get('workflow', '?'),
            'verdict': verdict,
            'correct': correct,
            'category': category,
        })

    # Calculate metrics
    tp, fp, tn, fn = confusion['TP'], confusion['FP'], confusion['TN'], confusion['FN']
    total = tp + fp + tn + fn

    precision = round(tp / (tp + fp), 3) if (tp + fp) > 0 else 0
    recall = round(tp / (tp + fn), 3) if (tp + fn) > 0 else 0
    f1 = round(2 * precision * recall / (precision + recall), 3) if (precision + recall) > 0 else 0
    accuracy = round((tp + tn) / total, 3) if total > 0 else 0

    # False positive rate — how often does it approve bad code?
    fpr = round(fp / (fp + tn), 3) if (fp + tn) > 0 else 0

    # False negative rate — how often does it reject good code?
    fnr = round(fn / (fn + tp), 3) if (fn + tp) > 0 else 0

    return {
        'confusion_matrix': confusion,
        'total': total,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'false_positive_rate': fpr,
        'false_negative_rate': fnr,
        'interpretation': {
            'precision': f"When agent says PASS, code is actually correct {precision*100}% of the time",
            'recall': f"Agent correctly identifies {recall*100}% of correct code",
            'fpr': f"Agent approves bad code {fpr*100}% of the time (DANGER metric)",
            'fnr': f"Agent rejects good code {fnr*100}% of the time (WASTE metric)",
        },
        'details': details,
    }


def evaluate_per_workflow(results):
    """Evaluate quality agent accuracy per workflow."""
    workflows = sorted(set(r['workflow'] for r in results))
    per_wf = {}

    for wf in workflows:
        wf_results = [r for r in results if r['workflow'] == wf]
        per_wf[wf] = evaluate_quality_agent(wf_results)

    return per_wf


def evaluate_test_agent(results):
    """
    Evaluate test agent: do AI-generated tests agree with HumanEval correctness?
    
    High test pass rate + correct code = Tests are good validators
    High test pass rate + wrong code   = Tests miss bugs (DANGEROUS)
    Low test pass rate + wrong code     = Tests catch bugs (GOOD)
    Low test pass rate + correct code   = Tests have false alarms
    """

    categories = {
        'good_validator': 0,
        'misses_bugs': 0,
        'catches_bugs': 0,
        'false_alarm': 0,
    }

    for r in results:
        correct = r.get('correct', False)
        pass_rate = r.get('test_pass_rate', 0)
        tests_say_good = pass_rate >= 0.8

        if tests_say_good and correct:
            categories['good_validator'] += 1
        elif tests_say_good and not correct:
            categories['misses_bugs'] += 1
        elif not tests_say_good and not correct:
            categories['catches_bugs'] += 1
        else:
            categories['false_alarm'] += 1

    total = sum(categories.values())
    bug_detection_rate = round(categories['catches_bugs'] / (categories['catches_bugs'] + categories['misses_bugs']), 3) if (categories['catches_bugs'] + categories['misses_bugs']) > 0 else 0

    return {
        'categories': categories,
        'total': total,
        'bug_detection_rate': bug_detection_rate,
        'test_reliability': round((categories['good_validator'] + categories['catches_bugs']) / total, 3) if total > 0 else 0,
        'interpretation': {
            'bug_detection': f"AI tests catch {bug_detection_rate*100}% of actual bugs",
            'misses': f"AI tests miss bugs in {categories['misses_bugs']} cases (code wrong but tests pass)",
        },
    }


def print_evaluation(results):
    """Print full agent evaluation report."""

    print(f"\n{'='*70}")
    print("AGENT SELF-EVALUATION REPORT")
    print(f"{'='*70}")

    # Quality agent evaluation
    qa = evaluate_quality_agent(results)
    print(f"\n1. QUALITY AGENT EVALUATION")
    print(f"   (Does quality verdict predict correctness?)")
    print(f"   {'-'*60}")
    cm = qa['confusion_matrix']
    print(f"                    Code CORRECT    Code WRONG")
    print(f"   Agent PASS       {cm['TP']:<15} {cm['FP']:<15} (FP = approved bad code)")
    print(f"   Agent FAIL       {cm['FN']:<15} {cm['TN']:<15} (FN = rejected good code)")
    print(f"")
    print(f"   Accuracy:    {qa['accuracy']}  ({qa['accuracy']*100}% overall correct)")
    print(f"   Precision:   {qa['precision']}  ({qa['interpretation']['precision']})")
    print(f"   Recall:      {qa['recall']}  ({qa['interpretation']['recall']})")
    print(f"   F1 Score:    {qa['f1_score']}")
    print(f"   FP Rate:     {qa['false_positive_rate']}  ({qa['interpretation']['fpr']})")
    print(f"   FN Rate:     {qa['false_negative_rate']}  ({qa['interpretation']['fnr']})")

    # Per workflow
    per_wf = evaluate_per_workflow(results)
    print(f"\n2. QUALITY AGENT PER WORKFLOW")
    print(f"   {'-'*60}")
    print(f"   {'Workflow':<18} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<10} {'FPR':<10}")
    for wf, ev in per_wf.items():
        print(f"   {wf:<18} {ev['accuracy']:<10} {ev['precision']:<10} {ev['recall']:<10} {ev['f1_score']:<10} {ev['false_positive_rate']:<10}")

    # Test agent evaluation
    ta = evaluate_test_agent(results)
    print(f"\n3. TEST AGENT EVALUATION")
    print(f"   (Do AI-generated tests catch actual bugs?)")
    print(f"   {'-'*60}")
    cats = ta['categories']
    print(f"   Good validator (tests pass + code correct): {cats['good_validator']}")
    print(f"   Catches bugs (tests fail + code wrong):     {cats['catches_bugs']}")
    print(f"   Misses bugs (tests pass + code WRONG):      {cats['misses_bugs']}  ← DANGEROUS")
    print(f"   False alarm (tests fail + code correct):    {cats['false_alarm']}")
    print(f"")
    print(f"   Bug detection rate: {ta['bug_detection_rate']}  ({ta['interpretation']['bug_detection']})")
    print(f"   Test reliability:   {ta['test_reliability']}")


if __name__ == "__main__":
    results_dir = "experiment_results"
    files = sorted([f for f in os.listdir(results_dir) if f.endswith('.json')])
    if files:
        with open(os.path.join(results_dir, files[-1]), 'r') as f:
            results = json.load(f)
        print(f"Loaded {len(results)} results from {files[-1]}")
        print_evaluation(results)
