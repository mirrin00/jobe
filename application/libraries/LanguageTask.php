<?php defined('BASEPATH') OR exit('No direct script access allowed');

/* ==============================================================
 *
 * This file defines the abstract Task class, a subclass of which
 * must be defined for each implemented language.
 *
 * ==============================================================
 *
 * @copyright  2014 Richard Lobb, University of Canterbury
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

require_once('application/libraries/resultobject.php');

define('ACTIVE_USERS', 1);  // The key for the shared memory active users array
define('MAX_RETRIES', 5);   // Maximum retries (1 secs per retry), waiting for free user account

class OverloadException extends Exception {
}


abstract class Task {

    // Symbolic constants as per ideone API

    const RESULT_COMPILATION_ERROR = 11;
    const RESULT_RUNTIME_ERROR = 12;
    const RESULT_TIME_LIMIT   = 13;
    const RESULT_SUCCESS      = 15;
    const RESULT_MEMORY_LIMIT    = 17;
    const RESULT_ILLEGAL_SYSCALL = 19;
    const RESULT_INTERNAL_ERR = 20;
    const RESULT_SERVER_OVERLOAD = 21;

    const PROJECT_KEY = 'j';  // For ftok function. Irrelevant (?)

    // Global default parameter values. Can be overridden by subclasses,
    // and then further overridden by the individual run requests.
    public $default_params = array(
        'disklimit'     => 20,      // MB (for normal files)
        'streamsize'    => 2,       // MB (for stdout/stderr)
        'cputime'       => 5,       // secs
        'memorylimit'   => 200,     // MB
        'numprocs'      => 20,
        'compileargs'   => array(),
        'linkargs'      => array(),
        'interpreterargs' => array(),
        'runargs'       => array()
    );

    public $id;             // The task id - use the workdir basename
    public $input;          // Stdin for this task
    public $sourceFileName; // The name to give the source file
    public $params;         // Request parameters

    public $userId = null;  // The user id (number counting from 0).
    public $user;           // The corresponding user name (e.g. jobe01).

    public $cmpinfo = '';   // Output from compilation
    public $time = 0;       // Execution time (secs)
    public $memory = 0;     // Memory used (MB)
    public $signal = 0;
    public $stdout = '';    // Output from execution
    public $stderr = '';
    public $result = Task::RESULT_INTERNAL_ERR;  // Should get overwritten
    public $workdir = '';   // The temporary working directory created in constructor

    // ************************************************
    //   MAIN METHODS THAT HANDLE THE FLOW OF ONE JOB
    // ************************************************

    public function __construct($filename, $input, $params) {
        $this->input = $input;
        $this->sourceFileName = $filename;
        $this->params = $params;
        $this->cmpinfo = '';  // Optimism (always look on the bright side of life).
    }


    // Grab any resources that will be needed to run the task. The contract
    // is that if prepare_execution_environment has been called, then
    // the close method will be called before the request using this object
    // is finished.
    //
    // For all languages it is necessary to store the source code in a
    // temporary file. A temporary directory is made to hold the source code.
    //
    // WARNING: the /home/jobe/runs directory (below) is generated by the installer.
    // If you change that directory for some reason, make sure the directory
    // exists, is owned by jobe, with group www-data (or whatever your web
    // server user is) and has access rights of 771. If it's readable by
    // any of the jobe<n> users, running programs will be able
    // to hoover up other students' submissions.
    public function prepare_execution_environment($sourceCode) {
        // Create the temporary directory that will be used.
        $this->workdir = tempnam("/home/jobe/runs", "jobe_");
        if (!unlink($this->workdir) || !mkdir($this->workdir)) {
            log_message('error', 'LanguageTask constructor: error making temp directory');
            throw new Exception("Task: error making temp directory (race error?)");
        }
        chdir($this->workdir);

        $this->id = basename($this->workdir);

        // Save the source there.
        if (empty($this->sourceFileName)) {
            $this->sourceFileName = $this->defaultFileName($sourceCode);
        }
        file_put_contents($this->workdir . '/' . $this->sourceFileName, $sourceCode);

        // Allocate one of the Jobe users.
        $this->userId = $this->getFreeUser();
        $this->user = sprintf("jobe%02d", $this->userId);

        // Give the user RW access.
        exec("setfacl -m u:{$this->user}:rwX {$this->workdir}");
    }


    // Load the specified files into the working directory.
    // The file list is an array of (fileId, filename) pairs.
    // Throws an exception if any are not present.
    public function load_files($fileList, $filecachedir) {
        foreach ($fileList as $file) {
            $fileId = $file[0];
            $filename = $file[1];
            $path = $filecachedir . $fileId;
            $destPath = $this->workdir . '/' . $filename;
            if (!file_exists($path) ||
               ($contents = file_get_contents($path)) === FALSE ||
               (file_put_contents($destPath, $contents)) === FALSE) {
                throw new JobException('One or more of the specified files is missing/unavailable',
                        'file(s) not found', 404);
            }
        }
    }

    // Compile the current source file in the current directory, saving
    // the compiled output in a file $this->executableFileName.
    // Sets $this->cmpinfo accordingly.
    public abstract function compile();


    // Execute this task, which must already have been compiled if necessary
    public function execute() {
        try {
            $cmd = implode(' ', $this->getRunCommand());
            list($this->stdout, $this->stderr) = $this->run_in_sandbox($cmd, $this->input);
            $this->stderr = $this->filteredStderr();
            $this->diagnose_result();  // Analyse output and set result
        }
        catch (OverloadException $e) {
            $this->result = Task::RESULT_SERVER_OVERLOAD;
            $this->stderr = $e->getMessage();
        }
        catch (Exception $e) {
            $this->result = Task::RESULT_INTERNAL_ERR;
            $this->stderr = $e->getMessage();
        }
    }


    // Called to clean up task when done
    public function close($deleteFiles = true) {

        if ($this->userId !== null) {
            exec("sudo /usr/bin/pkill -9 -u {$this->user}"); // Kill any remaining processes
            $this->removeTemporaryFiles($this->user);
            $this->freeUser($this->userId);
            $this->userId = null;
            $this->user = null;
        }

        if ($deleteFiles && $this->workdir) {
            $dir = $this->workdir;
            exec("sudo rm -R $dir");
            $this->workdir = null;
        }
    }

    // ************************************************
    //    METHODS TO ALLOCATE AND FREE ONE JOBE USER
    // ************************************************

    // Find a currently unused jobe user account.
    // Uses a shared memory segment containing one byte (used as a 'busy'
    // boolean) for each of the possible user accounts.
    // If no free accounts exist at present, the function sleeps for a
    // second then retries, up to a maximum of 10 retries.
    // Throws OverloadException if a free user cannot be found, otherwise
    // returns an integer in the range 0 to jobe_max_users - 1 inclusive.
    private function getFreeUser() {
        global $CI;

        $numUsers = $CI->config->item('jobe_max_users');
        $key = ftok(__FILE__,  TASK::PROJECT_KEY);
        $sem = sem_get($key);
        $user = -1;
        $retries = 0;
        while ($user == -1 && $retries < MAX_RETRIES) {
            sem_acquire($sem);
            $shm = shm_attach($key);
            if (!shm_has_var($shm, ACTIVE_USERS)) {
                // First time since boot -- initialise active list
                $active = array();
                for($i = 0; $i < $numUsers; $i++) {
                    $active[$i] = FALSE;
                }
                shm_put_var($shm, ACTIVE_USERS, $active);
            }
            $active = shm_get_var($shm, ACTIVE_USERS);
            for ($user = 0; $user < $numUsers; $user++) {
                if (!$active[$user]) {
                    $active[$user] = TRUE;
                    shm_put_var($shm, ACTIVE_USERS, $active);
                    break;
                }
            }
            shm_detach($shm);
            sem_release($sem);
            if ($user == $numUsers) {
                $user = -1;
                $retries += 1;
                if ($retries < MAX_RETRIES) {
                    sleep(1);
                } else {
                    throw new OverloadException();
                }
            }
        }
        return $user;
    }


    // Mark the given user number (0 to jobe_max_users - 1) as free.
    private function freeUser($userNum) {
        $key = ftok(__FILE__, 'j');
        $sem = sem_get($key);
        sem_acquire($sem);
        $shm = shm_attach($key);
        $active = shm_get_var($shm, ACTIVE_USERS);
        $active[$userNum] = FALSE;
        shm_put_var($shm, ACTIVE_USERS, $active);
        shm_detach($shm);
        sem_release($sem);
    }

    // ************************************************
    //                  HELPER METHODS
    // ************************************************

    /**
     * Run the given shell command in the runguard sandbox, using the given
     * string for stdin (if given).
     * @param string $cmd The shell command to execute
     * @param string $stdin The string to use as standard input. If not given use /dev/null
     * @return array a two element array of the standard output and the standard error
     * from running the given command.
     */
    public function run_in_sandbox($cmd, $stdin=null) {
        $filesize = 1000 * $this->getParam('disklimit'); // MB -> kB
        $streamsize = 1000 * $this->getParam('streamsize'); // MB -> kB
        $memsize = 1000 * $this->getParam('memorylimit');
        $cputime = $this->getParam('cputime');
        $numProcs = $this->getParam('numprocs');
        $commandBits = array(
                "sudo " . dirname(__FILE__)  . "/../../runguard/runguard",
                "--user={$this->user}",
                "--group=jobe",
                "--time=$cputime",         // Seconds of execution time allowed
                "--filesize=$filesize",    // Max file sizes
                "--nproc=$numProcs",       // Max num processes/threads for this *user*
                "--no-core",
                "--streamsize=$streamsize");   // Max stdout/stderr sizes

        if ($memsize != 0) {  // Special case: Matlab won't run with a memsize set. TODO: WHY NOT!
            $commandBits[] = "--memsize=$memsize";
        }
        $commandBits[] = $cmd;
        $cmd = implode(' ', $commandBits) . " >prog.out 2>prog.err";

        // Set up the work directory and run the job
        $workdir = $this->workdir;
        exec("setfacl -m u:{$this->user}:rwX $workdir");  // Give the user RW access
        chdir($workdir);

        if ($stdin) {
            $f = fopen('prog.in', 'w');
            fwrite($f, $stdin);
            fclose($f);
            $cmd .= " <prog.in\n";
        }
        else {
            $cmd .= " </dev/null\n";
        }

        file_put_contents('prog.cmd', $cmd);

        $handle = popen($cmd, 'r');
        $result = fread($handle, MAX_READ);
        pclose($handle);

        $output = file_get_contents("$workdir/prog.out");
        if (file_exists("{$this->workdir}/prog.err")) {
            $stderr = file_get_contents("{$this->workdir}/prog.err");
        } else {
            $stderr = '';
        }
        return array($output, $stderr);
    }


    protected function getParam($key) {
        if (isset($this->params) && array_key_exists($key, $this->params)) {
            return $this->params[$key];
        } else {
            return $this->default_params[$key];
        }
    }


    // Check if PHP exec environment includes a PATH. If not, set up a
    // default, or gcc misbehaves. [Thanks to Binoj D for this bug fix,
    // needed on his CentOS system.]
    protected function setPath() {
        $envVars = array();
        exec('printenv', $envVars);
        $hasPath = FALSE;
        foreach ($envVars as $var) {
            if (strpos($var, 'PATH=') === 0) {
                $hasPath = TRUE;
                break;
            }
        }
        if (!$hasPath) {
            putenv("PATH=/sbin:/bin:/usr/sbin:/usr/bin");
        }
    }


    // Return the Linux command to use to run the current job with the given
    // standard input. It's an array of strings, which when joined with a
    // a space character makes a bash command. The default is to use the
    // name of the executable from getExecutablePath() followed by the strings
    // in the 'interpreterargs' parameter followed by the name of the target file
    // as returned by getTargetFile() followed by the strings in the
    // 'runargs' parameter. For compiled languages, getExecutablePath
    // should generally return the path to the compiled object file and
    // getTargetFile() should return the empty string. The interpreterargs
    // and runargs parameters are then just added (in that order) to the
    // run command. For interpreted languages getExecutablePath should return
    // the path to the interpreter and getTargetFile() should return the
    // name of the file to be interpreted (in the current directory).
    // This design allows for commands like java -Xss256k thing -blah.
    public function getRunCommand() {
        $cmd = array($this->getExecutablePath());
        $cmd = array_merge($cmd, $this->getParam('interpreterargs'));
        if ($this->getTargetFile()) {
            $cmd[] = $this->getTargetFile();
        }
        $cmd = array_merge($cmd, $this->getParam('runargs'));
        return $cmd;
    }


    // Return a suitable default filename for the given sourcecode.
    // Usually of form prog.py, prog.cpp etc but Java is a special case.
    public abstract function defaultFileName($sourcecode);


    // Return the path to the executable that runs this job. For compiled
    // languages this will be the output from the compilation. For interpreted
    // languages it will be the path to the interpreter or JVM etc.
    public abstract function getExecutablePath();


    // Return the name of the so called "target file", which will typically be empty
    // for compiled languages and will be the name of the file to be interpreted
    // (usually just $this->executableFileName) for interpreted languages.
    public abstract function getTargetFile();


    // Override the following function if the output from executing a program
    // in this language needs post-filtering to remove stuff like
    // header output.
    public function filteredStdout() {
        return $this->stdout;
    }


    // Override the following function if the stderr from executing a program
    // in this language needs post-filtering to remove stuff like
    // backspaces and bells.
    public function filteredStderr() {
        return $this->stderr;
    }


    // Called after each run to set the task result value. Default is to
    // set the result to SUCCESS if there's no stderr output or to timelimit
    // exceeded if the appropriate warning message is found in stdout or
    // to runtime error otherwise.
    // Note that Runguard does not identify memorylimit exceeded as a special
    // type of runtime error so that value is not returned by default.

    // Subclasses may wish to add further postprocessing, e.g. for memory
    // limit exceeded if the language identifies this specifically.
    public function diagnose_result() {
        if (strlen($this->filteredStderr())) {
            $this->result = TASK::RESULT_RUNTIME_ERROR;
        } else {
            $this->result = TASK::RESULT_SUCCESS;
        }

        // Refine RuntimeError if possible
        if (strpos($this->stderr, "warning: timelimit exceeded")) {
            $this->result = Task::RESULT_TIME_LIMIT;
            $this->signal = 9;
            $this->stderr = '';
        } else if(strpos($this->stderr, "warning: command terminated with signal 11")) {
            $this->signal = 11;
            $this->stderr = '';
        }
    }


    // Return the JobeAPI result object to describe the state of this task
    public function resultObject() {
        if ($this->cmpinfo) {
            $this->result = Task::RESULT_COMPILATION_ERROR;
        }
        return new ResultObject(
                $this->workdir,
                $this->result,
                $this->cmpinfo,
                $this->filteredStdout(),
                $this->filteredStderr()
        );
    }


    // Remove any temporary files created by the given user on completion
    // of a run
    protected function removeTemporaryFiles($user) {
        global $CI;
        $path = $CI->config->item('clean_up_path');
        $dirs = explode(';', $path);
        foreach($dirs as $dir) {
            exec("sudo /usr/bin/find $dir/ -user $user -delete");
        }
    }

    // ************************************************
    //  METHODS FOR DIAGNOSING THE AVAILABLE LANGUAGES
    // ************************************************

    // Return a two-element array of the shell command to be run to obtain
    // a version number and the RE pattern with which to extract the version
    // string from the output. This should have a capturing parenthesised
    // group so that $matches[1] is the required string after a call to
    // preg_match. See getVersion below for details.
    // Should be implemented by all subclasses. [Older versions of PHP
    // don't allow me to declare this abstract. But it is!!]
    public static function getVersionCommand() {}


    // Return a string giving the version of language supported by this
    // particular Language/Task.
    // Return NULL if the version command (supplied by the subclass's
    // getVersionCommand) fails or produces no output. This can be interpreted
    // as a non-existent language that should be removed from the list of
    // languages handled by this Jobe server.
    // If the version command runs but yields a result in
    // an unexpected format, returns the string "Unknown".
    public static function getVersion() {
        list($command, $pattern) = static::getVersionCommand();
        $output = array();
        $retvalue = null;
        exec($command . ' 2>&1', $output, $retvalue);
        if ($retvalue != 0 || count($output) == 0) {
            return NULL;
        } else {
            $matches = array();
            $allOutput = implode("\n", $output);
            $isMatch = preg_match($pattern, $allOutput, $matches);
            return $isMatch ? $matches[1] : "Unknown";
        }
    }
}
