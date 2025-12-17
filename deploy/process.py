# This Python file uses the following encoding: utf-8
# copy from alas https://github.com/LmeSzinc/AzurLaneAutoScript
import subprocess
from deploy.config import DeployConfig
from deploy.logger import logger
from deploy.utils import *
from module.server.setting import State


class ProcessManager(DeployConfig):
    @cached_property
    def process_folder(self):
        return [
            self.filepath("PythonExecutable"),
            self.root_filepath
        ]

    @cached_property
    def self_pid(self):
        return os.getpid()

    def iter_process_by_name(self, name):
        """
        Args:
            name (str): process name, such as 'alas.exe'

        Yields:
            str, str, str: executable_path, process_name, process_id
        """
        try:
            from win32com.client import GetObject
        except ModuleNotFoundError:
            logger.info('pywin32 not installed, skip')
            return False

        try:
            wmi = GetObject('winmgmts:')
            processes = wmi.InstancesOf('Win32_Process')
            for p in processes:
                executable_path = p.Properties_["ExecutablePath"].Value
                process_name = p.Properties_("Name").Value
                process_id = p.Properties_["ProcessID"].Value

                if executable_path is not None and process_name == name and process_id != self.self_pid:
                    executable_path = executable_path.replace(r'\\', '/').replace('\\', '/')
                    for folder in self.process_folder:
                        if folder in executable_path:
                            yield executable_path, process_name, process_id
        except Exception as e:
            # Possible exception
            # pywintypes.com_error: (-2147217392, 'OLE error 0x80041010', None, None)
            logger.info(str(e))
            return False

    def kill_oas_server(self, server_name):
        """
        更精确地杀死OAS服务器进程，避免影响其他Python程序
        """
        # 杀死所有运行server.py的Python进程
        killed_pids = []

        for name in ['python.exe', 'pythonw.exe']:
            for row in self.iter_process_by_name(name):
                # 检查命令行参数是否包含server.py
                try:
                    executable_path, process_name, process_id = row
                    # 获取进程的命令行参数
                    from win32com.client import GetObject
                    wmi = GetObject('winmgmts:')
                    processes = wmi.ExecQuery(f'Select * from Win32_Process where ProcessId = {process_id}')
                    for p in processes:
                        cmdline = p.CommandLine
                        if cmdline and server_name in cmdline.lower() and process_id not in killed_pids:
                            logger.info(f'Killing OAS server tree: {cmdline}')
                            # 杀死指定PID的进程树（包括子进程）
                            self._kill_process_tree(process_id)
                            killed_pids.append(process_id)
                except Exception as e:
                    logger.info(f'Error checking process : {e}')

    def kill_by_port(self, port):
        """
        结束占用指定端口的进程
        Args:
            port (int): 要结束的端口号
        """
        try:
            # 使用 subprocess 直接执行 netstat 命令
            result = subprocess.run(
                f'netstat -aon | findstr :{port}',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout.strip()

            # 检查返回值是否为空
            if not result or 'LISTENING' not in result.upper():
                logger.info(f'No process found listening on port {port}')
                return

            # 解析每一行
            lines = result.splitlines()
            for line in lines:
                parts = line.split()
                if len(parts) < 5:  # 确保分割后至少有 5 列
                    logger.warning(f'Invalid line format: {line}')
                    continue

                # 提取协议、本地地址、状态、远程地址和 PID
                local_address = parts[1]
                state = parts[3].upper()  # 转为大写
                process_id = parts[-1].strip()

                # 检查是否为监听状态且端口匹配
                if state == 'LISTENING' and f':{port}' in local_address:
                    if process_id.isdigit():
                        logger.info(f'Found process with PID {process_id} listening on port {port}')
                        # 杀死指定PID的进程树（包括子进程）
                        self._kill_process_tree(int(process_id))
                    else:
                        logger.warning(f'Invalid PID found: {process_id}')
        except Exception as e:
            logger.error(f'Error killing process on port {port}: {e}')

    def kill_by_name(self, name):
        """
        Args:
            name (str): Process name
        """
        logger.hr(f'Kill {name}', 1)
        for row in self.iter_process_by_name(name):
            logger.info(' '.join(map(str, row)))
            self.execute(f'taskkill /f /pid {row[2]}', allow_failure=True, output=False)

    def _kill_process_tree(self, pid):
        """
        杀死指定PID的进程树（包括子进程）
        Args:
            pid (int): 要结束的进程ID
        """
        logger.info(f'Killing process tree with PID {pid}')
        kill_result = self.execute(f'taskkill /PID {pid} /F /T', allow_failure=True, output=False)
        if kill_result:
            logger.info(f'Successfully killed process tree with PID {pid}')
        else:
            logger.warning(f'Failed to kill process tree with PID {pid}')

    def stop_process_tree_by_port(self, port=None):
        """
        通过端口停止主进程及其所有子进程
        """
        import psutil
        import signal

        # 查找占用指定端口的主进程
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in proc.net_connections():
                    if conn.laddr.port == port:
                        # 先停止所有子进程
                        children = proc.children(recursive=True)
                        for child in children:
                            try:
                                child.send_signal(signal.SIGTERM)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue

                        # 再停止主进程
                        proc.send_signal(signal.SIGTERM)
                        logger.info(f"[ProcessManager] Stopped process tree on port {port} (PID: {proc.pid})")
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        logger.info(f"[ProcessManager] No process found running on port {port}")
        return False

    def process_kill_by_serverName(self, server_name=None):
        if not server_name:
            server_name = 'server.py'
        logger.hr(f'Kill  OAS  Server', 0)
        self.kill_oas_server(server_name)

    def process_kill_by_port(self, port=None):
        if not port:
            port = int(State.deploy_config.WebuiPort) or 22270
        logger.hr(f'Kill  Port  {port}', 0)
        self.kill_by_port(port)

    def process_stop_by_port(self, port=None):
        if not port:
            port = int(State.deploy_config.WebuiPort) or 22270
        logger.hr(f'Stop  Port  {port}', 0)
        self.stop_process_tree_by_port(port)

    def process_kill(self):
        # self.process_kill_by_port()
        # self.process_kill_by_serverName()
        # self.kill_by_name("pythonw.exe")
        self.process_stop_by_port()


if __name__ == '__main__':
    pass
    # ProcessManager().kill_by_name('pythonw')
    # ProcessManager().process_kill_by_serverName()
    # ProcessManager().process_kill_by_port()
    ProcessManager().process_stop_by_port()
