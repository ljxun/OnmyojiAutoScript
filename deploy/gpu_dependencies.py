# This Python file uses the following encoding: utf-8
"""
GPU Dependencies Manager
Handles installation of GPU/CPU specific dependencies based on UseGpu configuration
"""

import sys

import subprocess
from deploy.logger import logger


class GPUDependencyManager:
    """Manages GPU/CPU specific dependencies installation"""

    def __init__(self, pip_cmd, arg_str=""):
        self.pip_cmd = pip_cmd
        self.arg_str = arg_str

    def check_cuda_available(self):
        """Check if CUDA is available on the system"""
        try:
            # 首先尝试通过onnxruntime检查CUDA
            import onnxruntime
            providers = onnxruntime.get_available_providers()
            return 'CUDAExecutionProvider' in providers
        except ImportError:
            pass

        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            # If neither onnxruntime nor torch is installed, we can't check CUDA availability
            return False

    def uninstall_conflicting_packages(self):
        """Uninstall conflicting torch and onnxruntime packages"""
        packages_to_uninstall = [
            'torch', 'torchvision', 'torchaudio',
            'onnxruntime', 'onnxruntime-gpu'
        ]

        for package in packages_to_uninstall:
            try:
                logger.info(f'Uninstalling {package} if present...')
                subprocess.run(
                    f'{self.pip_cmd} uninstall {package} -y{self.arg_str}',
                    shell=True, check=False, capture_output=True
                )
            except Exception as e:
                logger.debug(f'Failed to uninstall {package}: {e}')

    def check_package_version(self, package_name, target_version):
        """Check if a package is installed with the target version"""
        try:
            result = subprocess.run(
                f'{self.pip_cmd} show {package_name}',
                shell=True, check=False, capture_output=True, text=True
            )
            if result.returncode == 0:
                # Parse the output to get version
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        current_version = line.split(':')[1].strip()
                        logger.info(f'{package_name} current version: {current_version}')
                        return current_version == target_version
            return False
        except Exception as e:
            logger.debug(f'Failed to check {package_name} version: {e}')
            return False

    def install_onnxruntime_gpu(self):
        """Install only onnxruntime-gpu without PyTorch for CUDA 12.4"""
        logger.hr('Installing ONNX Runtime GPU Only', 1)

        target_version = "1.19.2"

        # 检查当前是否已安装目标版本
        if self.check_package_version('onnxruntime-gpu', target_version):
            logger.info(f'✓ onnxruntime-gpu {target_version} already installed, skipping installation')
            # 仍然进行验证
            if self.verify_onnx_gpu_installation():
                logger.info('✓ ONNX Runtime GPU verification successful')
                return
            else:
                logger.warning('⚠ Existing installation verification failed, reinstalling...')
        else:
            logger.info(f'onnxruntime-gpu {target_version} not found, proceeding with installation')

        # 如果没有目标版本或验证失败，则卸载并重新安装
        packages_to_uninstall = ['onnxruntime', 'onnxruntime-gpu']
        for package in packages_to_uninstall:
            try:
                logger.info(f'Uninstalling {package} if present...')
                subprocess.run(
                    f'{self.pip_cmd} uninstall {package} -y{self.arg_str}',
                    shell=True, check=False, capture_output=True
                )
            except Exception as e:
                logger.debug(f'Failed to uninstall {package}: {e}')

        try:
            # 为CUDA 12.4安装兼容的onnxruntime-gpu版本
            # onnxruntime-gpu 1.19.0+ 支持CUDA 12.x
            onnx_cmd = f'{self.pip_cmd} install onnxruntime-gpu=={target_version}{self.arg_str}'
            logger.info(f'Installing onnxruntime-gpu {target_version} (compatible with CUDA 12.4)...')
            result = subprocess.run(onnx_cmd, shell=True, check=True, capture_output=True, text=True)
            logger.info('onnxruntime-gpu installation completed')

            # 验证安装
            if self.verify_onnx_gpu_installation():
                logger.info('✓ ONNX Runtime GPU installed successfully and CUDA is available')
            else:
                logger.warning('⚠ ONNX Runtime GPU installed but CUDA may not be available')

        except subprocess.CalledProcessError as e:
            logger.error(f'Failed to install onnxruntime-gpu: {e}')
            logger.error(f'Command output: {e.stdout if hasattr(e, "stdout") else ""}')
            logger.error(f'Command error: {e.stderr if hasattr(e, "stderr") else ""}')
            # Fallback to CPU installation
            logger.info('Falling back to CPU onnxruntime...')
            self.install_onnxruntime_cpu()

    def install_onnxruntime_cpu(self):
        """Install only onnxruntime CPU version"""
        logger.hr('Installing ONNX Runtime CPU Only', 1)

        target_version = "1.19.2"

        # 检查当前是否已安装目标版本
        if self.check_package_version('onnxruntime', target_version):
            logger.info(f'✓ onnxruntime {target_version} already installed, skipping installation')
            # 仍然进行验证
            if self.verify_onnx_installation():
                logger.info('✓ ONNX Runtime CPU verification successful')
                return
            else:
                logger.warning('⚠ Existing installation verification failed, reinstalling...')
        else:
            logger.info(f'onnxruntime {target_version} not found, proceeding with installation')

        # 如果没有目标版本或验证失败，则卸载并重新安装
        packages_to_uninstall = ['onnxruntime', 'onnxruntime-gpu']
        for package in packages_to_uninstall:
            try:
                logger.info(f'Uninstalling {package} if present...')
                subprocess.run(
                    f'{self.pip_cmd} uninstall {package} -y{self.arg_str}',
                    shell=True, check=False, capture_output=True
                )
            except Exception as e:
                logger.debug(f'Failed to uninstall {package}: {e}')

        try:
            # 安装onnxruntime CPU版本
            onnx_cmd = f'{self.pip_cmd} install onnxruntime=={target_version}{self.arg_str}'
            logger.info(f'Installing onnxruntime CPU version {target_version}...')
            result = subprocess.run(onnx_cmd, shell=True, check=True, capture_output=True, text=True)
            logger.info('onnxruntime CPU installation completed')

            # 验证安装
            if self.verify_onnx_installation():
                logger.info('✓ ONNX Runtime CPU installed successfully')
            else:
                logger.warning('⚠ ONNX Runtime CPU installed but verification failed')

        except subprocess.CalledProcessError as e:
            logger.error(f'Failed to install onnxruntime CPU: {e}')
            logger.error(f'Command output: {e.stdout if hasattr(e, "stdout") else ""}')
            logger.error(f'Command error: {e.stderr if hasattr(e, "stderr") else ""}')
            raise

    def install_cpu_dependencies(self):
        """Install CPU-only dependencies"""
        logger.hr('Installing CPU Dependencies', 1)

        # First uninstall any existing conflicting packages
        self.uninstall_conflicting_packages()

        try:
            # Install PyTorch CPU version
            torch_cmd = (
                f'{self.pip_cmd} install torch torchvision torchaudio '
                f'--index-url https://download.pytorch.org/whl/cpu{self.arg_str}'
            )
            logger.info('Installing PyTorch CPU version...')
            result = subprocess.run(torch_cmd, shell=True, check=True, capture_output=True, text=True)
            logger.info('PyTorch CPU installation completed')

            # Install onnxruntime CPU version (指定版本以确保兼容性)
            onnx_cmd = f'{self.pip_cmd} install "onnxruntime>=1.16.0,<1.23.0"{self.arg_str}'
            logger.info('Installing onnxruntime CPU version...')
            result = subprocess.run(onnx_cmd, shell=True, check=True, capture_output=True, text=True)
            logger.info('onnxruntime CPU installation completed')

            # 验证安装
            if self.verify_onnx_installation():
                logger.info('✓ CPU dependencies installed successfully')
            else:
                logger.warning('⚠ CPU dependencies installed but verification failed')

        except subprocess.CalledProcessError as e:
            logger.error(f'Failed to install CPU dependencies: {e}')
            logger.error(f'Command output: {e.stdout if hasattr(e, "stdout") else ""}')
            logger.error(f'Command error: {e.stderr if hasattr(e, "stderr") else ""}')
            raise

    def verify_onnx_installation(self):
        """Verify that ONNX Runtime installation is working"""
        try:
            # 清除已导入的模块以获取最新安装
            modules_to_clear = ['onnxruntime', 'onnxruntime.capi._pybind_state']
            for module in modules_to_clear:
                if module in sys.modules:
                    del sys.modules[module]

            import onnxruntime
            logger.info(f'ONNX Runtime verification: version {onnxruntime.__version__}')

            # 测试创建简单会话
            providers = onnxruntime.get_available_providers()
            logger.info(f'Available providers: {providers}')
            return True

        except Exception as e:
            logger.warning(f'ONNX Runtime verification failed: {e}')
            return False

    def verify_cuda_installation(self):
        """Verify that CUDA installation is working"""
        try:
            # Reimport torch to get the updated installation
            if 'torch' in sys.modules:
                del sys.modules['torch']

            import torch
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                device_count = torch.cuda.device_count()
                device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"
                logger.info(f'CUDA verification: {device_count} GPU(s) detected, primary device: {device_name}')

            # 同时验证 ONNX Runtime
            self.verify_onnx_installation()
            return cuda_available
        except Exception as e:
            logger.warning(f'CUDA verification failed: {e}')
            return False

    def verify_onnx_gpu_installation(self):
        """Verify that ONNX Runtime GPU installation is working"""
        try:
            # 清除已导入的模块以获取最新安装
            modules_to_clear = ['onnxruntime', 'onnxruntime.capi._pybind_state']
            for module in modules_to_clear:
                if module in sys.modules:
                    del sys.modules[module]

            import onnxruntime
            logger.info(f'ONNX Runtime verification: version {onnxruntime.__version__}')

            # 检查可用的执行提供者
            providers = onnxruntime.get_available_providers()
            logger.info(f'Available providers: {providers}')

            # 检查是否有CUDA支持
            has_cuda = 'CUDAExecutionProvider' in providers
            if has_cuda:
                logger.info('✓ CUDA Execution Provider is available')
            else:
                logger.warning('⚠ CUDA Execution Provider not found')

            return has_cuda

        except Exception as e:
            logger.warning(f'ONNX Runtime GPU verification failed: {e}')
            return False

    def install_dependencies(self, use_gpu=True):
        """Main method to install dependencies based on configuration"""
        if use_gpu:
            self.install_onnxruntime_gpu()
        else:
            self.install_onnxruntime_cpu()

if __name__ == "__main__":
    # Example usage
    pip_command = sys.executable + " -m pip"
    arg_string = " --trusted-host pypi.org --trusted-host files.pythonhosted.org"

    manager = GPUDependencyManager(pip_command, arg_string)
    manager.install_dependencies(use_gpu=True)
