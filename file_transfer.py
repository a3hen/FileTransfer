import paramiko
import yaml
import argparse
import subprocess
import os
import re

def extrace_file_name(path):
    result = re.findall(r'[^\\/:*?"<>|\r\n]+$',path)
    result1 = result[0]
    return result1

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
    # parser.set_defaults(func=err_info())

    args = parser.parse_args()
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
    def __init__(self, ip, password, timeout=30):
        self.ip = ip
        self.port = 22
        self.username = 'root'
        self.password = password
        self.timeout = timeout
        self.obj_SSHClient = paramiko.SSHClient()
        self.transport = paramiko.Transport(sock=(self.ip, self.port))

    def connect(self):
        try:
            self.obj_SSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.obj_SSHClient.connect(hostname=self.ip,
                                       port=self.port,
                                       username=self.username,
                                       password=self.password, )
            self.transport.connect(username=self.username, password=self.password)
        except:
            print("ssh password  connect failed")

    def close(self):
        self.transport.close()
        self.obj_SSHClient.close()

    def sftp_get(self, remotefile, localfile):
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.get(remotefile, localfile)

    def sftp_put(self, localfile, remotefile):
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.put(localfile, remotefile)


def download(args):
    file_name = extrace_file_name(args.source)
    try:
        for node in config_list:
            path = f'{args.target}{node[0]}/'  # Windows用"\"即在此用"\\"，linux用"/,此处为已经加上了自建文件的路径"
            target = f'{path}{file_name}'
            if not os.path.isdir(path):
                mkdir_file = f"mkdir {path}"
                subprocess.run(mkdir_file, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8',
                               timeout=100)
            obj_ssh = Ssh(node[0], node[1])
            obj_ssh.connect()
            obj_ssh.sftp_get(args.source, target)
            obj_ssh.close()
        print("download successful")
    except:
        print("download failed")


def upload(args):
    file_name = extrace_file_name(args.source)
    target = f'{args.target}{file_name}'
    try:
        for node in config_list:
            obj_ssh = Ssh(node[0], node[1])
            obj_ssh.connect()
            obj_ssh.sftp_put(args.source, target)
            obj_ssh.close()
        print("upload successful")
    except:
        print("upload failed")


if __name__ == '__main__':
    """
    使用格式：
        例：把本地目录/test/下的123.txt文件上传，上传到的目录为/tset/下
        上传：python3 new_file_transter.py upload -s /test/123.txt -t /tset/
        例：
        下载：python3 new_file_transter.py download -s /tset/123.txt -t /test/
    """
    obj_readconfig = ReadConfig()
    config_list = obj_readconfig.config_list
    args = arg()