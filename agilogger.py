import json
import re
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen, build_opener


FILE = "test_12_entries.log"
BASE_URL = "http://agilefant.cosc.canterbury.ac.nz:8080/agilefant302/"
ITERATION_ID = 76

patterns = {
	'COMMIT': re.compile("commit ([a-f0-9]{40})"),
	'AUTHOR': re.compile("Author: (.*) <(.*)>"),
	'DATE': re.compile("Date: (.*)"),
	'STORY': re.compile("#story\[([0-9]+)\]"),
	'TASK': re.compile("!task\[([a-zA-Z]+)\]"),
	'TIME_SPENT': re.compile("Took (?:([0-9]+) hours? )?([0-9]+) minutes?"),
	'TASK_CODE': re.compile("([a-zA-Z]+):")
}

urls = {
	'LOGIN': "login.jsp",
	'SECURITY_CHECK': "j_spring_security_check",
	'LOGOUT': "j_spring_security_logout?exit=Logout",
	'ITERATION_DATA': "ajax/iterationData.action?iterationId={}",
	'RETRIEVE_EFFORT_ENTRIES': "ajax/retrieveTaskHourEntries.action?parentObjectId={}",
	'LOG_TASK_EFFORT': "ajax/logTaskEffort.action"
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


def find_task_id(iteration_data, story_id, task_code):
	for story in iteration_data['rankedStories']:
		if story['id'] == story_id:
			for task in story['tasks']:
				match = patterns['TASK_CODE'].match(task['name'])
				if match and match.group(1) == task_code:
					return task['id']
	return None


def get_jsession_id():
	res = urlopen(BASE_URL + urls['LOGIN'])
	cookies = res.getheader('Set-Cookie')
	return cookies[cookies.find("JSESSIONID=") + len("JSESSIONID="):cookies.find(";")]


def login(jsession_id, username, password):
	post_fields = {
		'j_username': username,
		'j_password': password
	}

	request = Request(BASE_URL + urls['SECURITY_CHECK'], urlencode(post_fields).encode())
	opener = build_opener()
	opener.addheaders.append(("Cookie", "JSESSIONID={}".format(jsession_id)))
	res = opener.open(request)
	print("Security check (login) response code: {}".format(res.getcode()))


def logout(jsession_id):
	opener = build_opener()
	opener.addheaders.append(("Cookie", "JSESSIONID={}".format(jsession_id)))
	res = opener.open(BASE_URL + urls['LOGOUT'])
	print("Logout response code: {}".format(res.getcode()))


def get_iteration_data(jsession_id, iteration_id):
	try:
		opener = build_opener()
		opener.addheaders.append(("Cookie", "JSESSIONID={}".format(jsession_id)))
		res = opener.open(BASE_URL + urls['ITERATION_DATA'].format(iteration_id))
		return json.loads(res.read().decode())
	except ValueError:
		print("An error occurred when getting the iteration data. Check that the iteration id provided is correct.")
		return None


def main():
	# with open(FILE, 'r') as file:
	# 	commit_strings = separate_commits(file.read())
	#
	# for commit in commit_strings:
	# 	print(str(parse_commit(commit)) + "\n")

	jsession_id = get_jsession_id()
	print(jsession_id)
	login(jsession_id, "USERNAME", "PASSWORD")
	iteration = get_iteration_data(jsession_id, ITERATION_ID)
	logout(jsession_id)

	for story in iteration['rankedStories']:
		print("Story {}: {}".format(story['id'], story['name']))
		for task in story['tasks']:
			task['name'] = "a: " + task['name']
			print("\tTask {}: {}".format(task['id'], task['name']))

	print(find_task_id(iteration, 358, "a"))


if __name__ == '__main__':
	main()
