#! python3

from pathlib import Path
from collections import namedtuple
from pprint import pprint
import itertools

import requests

Group = namedtuple('Group', 'name courses')
Course = namedtuple('Course', 'mit cued recommended')

mapping_file = Path('cued.txt')

class AttrDict(dict):
	def __getattr__(self, attr):
		return self[attr]

def get_course_mappings(mapping_file=mapping_file):
	groups = []

	with mapping_file.open(encoding='utf8') as f:
		current_group = None


		for line in f:
			line = line.rstrip()
			if not line:
				continue

			if not line.startswith('\t'):
				groups.append(Group(name=line, courses=set()))

			else:
				parts = line[1:].split('\t')
				cued = parts[0] or None
				mit = parts[1] or None
				recommended = False
				if len(parts) == 3:
					assert parts[2] == 'X', "Crap"
					recommended = True

				groups[-1].courses.add(Course(mit, cued, recommended))

	return groups

def get_courses(term):
	return [
		AttrDict(x)
		for x in requests.get('http://coursews.mit.edu/coursews/', params=dict(term=term)).json()['items']
		if x['type'] == 'Class'
	]

def get_all_courses():
	return get_courses('2015FA') + get_courses('2015SP') + get_courses('2015SU')

courses = get_all_courses()
mapping = get_course_mappings()

course_keys = {c.id for c in courses}
mapping_keys = {c for group in mapping for c in group.courses}

matched = set()
missed = set()

def mutations(m):
	yield m

	if m.endswith('J'):
		yield m[:-1]

	if '/' in m:
		parts = [p.split('/') for p in m.split('.')]
		for new_parts in itertools.product(*parts):
			new_id = '.'.join(new_parts)
			yield new_id

	if len(m.split('.')[1]) == 2:
		yield m.replace('.', '.0')

for m in mapping_keys:
	if any(mut in course_keys for mut in mutations(m.mit)):
		matched.add(m)
	else:
		missed.add(m)

print("Matched {} of {}:".format(len(matched), len(mapping_keys)))
for c in sorted(matched, key=lambda t: (t.recommended, t.cued is not None, t.mit)):
	print("\t",c)

print("Missed:")
for c in sorted(missed, key=lambda t: (t.recommended, t.cued is not None, t.mit)):
	print("\t",c)

print("All MIT courses:")
for c in sorted(course_keys):
	print("\t", c)
