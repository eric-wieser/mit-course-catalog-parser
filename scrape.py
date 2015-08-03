from __future__ import unicode_literals
import requests
import bs4
import re
from pprint import pprint

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

page = requests.get('http://student.mit.edu/catalog/m6a.html')

soup = bs4.BeautifulSoup(page.text)

def wrap(elems):
	res = soup.new_tag('div')
	for e in elems:
		res.append(e)
	return res

def process_page(soup):
	a_tags = soup.select('table table a[name]')

	def chunk():
		a_iter = iter(a_tags)

		# get the first tag
		curr = next(a_iter)
		while curr:
			next_a_tag = next(a_iter)

			res = []

			# keep going till we find a header, then until the next a tag
			header_found = False
			while True:
				res.append(curr)
				curr = curr.nextSibling

				if isinstance(curr, bs4.Tag) and curr.name == 'h3':
					header_found = True

				if curr == next_a_tag:
					if header_found:
						break
					else:
						next_a_tag = next(a_iter, None)

				if isinstance(curr, bs4.Comment) and curr.string == 'end':
					curr = next_a_tag
					break


			yield wrap(res)

	return chunk()

def process_chunk(chunk):

	title_elem = chunk.find('h3')

	course = Course(numbers=[a.attrs['name'] for a in chunk.select('a[name]')])
	course.title = re.match(
		r'(?s)^(?:\d+.[-A-Z0-9.]+(?:, )?)+ (.*?)\s*$',
		title_elem.text
	).group(1)

	def sections():
		so_far = []
		for c in title_elem.next_siblings:
			if isinstance(c, bs4.Tag) and c.name == 'br':
				yield wrap(so_far)
				so_far = []
			else:
				so_far.append(c)

		if so_far:
			yield wrap(so_far)

	sections = sections()

	img_section = next(sections)
	course.tags = [
		re.match(r'/icns/(.*)\.gif', img.attrs['src']).group(1)
		for img in img_section.find_all('img')
	]

	before_descr = True
	for section in sections:
		first = next(section.children)

		if isinstance(first, bs4.Tag):
			if first.name == 'i':
				if course.lecturers: raise ValueError
				course.lecturers = first.text.split(', ')
				continue

			if first.name == 'img' and first.attrs['src'] == '/icns/hr.gif':
				before_descr = False
				continue

			if first.name == 'a' and 'editcookie.cgi' in first.attrs['href']:
				continue

		if isinstance(first, bs4.NavigableString):
			if first.string.startswith('Prereq'):
				if course.prereq_numbers: raise ValueError
				course.prereq_numbers = [p.get_text() for p in section.find_all('a')]
				continue

			m = re.match(r'Units:? (.*)', first.string)
			if m:
				if course.unit_str: raise ValueError
				course.unit_str = m.group(1)
				continue

			if first.string.startswith('(Same subject as'):
				if course.aliases: raise ValueError
				course.aliases = [p.get_text() for p in section.find_all('a')]
				continue

			if first.string.startswith('URL:'):
				course.url = section.find('a').get_text()
				continue

			if not before_descr and not course.description:
				course.description = section
				continue


		# print "\t", section

	return course

for chunk in process_page(soup):
	print process_chunk(chunk).prettify()