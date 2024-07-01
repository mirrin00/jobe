import requests
import unittest

URL = "http://localhost/jobe/index.php/restapi/runs"


class TestChrootFeature(unittest.TestCase):
	"""
	TESTS WITH SETTED NO_RUNGUARD PARAMETR
	"""

	def test_print_current_directory(self):
		""""
		A test shows that the sourcecode (prog.py) and __student_answer__ (student.py) execute separately.
		prog.py does not execute in chroot jail
		student.py is execute in chroot jail
		"""
		data = {
			"run_spec": {
				"language_id": "python3",
				"sourcecode": "import os, subprocess, sys\n\n__student_answer__ = \"\"\"import os\r\nprint(f\\\"#Current directory (student.py): {os.getcwd()}\\\");\r\n\r\n\"\"\"\n\n\nwith open(\"student.py\", \"w\") as stud_ans:\n    print(__student_answer__, file=stud_ans);\n\nprint(f\"#Current directory (prog.py): {os.getcwd()}\");\n\nreturn_code = 0\nreturn_code = subprocess.run([\"bash\", \"compile_student.cmd\"], check=True)\n\nif  return_code != 0:\n    subprocess.run([\"bash\", \"execute_student.cmd\"])",
				"sourcefilename": "prog.py",
				"parameters": {
					"chroot_dir": "test",
					"no_runguard": {
						"language_id": "python3"
					}
				}
			}
		}

		response = requests.post(URL, json=data)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['outcome'], 15)
		print(response.json()['stdout'])

	def test_python_sqr_function(self):
		"""
		Execute __tester__.python3 program (not in chroot jail),
		then writes __student__answer__ to prog.py with added tests
		then compile and execute it in chroot jail
		"""
		data = {
			"run_spec": {
				"language_id": "python3",
				"sourcecode": "import os, subprocess, sys\n\n__student_answer__ = \"\"\"def sqr(n):\r\n    return n * n\r\n\r\n\"\"\"\n\n\n__student_answer__ += \"\"\"\nprint(sqr(10))\n\"\"\"\n__student_answer__ += \"\"\"\nprint('#<ab@17943918#@>#')\n\"\"\"\n__student_answer__ += \"\"\"\nprint(sqr(5))\n\"\"\"\n__student_answer__ += \"\"\"\nprint('#<ab@17943918#@>#')\n\"\"\"\n__student_answer__ += \"\"\"\nprint(sqr(0))\n\"\"\"\n__student_answer__ += \"\"\"\nprint('#<ab@17943918#@>#')\n\"\"\"\n__student_answer__ += \"\"\"\nprint(sqr(11))\n\"\"\"\n__student_answer__ += \"\"\"\nprint('#<ab@17943918#@>#')\n\"\"\"\n__student_answer__ += \"\"\"\nprint(sqr(1))\n\"\"\"\n\nwith open(\"student.py\", \"w\") as stud_ans:\n    print(__student_answer__, file=stud_ans);\n\n\n\nreturn_code = 0\nreturn_code = subprocess.run([\"bash\", \"compile_student.cmd\"], check=True)\n\nif  return_code != 0:\n    subprocess.run([\"bash\", \"execute_student.cmd\"])",
				"sourcefilename": "__tester__.python3",
				"input": "",
				"file_list": [],
				"parameters": {
					"chroot_dir": "test",
					"no_runguard": {
						"language_id": "python3",
						"filename": "prog.py"
					}
				}
			}
		}

		response = requests.post(URL, json=data)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['outcome'], 15)
		self.assertEqual(response.json()['chroot_dir'], "test")
		self.assertEqual(response.json()['stdout'], "100\n#<ab@17943918#@>#\n25\n#<ab@17943918#@>#\n0\n#<ab@17943918#@>#\n121\n#<ab@17943918#@>#\n1\n")

	def test_c_sqr_function(self):
		"""
		Execute __tester__.python3 program (not in chroot jail),
		then writes __student__answer__ to student.c with added tests
		then compile and execute it in chroot jail
		"""
		data = {
			"run_spec": {
				"language_id": "python3",
				"sourcecode": "import subprocess, sys\n\n__student_answer__ = \"\"\"#include <stdio.h>\r\n\r\nint sqr(int n) {\r\n    return n * n;\r\n}\r\n\r\n\"\"\"\n\n__student_answer__ += \"\"\"int main(){\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(10));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(5));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(0));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(11));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(1));\n\"\"\"\n__student_answer__ += \"\"\"    return 0; \\n}\"\"\"\nwith open(\"student.c\", \"w\") as stud_ans:\n    print(__student_answer__, file=stud_ans);\n\n\n\nreturn_code = 0\nreturn_code = subprocess.run([\"bash\", \"compile_student.cmd\"], check=True)\n\nif  return_code != 0:\n    subprocess.run([\"bash\", \"execute_student.cmd\"])",
				"sourcefilename": "__tester__.python3",
				"input": "",
				"file_list": [],
				"parameters": {
					"chroot_dir": "test",
					"no_runguard": {
						"language_id": "c"
					}
				}
			}
		}

		response = requests.post(URL, json=data)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['outcome'], 15)
		self.assertEqual(response.json()['chroot_dir'], "test")
		self.assertEqual(response.json()['stdout'], "100\n#<ab@17943918#@>#25\n#<ab@17943918#@>#0\n#<ab@17943918#@>#121\n#<ab@17943918#@>#1\n")

	def test_invalid_student_language(self):
		"""
		Try to execute student c program as python3
		Should return Runtime error
		"""
		data = {
			"run_spec": {
				"language_id": "python3",
				"sourcecode": "import subprocess, sys\n\n__student_answer__ = \"\"\"#include <stdio.h>\r\n\r\nint sqr(int n) {\r\n    return n * n;\r\n}\r\n\r\n\"\"\"\n\n__student_answer__ += \"\"\"int main(){\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(10));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(5));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(0));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(11));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(1));\n\"\"\"\n__student_answer__ += \"\"\"    return 0; \\n}\"\"\"\nwith open(\"student.c\", \"w\") as stud_ans:\n    print(__student_answer__, file=stud_ans);\n\n\n\nreturn_code = 0\nreturn_code = subprocess.run([\"bash\", \"compile_student.cmd\"], check=True)\n\nif  return_code != 0:\n    subprocess.run([\"bash\", \"execute_student.cmd\"])",
				"sourcefilename": "__tester__.python3",
				"input": "",
				"file_list": [],
				"parameters": {
					"chroot_dir": "test",
					"no_runguard": {
						"language_id": "python3"
					}
				}
			}
		}

		response = requests.post(URL, json=data)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['outcome'], 12)

	def test_not_supported_student_language(self):
		"""
		Supported language for no_runguard param are c, cpp and python3 only
		There is java specified
		"""
		data = {
			"run_spec": {
				"language_id": "python3",
				"sourcecode": "import subprocess, sys\n\n__student_answer__ = \"\"\"#include <stdio.h>\r\n\r\nint sqr(int n) {\r\n    return n * n;\r\n}\r\n\r\n\"\"\"\n\n__student_answer__ += \"\"\"int main(){\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(10));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(5));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(0));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(11));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(1));\n\"\"\"\n__student_answer__ += \"\"\"    return 0; \\n}\"\"\"\nwith open(\"student.c\", \"w\") as stud_ans:\n    print(__student_answer__, file=stud_ans);\n\n\n\nreturn_code = 0\nreturn_code = subprocess.run([\"bash\", \"compile_student.cmd\"], check=True)\n\nif  return_code != 0:\n    subprocess.run([\"bash\", \"execute_student.cmd\"])",
				"sourcefilename": "__tester__.python3",
				"input": "",
				"file_list": [],
				"parameters": {
					"chroot_dir": "test",
					"no_runguard": {
						"language_id": "java"
					}
				}
			}
		}

		response = requests.post(URL, json=data)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json(), "runs_post: student code language does not exist or do not supported")

	def test_not_supported_main_language(self):
		"""
		Other programs can only be compiled and executed via python3
		There is c specified
		"""
		data = {
			"run_spec": {
				"language_id": "c",
				"sourcecode": "import subprocess, sys\n\n__student_answer__ = \"\"\"#include <stdio.h>\r\n\r\nint sqr(int n) {\r\n    return n * n;\r\n}\r\n\r\n\"\"\"\n\n__student_answer__ += \"\"\"int main(){\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(10));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(5));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(0));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(11));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(1));\n\"\"\"\n__student_answer__ += \"\"\"    return 0; \\n}\"\"\"\nwith open(\"student.c\", \"w\") as stud_ans:\n    print(__student_answer__, file=stud_ans);\n\n\n\nreturn_code = 0\nreturn_code = subprocess.run([\"bash\", \"compile_student.cmd\"], check=True)\n\nif  return_code != 0:\n    subprocess.run([\"bash\", \"execute_student.cmd\"])",
				"sourcefilename": "__tester__.python3",
				"input": "",
				"file_list": [],
				"parameters": {
					"chroot_dir": "test",
					"no_runguard": {
						"language_id": "c"
					}
				}
			}
		}

		response = requests.post(URL, json=data)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json(), "runs_post: language not supported with no_runguard param")

	def test_unspecified_student_language(self):
		"""
		It is necessary to specify the student language
		There is parameters['norunguard']['language_id'] is empty
		"""

		data = {
			"run_spec": {
				"language_id": "python3",
				"sourcecode": "import subprocess, sys\n\n__student_answer__ = \"\"\"#include <stdio.h>\r\n\r\nint sqr(int n) {\r\n    return n * n;\r\n}\r\n\r\n\"\"\"\n\n__student_answer__ += \"\"\"int main(){\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(10));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(5));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(0));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(11));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(1));\n\"\"\"\n__student_answer__ += \"\"\"    return 0; \\n}\"\"\"\nwith open(\"student.c\", \"w\") as stud_ans:\n    print(__student_answer__, file=stud_ans);\n\n\n\nreturn_code = 0\nreturn_code = subprocess.run([\"bash\", \"compile_student.cmd\"], check=True)\n\nif  return_code != 0:\n    subprocess.run([\"bash\", \"execute_student.cmd\"])",
				"sourcefilename": "__tester__.python3",
				"input": "",
				"file_list": [],
				"parameters": {
					"chroot_dir": "test",
					"no_runguard": {

					}
				}
			}
		}

		response = requests.post(URL, json=data)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json(), "runs_post: no_runguard was provided, but student language_id was not")

	def test_invalid_student_filename(self):
		"""
		parameters['norunguard']['sourcefilename'] specifies the name of the student file where the student code will be written to
		It is not necessary to specify (student.* by default), but if soucefilename is invalid server will return 400
		"""

		data = {
			"run_spec": {
				"language_id": "python3",
				"sourcecode": "import subprocess, sys\n\n__student_answer__ = \"\"\"#include <stdio.h>\r\n\r\nint sqr(int n) {\r\n    return n * n;\r\n}\r\n\r\n\"\"\"\n\n__student_answer__ += \"\"\"int main(){\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(10));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(5));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(0));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(11));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(1));\n\"\"\"\n__student_answer__ += \"\"\"    return 0; \\n}\"\"\"\nwith open(\"student.c\", \"w\") as stud_ans:\n    print(__student_answer__, file=stud_ans);\n\n\n\nreturn_code = 0\nreturn_code = subprocess.run([\"bash\", \"compile_student.cmd\"], check=True)\n\nif  return_code != 0:\n    subprocess.run([\"bash\", \"execute_student.cmd\"])",
				"sourcefilename": "__tester__.python3",
				"input": "",
				"file_list": [],
				"parameters": {
					"chroot_dir": "test",
					"no_runguard": {
						"language_id": "c",
						"sourcefilename": True
					}
				}
			}
		}

		response = requests.post(URL, json=data)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json(), "runs_post: invalid student_sourcefilename")

	def test_incorrect_no_runguard_use(self):
		"""
		Using no_runguard implies that chroot_dir is specified
		There is parameters['chroot_dir'] is empty
		"""
		data = {
			"run_spec": {
				"language_id": "python3",
				"sourcecode": "import subprocess, sys\n\n__student_answer__ = \"\"\"#include <stdio.h>\r\n\r\nint sqr(int n) {\r\n    return n * n;\r\n}\r\n\r\n\"\"\"\n\n__student_answer__ += \"\"\"int main(){\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(10));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(5));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(0));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(11));\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\"#<ab@17943918#@>#\");\n\"\"\"\n__student_answer__ += \"\"\"\n    printf(\\\"%d\\\\n\\\", sqr(1));\n\"\"\"\n__student_answer__ += \"\"\"    return 0; \\n}\"\"\"\nwith open(\"student.c\", \"w\") as stud_ans:\n    print(__student_answer__, file=stud_ans);\n\n\n\nreturn_code = 0\nreturn_code = subprocess.run([\"bash\", \"compile_student.cmd\"], check=True)\n\nif  return_code != 0:\n    subprocess.run([\"bash\", \"execute_student.cmd\"])",
				"sourcefilename": "__tester__.python3",
				"input": "",
				"file_list": [],
				"parameters": {
					"no_runguard": {
						"language_id": "c",
					}
				}
			}
		}

		response = requests.post(URL, json=data)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json(), "runs_post: runguard was provided, but chroot_dir was not")

	def test_non_existent_chroot(self):
		"""
		сhroot directory must exist on the server
		"""
		data = {
			"run_spec": {
				"language_id": "c",
				"sourcecode": "\n#include <stdio.h>\n\nint main() {\n    printf(\"Hello world!\");{}\n}\n",
				"sourcefilename": "test.c",
				"parameters": {
					"chroot_dir": "fljksafjass",
					"no_runguard": {
						"language_id": "c"
					}
				}
			}
		}

		response = requests.post(URL, json=data)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json(), "runs_post: chroot_dir does not exist")

	def test_incorrect_chroot_dir(self):
		"""
		chroot directory must specified by the string.
		"""
		data = {
			"run_spec": {
				"language_id": "c",
				"sourcecode": "\n#include <stdio.h>\n\nint main() {\n    printf(\"Hello world!\");{}\n}\n",
				"sourcefilename": "test.c",
				"parameters": {
					"chroot_dir": None,
					"no_runguard": {
						"language_id": "c"
					}
				}
			}
		}

		response = requests.post(URL, json=data)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json(), "runs_post: chroot_dir name must be a string")
