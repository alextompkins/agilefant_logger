import json
import textwrap
import subprocess
from datetime import datetime, timezone
from getpass import getpass
from urllib import urlencode
from urllib2 import Request, HTTPError, urlopen, build_opener
from agilogger_config import *


class Commit:
	def __init__(self, commit_hash, author, email, date, description):
		self.commit_hash = commit_hash
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

		tags['commits'] = self.commit_hash[:8]

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

		if spent == 0:
			return None
		else:
			return spent

	def __str__(self):
		return "Commit {} by {} <{}>\n\t{}\n\t{}\n\tTags: {}\n\tTime spent: {} mins"\
			.format(self.commit_hash[:8], self.author, self.email, self.date,
					"\n\t".join(textwrap.wrap(self.description)), str(self.tags), self.get_mins_spent())

	def build_effort_entry(self, iteration_data, user_id):
		if not ('story' in self.tags and 'task' in self.tags):
			print("This is not a valid effort entry; its commit message is missing task/story tags.")
			if input("Do you want to enter the story/task ids for this commit? (y/n): ").lower() == "y":
				self.tags['story'], self.tags['task'] = get_story_and_task_tags_from_user_input()
			else:
				raise ValueError("Task/story tag is not present, so effort entry cannot be created.")

		task_id = find_task_id(iteration_data, self.tags['story'], self.tags['task'])
		return EffortEntry(self.date, self.get_mins_spent(),
						   self.description + " #commits[{}]".format(self.tags['commits']), task_id, user_id)


class EffortEntry:
	def __init__(self, date, minutes_spent, description, task_id, user_id):
		epoch = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
		self.date = int((date - epoch).total_seconds()) * 1000
		self.minutes_spent = minutes_spent
		self.description = description
		self.task_id = task_id
		self.user_id = user_id

		if self.date is None:
			raise ValueError("This is not a valid effort entry; its commit is missing a date/time.")
		elif self.minutes_spent is None:
			user_input = get_minutes_spent_from_user_input()
			if user_input is None:
				raise ValueError("Effort entry discarded as no time spent was provided.")
			else:
				self.minutes_spent = user_input
		elif self.description is None:
			raise ValueError("This is not a valid effort entry; its commit is missing a description.")
		elif self.task_id is None:
			raise ValueError("This is not a valid effort entry; no task could be found matching the story/task tags provided.")
		elif self.user_id is None:
			raise ValueError("This is not a valid effort entry; your user ID is missing.")

	def get_post_data(self):
		return {
			"hourEntry.date": self.date,
			"hourEntry.description": self.description,
			"hourEntry.minutesSpent": self.minutes_spent,
			"parentObjectId": self.task_id,
			"userIds": self.user_id
		}

	def __str__(self):
		return ("hourEntry.date={}\n" +
				"hourEntry.description={}\n" +
				"hourEntry.minutesSpent={}\n" +
				"parentObjectId={}\n" +
				"userIds={}")\
				.format(self.date, "\n".join(textwrap.wrap(self.description)),
						self.minutes_spent, self.task_id, self.user_id)


def get_minutes_spent_from_user_input():
	print("This is not a valid effort entry; its commit message does not include the time spent.")
	if input("Do you want to enter a time spent for this commit? (y/n): ").lower() == "y":
		while True:
			try:
				time_spent = int(input("Enter the time spent on this commit (in minutes): "))
			except ValueError:
				print("Incorrect value for time spent. Enter it as an integer.")
				continue
			if time_spent <= 0:
				print("Time spent must be greater than 0.")
				continue
			else:
				# Valid input for time spent
				return time_spent

	return None


def get_story_and_task_tags_from_user_input():
	while True:
		try:
			story_id = int(input("Enter the story id (e.g. 751) for this commit: "))
		except ValueError:
			print("Story id must be an integer.")
			continue
		if story_id <= 0:
			print("Story id must be greater than 0.")
			continue
		else:
			# Valid input for story id
			break

	while True:
		task_id = input("Enter the task id for this commit (e.g. 'a'): ")
		if task_id == "":
			print("Task id must not be blank.")
			continue
		else:
			# Valid input for task id
			break

	return story_id, task_id


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
			commit['commit_hash'] = patterns['COMMIT'].match(line).group(1)
			
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
	return "Invalid username or password" not in res.read().decode()


def logout(jsession_id):
	opener = build_opener()
	opener.addheaders.append(("Cookie", "JSESSIONID={}".format(jsession_id)))
	opener.open(BASE_URL + urls['LOGOUT'])


def get_iteration_data(jsession_id, iteration_id):
	try:
		opener = build_opener()
		opener.addheaders.append(("Cookie", "JSESSIONID={}".format(jsession_id)))
		res = opener.open(BASE_URL + urls['ITERATION_DATA'].format(iteration_id))
		if res.getcode() == 200:
			return json.loads(res.read().decode())
		else:
			return None
	except HTTPError:
		return None
	except ValueError:
		return None


def find_user_id_matching_username(iteration_data, username):
	for assignee in iteration_data['assignees']:
		if assignee['initials'] == username:
			return assignee['id']
	return None


def get_effort_entries_for_task(jsession_id, task_id):
	try:
		opener = build_opener()
		opener.addheaders.append(("Cookie", "JSESSIONID={}".format(jsession_id)))
		res = opener.open(BASE_URL + urls['RETRIEVE_EFFORT_ENTRIES'].format(task_id))
		return json.loads(res.read().decode())
	except HTTPError:
		raise ValueError("That story/task does not exist.")
	except ValueError:
		print("An error occurred when getting the effort entry data for task {}.".format(task_id))
		return None


def post_effort_entry(jsession_id, entry):
	request = Request(BASE_URL + urls['LOG_TASK_EFFORT'], urlencode(entry.get_post_data()).encode())
	opener = build_opener()
	opener.addheaders.append(("Cookie", "JSESSIONID={}".format(jsession_id)))
	opener.open(request)


def main():
	if (ITERATION_ID == None):
		print("You need to set ITERATION_ID in 'agilogger_config.py'.")
		exit()

	username = input("Enter your agilefant username: ")
	password = getpass("Enter your agilefant password: ")

	commits = list()
	if 'FILE' in globals():
		print("Reading commit log from '{}'...".format(globals()['FILE']))
		with open(globals()['FILE'], 'r') as file:
			log = file.read()
	else:
		print("Using 'git log' to get commits...")
		try:
			n = int(input("How many of your recent commits should the script parse? (starting with the most recent): "))
			log = subprocess.check_output("git log -n {} --author=\"{}\" --all --reverse".format(n, username), shell=True).decode()
		except ValueError:
			print("That is not a valid number.")
			return

	commit_strings = separate_commits(log)
	for commit in commit_strings:
		commits.append(parse_commit(commit))

	jsession_id = get_jsession_id()
	if not login(jsession_id, username, password):
		print("Could not log in to agilefant with the provided username and password. \n"
			  "Check that the server is accessible and that your credentials are correct.")

	else:
		iteration_data = get_iteration_data(jsession_id, ITERATION_ID)
		if iteration_data is None:
			print("Error: No iteration with id {} exists in agilefant.".format(ITERATION_ID))

		else:
			user_id = find_user_id_matching_username(iteration_data, username)
			if user_id is None:
				print("Error: You are not assigned to the iteration with id {} in agilefant.".format(ITERATION_ID))

			else:
				for commit in commits:
					print("\n\n" + str(commit))
					try:
						new_entry = commit.build_effort_entry(iteration_data, user_id=user_id)
						current_entries = get_effort_entries_for_task(jsession_id, new_entry.task_id)
						for entry in current_entries:
							if "#commits[{}".format(commit.commit_hash[:8]) in entry['description']:
								raise ValueError("An effort entry for this commit already exists on agilefant.")
						post_effort_entry(jsession_id, new_entry)
						print("Effort entry posted to agilefant.")
					except ValueError as exc:
						print(exc)

		logout(jsession_id)


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		exit()
