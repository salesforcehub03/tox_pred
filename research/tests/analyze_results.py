import json
import os

# Point to data folder
data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'validation_results.json')
report_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'analysis_report.txt')

data = json.load(open(data_path))
c = [d for d in data if d['status'] == 'COMPLETE']
failed = [d for d in data if d['status'] != 'COMPLETE']

lines = []
lines.append(f"Completed: {len(c)}/{len(data)}")
if failed:
    for f in failed:
        lines.append(f"  FAILED: {f['drug']} - {f.get('error', f['status'])}")

ot = sum(d['organ_risk']['_aggregate']['score'] for d in c)
om = sum(d['organ_risk']['_aggregate']['max_score'] for d in c)
lines.append(f"\nOverall Organ Accuracy: {ot}/{om} = {ot/om*100:.1f}%")

for organ in ['liver', 'lung', 'kidney', 'heart', 'brain']:
    scores = [d['organ_risk'][organ]['accuracy'] for d in c]
    avg = sum(scores) / len(scores) * 100
    lines.append(f"  {organ.capitalize():<10}: {avg:.0f}%")

avg_ae = sum(d['ae_overlap']['overlap_pct'] for d in c) / len(c)
lines.append(f"\nAverage AE Overlap: {avg_ae:.1f}%")

lines.append(f"\n{'Drug':<30} {'Organ%':>7} {'AE%':>6} {'Conc%':>6}")
lines.append("-" * 55)
for d in sorted(c, key=lambda x: x['organ_risk']['_aggregate']['accuracy_pct'], reverse=True):
    conc = d['ae_concordance'].get('concordance_pct', 0)
    lines.append(f"  {d['drug'][:28]:<28} {d['organ_risk']['_aggregate']['accuracy_pct']:>6}% {d['ae_overlap']['overlap_pct']:>5}% {conc:>5}%")

lines.append(f"\nCRITICAL MISSES (off by 2+ levels):")
miss_count = 0
for d in c:
    for o in ['liver', 'lung', 'kidney', 'heart', 'brain']:
        r = d['organ_risk'][o]
        if r['accuracy'] == 0.0:
            miss_count += 1
            lines.append(f"  {d['drug'][:27]:<28} {o:<10} Expected: {r['expected']:<10} Got: {r['predicted']} ({r['predicted_pct']}%)")
lines.append(f"Total critical misses: {miss_count}")

# Patterns in misses
lines.append(f"\nMISS PATTERN ANALYSIS:")
miss_by_organ = {}
miss_direction = {"under": 0, "over": 0}
for d in c:
    for o in ['liver', 'lung', 'kidney', 'heart', 'brain']:
        r = d['organ_risk'][o]
        if r['accuracy'] == 0.0:
            miss_by_organ[o] = miss_by_organ.get(o, 0) + 1
            exp_ord = {"none": 0, "low": 1, "moderate": 2, "high": 3}
            e = exp_ord.get(r['expected'].lower(), 0)
            p = exp_ord.get(r['predicted'].lower(), 0)
            if p < e:
                miss_direction["under"] += 1
            else:
                miss_direction["over"] += 1

for organ, cnt in sorted(miss_by_organ.items(), key=lambda x: x[1], reverse=True):
    lines.append(f"  {organ.capitalize()}: {cnt} misses")
lines.append(f"  Under-prediction: {miss_direction['under']}")
lines.append(f"  Over-prediction: {miss_direction['over']}")

# DeepChem status
lines.append(f"\nDEEPCHEM STATUS:")
for d in c:
    note = d.get('deepchem_note', '')
    mode = "TRUE AI" if "TRUE" in note else "SIMULATION"
    lines.append(f"  {d['drug'][:28]:<30} {mode}")

with open(report_path, 'w') as f:
    f.write('\n'.join(lines))
print("Done - written to analysis_report.txt")
