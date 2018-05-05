import re
from datetime import datetime


FILE = "test_12_entries.log"

patterns = {
	'COMMIT': re.compile("commit ([a-f0-9]{40})"),
	'AUTHOR': re.compile("Author: (.*) <(.*)>"),
	'DATE': re.compile("Date: (.*)"),
	'STORY': re.compile("#story\[([0-9]+)\]"),
	'TASK': re.compile("!task\[([a-zA-Z]+)\]"),
	'TIME_SPENT': re.compile("Took (?:([0-9]+) hours? )?([0-9]+) minutes?")
}


class Commit:
	def __init__(self, hash, author, email, date, description):
		self.commit_hash = hash
		self.author = author
		self.email = email
		self.date = datetime.strptime(date, "%a %b %d %H:%M:%S %Y %z")
		self.description = description
		self.tags = self.get_tags()

	def get_tags(self):
		tags = dict()

		match = patterns['STORY'].search(self.description)
		if match:
			tags['story'] = int(match.group(1))

		match = patterns['TASK'].search(self.description)
		if match:
			tags['task'] = match.group(1)

		tags['commits'] = self.commit_hash[:7]

		return tags

	def get_mins_spent(self):
		spent = 0

		match = patterns['TIME_SPENT'].search(self.description)
		if match:
			hours = match.group(1)
			mins = match.group(2)
			if mins:
				spent += int(mins)
			if hours:
				spent += int(hours) * 60
		return spent

	def __str__(self):
		return "Commit {} by {} <{}>\n{}\n{}\nTags: {}\nTime spent: {} mins"\
			.format(self.commit_hash, self.author, self.email, self.date, self.description, str(self.tags),
					self.get_mins_spent())


class EffortEntry:
	def __init__(self, date, minutes_spent, description, story_id, task_id, user_id):
		pass


def separate_commits(log):
	commit_strings = []

	positions = []
	for match in patterns['COMMIT'].finditer(log):
		positions.append(match.start())
	positions.append(len(log))

	for i in range(len(positions) - 1):
		commit_strings.append(log[positions[i]:positions[i+1]])

	return commit_strings


def parse_commit(text):
	commit = dict()

	for line in text.split("\n"):
		if patterns['COMMIT'].match(line):
			commit['hash'] = patterns['COMMIT'].match(line).group(1)
			
		elif patterns['AUTHOR'].match(line):
			commit['author'], commit['email'] = patterns['AUTHOR'].match(line).groups()

		elif patterns['DATE'].match(line):
			commit['date'] = patterns['DATE'].match(line).group(1).strip()

		else:
			if line != "\n" and line != "":
				if 'description' in commit:
					commit['description'] += " " + line.strip()
				else:
					commit['description'] = line.strip()

	return Commit(**commit)


def main():
	with open(FILE, 'r') as file:
		commit_strings = separate_commits(file.read())

	for commit in commit_strings:
		print(str(parse_commit(commit)) + "\n")


if __name__ == '__main__':
	main()
