# -*- coding: utf-8 -*-

import stat
import paramiko
import yaml
import argparse
import subprocess
import os
import re

def extrace_file_name(path):
    """
    处理输入的路径，提取最后的文件夹名或是文件名
    """
    result = re.findall(r'[^\\/:*?"<>|\r\n]+$',path)
    result1 = result[0]
    return result1

def err_info(args):
    pass

def get_all_files_in_local_dir(local_dir):
    """
    递归获取本地当前目录下所有文件目录
    """
    all_files = []
    # 获取当前指定目录下的所有目录及文件，包含属性值
    files = os.listdir(local_dir)
    if not files:
        all_files.append(local_dir)
    else:
        for x in files:
            # local_dir目录中每一个文件或目录的完整路径
            filename = os.path.join(local_dir, x)
            # 如果是目录，则递归处理该目录
            if os.path.isdir(filename):
                all_files.extend(get_all_files_in_local_dir(filename))
            else:
                all_files.append(filename)
    return all_files

def get_all_files_in_remote_dir(sftp,remote_dir):
    """
    递归获取远程当前目录下所有文件目录
    """
    all_files = []
    if remote_dir[-1] == '/':   #排除/root/test/的情况，修正为/root/test
        remote_dir = remote_dir[0:-1]

    files = sftp.listdir_attr(remote_dir)   #列出指定目录下的所有文件和目录以及属性
    if not files:
        all_files.append(remote_dir)
    else:
        for file in files:
            filename = remote_dir + '/' + file.filename

            if stat.S_ISDIR(file.st_mode):  #通过stat模块来实现检查类型
                all_files.extend(get_all_files_in_remote_dir(sftp,filename))
            else:
                all_files.append(filename)

    return all_files

def arg():
    parser = argparse.ArgumentParser(description='collect debug message')
    sub_parser = parser.add_subparsers()
    parser_upload = sub_parser.add_parser("upload", aliases=["u"])
    parser_download = sub_parser.add_parser("download", aliases=["d"])

    parser_upload.add_argument('--source', '-s',required=True)
    parser_upload.add_argument('--target', '-t',required=True)
    parser_download.add_argument('--source', '-s',required=True)
    parser_download.add_argument('--target', '-t',required=True)

    parser_upload.set_defaults(func=upload)
    parser_download.set_defaults(func=download)
    parser.set_defaults(func=err_info)

    args = parser.parse_args()

    try:
        if args.source is not None and args.target is not None:
            pass
        else:
            pass
    except:
        parser.print_help()

    args.func(args)

    return args


class ReadConfig():
    """
    读取配置文件,get_list方法把ip和password以列表的形式输出,便于后续操作
    """

    def __init__(self):
        self.yaml_name = "./config.yaml"
        self.yaml_info = self.read_yaml()
        self.config_list = self.get_list()

    def read_yaml(self):
        try:
            with open(self.yaml_name, encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            print(f"Please check the file name: {self.yaml_name}")
        except TypeError:
            print("Error in the type of file name.")

    def get_list(self):
        list = []
        for node in self.yaml_info["node"]:
            list.append([node['ip'], node['password']])
        return list


class Ssh():
    def __init__(self, ip, password):
        self.ip = ip
        self.port = 22
        self.username = 'root'
        self.password = password
        self.obj_SSHClient = paramiko.SSHClient()
        self.transport = paramiko.Transport((self.ip, self.port))
        self.connect()
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def connect(self):
        try:
            self.obj_SSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.obj_SSHClient.connect(hostname=self.ip,
                                       port=self.port,
                                       username=self.username,
                                       password=self.password, )
            self.transport.connect(username=self.username, password=self.password)
        except:
            print("SSH connection failed,please check the hostname or password")

    def close(self):
        self.sftp.close()
        self.obj_SSHClient.close()

    def sftp_get(self, remotefile, localfile):
        try:
            self.sftp.get(remotefile, localfile)
        except:
            print("SFTP connection failed")

    def sftp_put(self, localfile, remotefile):
        try:
            self.sftp.put(localfile, remotefile)
        except:
            print("SFTP put failed")


def download(args):
    test1 = os.path.split(args.target)[1]

    if test1 == '':
        pass
    else:
        args.target = args.target + '/'

    file_name = extrace_file_name(args.source)
    for node in config_list:
        print(f"Start downloading: {args.source}")
        path = f'{args.target}{node[0]}/'  # Windows用"\"即在此用"\\"，linux用"/,此处为已经加上了自建文件的路径"

        if not os.path.isdir(path): #如果对应node的文件夹不存在则创建
            mkdir_file = f"mkdir {path}"
            subprocess.run(mkdir_file, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8',
                           timeout=100)
            print(f"Node folder has been created: {path}")

        one_test = Ssh(node[0], node[1])
        one_test_sftp = one_test.sftp
        try:
            teststr = one_test_sftp.stat(args.source)
            print("The file/folder is detected and can be downloaded")
            try:
                testfile2 = one_test_sftp.listdir_attr(args.source)
                if testfile2 is not None:
                    one_test.close()
                    source = args.source
                    target = args.target  # 测试，正式加入时改回linux方法 C:\\EFI\\

                    obj_ssh = Ssh(node[0], node[1])
                    test_sftp = obj_ssh.sftp
                    all_files = get_all_files_in_remote_dir(test_sftp, source)

                    local_pathname = os.path.split(source)[-1]  # 远程下载的文件名 test
                    real_local_Path = path + local_pathname  # 远程下载后保存的路径，包括目录名 C:/EFI/test

                    if not target[-1] == '/':  # 排除/root/test/的情况，修正为/root/test
                        target = target + '/'
                        print(f"Download path error，change to {target}")
                    else:
                        print("Download path is correct")

                    if not os.path.isdir(target):
                        print("Download path entered does not exist, please re output")
                    else:
                        print("Download path is correct, and the download will begin soon")

                    if not os.path.isdir(real_local_Path):  # 如果下载的根文件不存在，则创建，创建test
                        mkdir_file2 = f'mkdir {real_local_Path}'
                        subprocess.run(mkdir_file2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       encoding='UTF-8',
                                       timeout=100)

                    for filepath in all_files:
                        # filepath = filepath.replace("/", "\\")  #测试，正式加入时删除
                        off_path_name = filepath.split(local_pathname)[-1]  # 用本地根文件夹名分隔本地文件路径，取得相对于下载的根文件的文件路径

                        try:
                            testfiles = test_sftp.listdir_attr(filepath)
                            if testfiles == [] and os.path.split(off_path_name)[0] == '/':
                                abs_path = off_path_name
                        except:
                            abs_path = os.path.split(off_path_name)[0]

                        reward_local_path = real_local_Path + abs_path
                        if not reward_local_path == '/':
                            subprocess.run(f'mkdir {reward_local_path}', shell=True, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, encoding='UTF-8',
                                           timeout=100)

                        try:
                            testfile2 = test_sftp.listdir_attr(filepath)
                            if testfile2 == [] and os.path.split(off_path_name)[0] == '/':
                                pass
                        except:
                            abs_file = os.path.split(filepath)[1]  # 期望下载的文件名
                            to_local = reward_local_path + '/' + abs_file  # 下载文件到远端的路径，\\删除
                            obj_ssh.sftp_get(filepath, to_local)

            except:
                one_target = f'{path}{file_name}'
                try:
                    one_obj_ssh = Ssh(node[0], node[1])
                    one_obj_ssh.sftp_get(args.source, one_target)
                    one_obj_ssh.close()
                    print("File download successful")
                except:
                    print("File download failed")
        except:
            print("The file/folder does not exist, please check the path")

        print(f"Download complete: {args.source}")


def upload(args):
    test1 = os.path.split(args.target)[1]
    if test1 == '':
        pass
    else:
        args.target = args.target + '/'

    if os.path.isfile(args.source):
        file_name = extrace_file_name(args.source)
        target = f'{args.target}{file_name}'
        try:
            for node in config_list:
                print(f'Start uploading: {args.target}')
                obj_ssh = Ssh(node[0], node[1])
                obj_sftp = obj_ssh.sftp
                try:
                    teststr = obj_sftp.stat(args.target)
                except:
                    print("Upload path does not exist, it is created automatically")
                    try:
                        obj_ssh.obj_SSHClient.exec_command(f"mkdir -p {args.target}")
                        teststr0 = obj_sftp.stat(args.target)
                    except:
                        print("Path creation failed")
                obj_ssh.sftp_put(args.source, target)
                obj_ssh.close()
            print("file upload successful")
        except:
            print("file upload failed")

    else:
        """
        source:C:\\EFI\\test target:/root/test
        local_path = args.source
        remote_paht = args.target
        """
        for node in config_list:
            """
            node[0]:ip
            node[1]:password
            """
            print(f'Start uploading: {args.target}')
            obj_ssh = Ssh(node[0], node[1])

            local_pathname = os.path.split(args.source)[-1]  #本地上传的文件名 test
            real_remote_Path = args.target + '/' + local_pathname   #远程上传后的路径，包括目录名 /root/test/test
            try:
                obj_ssh.sftp.stat(args.target)
            except Exception as e :
                print(f"Upload path does not exist, it is created automatically: {args.target}")
                obj_ssh.obj_SSHClient.exec_command(f'mkdir -p {args.target}')
            obj_ssh.obj_SSHClient.exec_command(f"mkdir -p {real_remote_Path}")

            all_file = get_all_files_in_local_dir(args.source) # 获取本地文件夹下所有的文件路径 ['C:\\EFI\\test\\123', 'C:\\EFI\\test\\456.txt', 'C:\\EFI\\test\\file\\456.txt', 'C:\\EFI\\test\\file2']

            for file_path in all_file:
                file_path = file_path.replace("\\", "/")
                off_path_name = file_path.split(local_pathname)[-1] #用本地根文件夹名分隔本地文件路径，取得相对的文件路径
                if os.path.isdir(file_path) is True and os.path.split(off_path_name)[0] == '/':
                    abs_path = off_path_name    #取得本地存在的嵌套文件夹层级
                else:
                    abs_path = os.path.split(off_path_name)[0]
                reward_remote_path = real_remote_Path + abs_path
                try:
                    obj_ssh.sftp.stat(reward_remote_path)
                except Exception as e:
                    obj_ssh.obj_SSHClient.exec_command("mkdir -p %s" % reward_remote_path)

                if os.path.isfile(file_path) :  #此处判断,如果是文件则进行上传,如果是空文件夹则不做处理,因为在上述步骤已经完成了文件夹的创建
                    abs_file = os.path.split(file_path)[1]  #期望上传的文件名
                    to_remote = reward_remote_path + '/' + abs_file #上传文件到远端的路径
                    obj_ssh.sftp_put(file_path,to_remote)

            print("Upload successful")

            obj_ssh.close()

if __name__ == '__main__':

    obj_readconfig = ReadConfig()
    config_list = obj_readconfig.config_list
    args = arg()
