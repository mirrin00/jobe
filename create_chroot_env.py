import os
import pwd
import subprocess
import argparse
import sys
import shlex

JOBE_HOME_DIR = '/home/jobe'
JOBE_USER = 'jobe'
JOBE_GROUP = 'jobe'
WWW_GROUP = 'www-data'
list_ignore = ['files', 'runs']

# directories for mount
chroot_mount_dependencies = ['/bin', '/lib', '/usr/lib', '/usr/lib64', '/usr/bin', '/usr/include', '/usr/share', '/usr/local', '/lib64', '/etc/alternatives', '/etc/python3', '/etc/java-11-openjdk', '/etc/php']

# files for copy
chroot_files_dependencies = ['/etc/octaverc', '/etc/pylintrc', '/etc/fpc.cfg', '/etc/fpc-3.2.2.cfg']

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f'Error executing command \'{command}\': {e}')


def add_fstab_entry(source, target, fstype, options='defaults'):
    entry = f'{source} {target} {fstype} {options} 0 0\n'
    try:
        with open('/etc/fstab', 'a') as fstab:
            fstab.write(entry)
    except FileNotFoundError:
        print("/etc/fstab file not found")
        raise
    except Exception as e:
        print(f"Failed to add fstab entry: {e}")
        raise

def remove_fstab_entry(target):
    try:
        with open('/etc/fstab', 'r') as fstab:
            lines = fstab.readlines()
        with open('/etc/fstab', 'w') as fstab:
            for line in lines:
                if f" {target} " not in line:
                    fstab.write(line)
    except FileNotFoundError:
        print("/etc/fstab file not found")
        raise
    except Exception as e:
        print(f"Failed to remove fstab entry: {e}")
        raise


def make_chroot_dir(dir_name):
    chroot_dir_path = os.path.join(JOBE_HOME_DIR, dir_name)
    if os.path.exists(chroot_dir_path):
        print(f'Directory \'{chroot_dir_path}\' already exists. Cannot create.')
    else:
        try:
            # Only for java
            run_command(f"ln -sf /usr/lib/jvm/java-11-openjdk-amd64/lib/jli/libjli.so /usr/lib/x86_64-linux-gnu/libjli.so")

            run_command(f'mkdir "{chroot_dir_path}" && '
                        f'chown {JOBE_USER}:{JOBE_GROUP} "{chroot_dir_path}" && '
                        f'chmod 751 "{chroot_dir_path}"')
            run_command(f'mkdir "{chroot_dir_path}/runs" && '
                        f'chown {JOBE_USER}:{WWW_GROUP} "{chroot_dir_path}/runs" && '
                        f'chmod 771 "{chroot_dir_path}/runs"')
            run_command(f'mkdir "{chroot_dir_path}/files" && '
                        f'chown {JOBE_USER}:{WWW_GROUP} "{chroot_dir_path}/files" && '
                        f'chmod 771 "{chroot_dir_path}/files"')
            """
            run_command(f'mkdir "{chroot_dir_path}/proc" && '
                        f'mount -t proc /proc "{chroot_dir_path}/proc"')
            add_fstab_entry('proc', f'{chroot_dir_path}/proc', 'proc')

            run_command(f'mkdir "{chroot_dir_path}/dev" && '
                        f'mount -t devtmpfs /dev "{chroot_dir_path}/dev"')
            add_fstab_entry('devtmpfs', f'{chroot_dir_path}/dev', 'devtmpfs')
            
            run_command(f'mkdir "{chroot_dir_path}/sys" && '
                        f'mount -t sysfs /sys "{chroot_dir_path}/sys"')
            add_fstab_entry('sysfs', f'{chroot_dir_path}/sys', 'sysfs')
            """

            run_command(f'mkdir -p "{chroot_dir_path}/dev" && mknod -m 666 "{chroot_dir_path}/dev/null" c 1 3')

            for file in chroot_files_dependencies:
                target_file = os.path.join(chroot_dir_path, file.lstrip('/'))
                if os.path.exists(file):
                    run_command(f'mkdir -p "{os.path.dirname(target_file)}" && cp {file} {target_file}')
                else:
                    print(f'Cannot copy \'{target_file}\'. Directory \'{directory}\' does not exist. There may be an error')

            for directory in chroot_mount_dependencies:
                target_dir = os.path.join(chroot_dir_path, directory.lstrip('/'))
                if os.path.exists(directory):
                    run_command(f'mkdir -p "{target_dir}"')
                    run_command(f'mount --bind "{directory}" "{target_dir}"')
                    add_fstab_entry(directory, target_dir, 'none', 'bind,ro')
                else:
                    print(f'Cannot mount to \'{target_dir}\'. Directory \'{directory}\' does not exist. There may be an error')

        except (RuntimeError, FileNotFoundError, Exception) as e:
            print(f'An error occurred while making chroot directory. Removing \'{chroot_dir_path}\'')
            remove_chroot_dir(dir_name)
            raise e


def remove_chroot_dir(dir_name):
    chroot_dir_path = os.path.join(JOBE_HOME_DIR, dir_name)
    if not os.path.exists(chroot_dir_path):
        print(f'Nothing to remove. Directory \'{chroot_dir_path}\' does not exist.')
    else:
        try:
            mount_paths = subprocess.check_output(f'mount | grep "{chroot_dir_path}" | '
                                                  f'awk -F \' on | type\' \'{{print $2}}\'',
                                                  shell=True, text=True).strip().splitlines()

            for mount_path in mount_paths:
                run_command(f'umount "{mount_path}"')
                remove_fstab_entry(mount_path)

            run_command(f'rm -rf "{chroot_dir_path}"')
        except (RuntimeError, FileNotFoundError, Exception) as e:
            raise e


def list_chroot_directories():
    try:
        jobe_user_uid = pwd.getpwnam(JOBE_USER).pw_uid
        files = os.listdir(JOBE_HOME_DIR)
        chroot_directories = [os.path.join(JOBE_HOME_DIR, shlex.quote(name)) for name in files
                              if os.path.isdir(os.path.join(JOBE_HOME_DIR, name))
                              and name not in list_ignore
                              and os.stat(os.path.join(JOBE_HOME_DIR, name)).st_uid == jobe_user_uid]

        if chroot_directories:
            print(f'Chroot directories:')
            directories_str = ' '.join(chroot_directories)
            run_command(f'ls -dl {directories_str}')
        else:
            print(f'No chroot directories found in \'{JOBE_HOME_DIR}\'')
    except Exception as e:
        print(f'An error occurred while listing chroot directories: {e}')


def parse_arguments():
    parser = argparse.ArgumentParser(description='A script to make/remove chroot directories')
    parser.add_argument('-mk', '--make', metavar='DIR_NAME', action='store', type=str,
                        help='Make a chroot directory with the given DIR_NAME')
    parser.add_argument('-rm', '--remove', metavar='DIR_NAME', action='store', type=str,
                        help='Delete a chroot directory with the given DIR_NAME')
    parser.add_argument('-ls', '--list', action='store_const', const=True, default=False,
                        help='List existing chroot directories')
    args = parser.parse_args(sys.argv[1:])

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return args


def main():
    if subprocess.check_output('whoami', shell=True) != b'root\n':
        print("This script must be run by root")
        sys.exit(1)

    args = parse_arguments()

    try:
        if args.make is not None:
            make_chroot_dir(args.make)
        if args.remove is not None:
            remove_chroot_dir(args.remove)
        if args.list:
            list_chroot_directories()
    except RuntimeError as e:
        print(e)


main()
