import yaml
import argparse
import subprocess
import os


def scp_file(file_source, file_target):
    """
    构建scp命令，无论是upload还是download都适用
    """
    cmd = f"scp {file_source} {file_target}" #scp传输格式：scp [可选参数] file_source file_target
    return cmd

def arg():
    parser = argparse.ArgumentParser(description='collect debug message')
    sub_parser = parser.add_subparsers()
    parser_upload = sub_parser.add_parser("upload", aliases=["s"])
    parser_download = sub_parser.add_parser("download", aliases=["c"])

    parser_upload .add_argument('--source', '-s')
    parser_upload .add_argument('--target', '-t')
    parser_download.add_argument('--source', '-s')
    parser_download.add_argument('--target', '-t')

    parser_upload.set_defaults(func=upload)
    parser_download.set_defaults(func=download)
    # parser.set_defaults(func=err_info())

    args = parser.parse_args()
    args.func(args)

    return args

def upload(args):
    """
    实现upload操作的函数
    """
    for node in config_list :
        target = f"root@{node[0]}:{args.target}"
        cmd = scp_file(args.source,target)
        ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', timeout=100)
        if ret.returncode == 0:
            print("success:",ret)
        else:
            print("error:",ret)

def download(args):
    """
    实现download操作的函数
    """
    for node in config_list :
        path = f'{args.target}/{node[0]}/' #Windows用"\"即在此用"\\"，linux用"/"
        source = f'root@{node[0]}:{args.source}'
        cmd = scp_file(source, path)
        if not os.path.isdir(path):
            mkdir_file = f"mkdir {path}"
            subprocess.run(mkdir_file, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8',timeout=100)
            ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8',timeout=100)
            if ret.returncode == 0:
                print("success:", ret)
            else:
                print("error:", ret)
        else:
            rett = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8',timeout=100)
            if rett.returncode == 0:
                print("success:", rett)
            else:
                print("error:", rett)

class ReadConfig() :
    """
    读取配置文件,get_list方法把ip和password以列表的形式输出,便于后续操作
    """
    def __init__(self):
        self.yaml_name = "./config.yaml"
        self.yaml_info = self.read_yaml()
        self.yaml_list = self.get_list()

    def read_yaml(self):
        try:
            with open(self.yaml_name,encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            print(f"Please check the file name: {self.yaml_name}")
        except TypeError:
            print("Error in the type of file name.")

    def get_list(self):
        list = []
        for node in self.yaml_info["node"]:
            list.append([node['ip'],node['password']])
        return list


# class Ssh() :   #暂时用不上此类，所有操作都是在本地进行
#     def __init__(self,ip,password,port=22,):
#         self.ip = ip
#         self.username = 'root'
#         self.password = password
#         self.port = port
#         self.SSHConnection = None
#         self.connect()
#
#     def connect(self):
#             objSSHClient = paramiko.SSHClient()
#             objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#             objSSHClient.connect(hostname=self.ip,
#                                  port=self.port,
#                                  username=self.username,
#                                  password=self.password,)
#             self.SSHConnection = objSSHClient
#
#     def exec_command(self,command):
#         if self.SSHConnection:
#             stdin, stdout, stderr = self.SSHConnection.exec_command(command)
#             data = stdout.read()
#             data = data.decode('utf-8')
#             return data



if __name__ == '__main__' :
    config_list = ReadConfig().get_list()
    args = arg()
    # print(args)





