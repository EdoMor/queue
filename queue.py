import paramiko
import os
import errno
import warnings
import click

if os.path.isfile('settings'):
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings'), 'r') as fo:
        settings = fo.read()
        SSH_USERNAME, SSH_PASSWORD, SSH_ADDRESS, SSH_PORT = settings.split('\n')
else:
    raise RuntimeError('please run queue --setup')

SSH_PORT = int(SSH_PORT)
dest = '/home/user/Desktop/projects/'
locpath = r'C:\Users\User\PycharmProjects\queue client\payload'


class FileExistsWarning(FutureWarning):
    pass


class MySFTPClient(paramiko.SFTPClient):
    def put_dir(self, source, target, override=False):
        ''' Uploads the contents of the source directory to the target path. The
            target directory needs to exists. All subdirectories in source are
            created under target.
        '''
        self.mkdir(target, ignore_existing=True)
        transfered_files = []
        for item in os.listdir(source):
            if not self.exists_remote(
                    target + str(item)) or override:  # DOTO: force os.path.join work like in linux # 1
                self.put(os.path.join(source, item), target + str(item))  # 1
                transfered_files.append(item)
            else:
                warnings.warn(
                    'file ' + str(item) + ' already exsists on host mashine. change file name or enable override',
                    RuntimeWarning)
        return transfered_files

    def mkdir(self, path, mode=511, ignore_existing=False):
        ''' Augments mkdir by adding an option to not fail if the folder exists  '''
        try:
            super(MySFTPClient, self).mkdir(path, mode)
        except IOError:
            if ignore_existing:
                pass
            else:
                raise

    def exists_remote(self, path):
        try:
            self.stat(path)
        except IOError as e:
            if e.errno == errno.ENOENT:
                return False
            raise
        else:
            return True

@click.group()
def cli():
    '''queue projects to run with server'''
    pass

@cli.command()
@click.argument('locpath', metavar='<path>')
@click.option('--override','-o', is_flag=True, help='override files on server False by default')
def transport(locpath,override=False):
    '''sends project folder from client to server'''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    conn = ssh.connect(SSH_ADDRESS, username=SSH_USERNAME, password=SSH_PASSWORD)

    transport = paramiko.Transport((SSH_ADDRESS, SSH_PORT))
    transport.connect(username=SSH_USERNAME, password=SSH_PASSWORD)

    sftp = MySFTPClient.from_transport(transport)
    print(sftp.put_dir(locpath, dest, override))

@cli.command()
def setup():
    input('username: ')
    input('password: ')
    input('ip: ')
    input('port: ')

if __name__ == '__main__':
    cli()

# ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('ls')
# print(ssh_stdout.read().decode('utf-8'))
