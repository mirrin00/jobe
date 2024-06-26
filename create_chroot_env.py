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
chroot_dependencies = ['/bin', '/lib', '/lib64', '/usr', '/etc']


def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f'Error executing command \'{command}\': {e}')


def make_chroot_dir(dir_name):
    chroot_dir_path = os.path.join(JOBE_HOME_DIR, dir_name)
    if os.path.exists(chroot_dir_path):
        print(f'Directory \'{chroot_dir_path}\' already exists. Cannot create.')
    else:
        try:
            run_command(f'mkdir "{chroot_dir_path}" && '
                        f'chown {JOBE_USER}:{JOBE_GROUP} "{chroot_dir_path}" && '
                        f'chmod 751 "{chroot_dir_path}"')
            run_command(f'mkdir "{chroot_dir_path}/runs" && '
                        f'chown {JOBE_USER}:{WWW_GROUP} "{chroot_dir_path}/runs" && '
                        f'chmod 771 "{chroot_dir_path}/runs"')
            run_command(f'mkdir "{chroot_dir_path}/files" && '
                        f'chown {JOBE_USER}:{WWW_GROUP} "{chroot_dir_path}/files" && '
                        f'chmod 771 "{chroot_dir_path}/files"')

            for directory in chroot_dependencies:
                target_dir = os.path.join(chroot_dir_path, directory.lstrip('/'))
                if os.path.exists(directory):
                    run_command(f'mkdir -p "{target_dir}"')
                    run_command(f'mount --bind -r "{directory}" "{target_dir}"')
                else:
                    print(f'Cannot mount to \'{target_dir}\'. Directory \'{directory}\' does not exist. There may be an error')

        except RuntimeError:
            print(f'An error occurred while making chroot directory. Removing \'{chroot_dir_path}\'')
            remove_chroot_dir(dir_name)
            raise


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

            run_command(f'rm -rf "{chroot_dir_path}"')
        except RuntimeError:
            raise


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
