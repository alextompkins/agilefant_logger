import re


FILE = "test_log.txt"
BASE_URL = "http://agilefant.cosc.canterbury.ac.nz:8080/agilefant302/"
ITERATION_ID = 210
USER_ID = 540

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
