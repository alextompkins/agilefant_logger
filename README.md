# agilogger
A logging tool for SENG302 students to automatically insert Git commit messages straight into Agilefant, including correct date/time and time spent details.


Commits must relate only to a single story/task, which can be entered manually or put into your commit messages using this syntax:

`#story[782]` will be mapped to a story with ID 782.

`!task[b]` will be mapped to a task with a description such as "b: Implement dinosaurs".

Both of these tags must be valid or their values will have to be entered manually when Agilogger parses each commit.

To use, follow these steps:

1. Clone this repo and copy `agilogger.py` & `agilogger_config.py` into your SENG302 project's root directory.
2. Edit the value of `ITERATION_ID` in `agilogger_config.py` to the ID of your current sprint (can be found in Agilefant).
3. Run `python ./agilogger.py` and follow the instructions.
4. (Optional) Download [Darkyenus Time Tracker](https://plugins.jetbrains.com/plugin/9286-darkyenus-time-tracker) plugin for IntelliJ to automatically track time spent on each commit.
5. (Optional) Enable the setting to insert time spent into the commit message. Agilogger will parse this automatically.

Master version is for Python 3, but there is also a branch with a version available for Python 2.
