import json, sys
d = json.load(open(sys.argv[1]))['jobs']
for j in d:
    print('== JOB:', j['name'], '({})'.format(j['conclusion']), '==')
    for s in j.get('steps', []):
        print('  step:', s['name'], '->', s['conclusion'])
