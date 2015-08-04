#! python3

class Course(object):
	by_number = {}
	def __init__(self, numbers):
		self.numbers = numbers
		self.title = None
		self.description = None
		self.prereq_numbers = []
		self.aliases = []
		self.unit_str = None
		self.tags = []
		self.lecturers = []

		for number in numbers:
			self.by_number[number] = self

	def __repr__(self):
		return "<{}: {}>".format(', '.join(self.numbers), self.title)

	@property
	def prereqs(self):
		for pn in self.prereq_numbers:
			yield self.by_number.get(pn, pn)


	def prettify(self):
		return '\n'.join([
			'{numbers}: {name}',
			'\tTags: {tags}',
			'\tLecturers: {lecturers}',
			'\tUnits: {unit_str}',
			'\tPrereqs:',
			'\t\t{prereqs}'
		]).format(
			numbers=', '.join(self.numbers),
			name=self.title,
			prereqs='\n\t\t'.join(
				p.prettify().replace('\n', '\n\t\t') if isinstance(p, Course) else p
				for p in self.prereqs
			),
			lecturers=', '.join(self.lecturers),
			tags=', '.join(self.tags),
			unit_str=self.unit_str
		)
