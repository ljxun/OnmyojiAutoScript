# This Python file uses the following encoding: utf-8
# copy from alas https://github.com/LmeSzinc/AzurLaneAutoScript
from deploy.config import DeployConfig
from deploy.gpu_dependencies import GPUDependencyManager
from deploy.logger import logger
from deploy.utils import *
from urllib.parse import urlparse


class PipManager(DeployConfig):
    @cached_property
    def python(self):
        return self.filepath("PythonExecutable")

    @cached_property
    def requirements_file(self):
        if self.RequirementsFile == 'requirements.txt':
            return 'requirements.txt'
        else:
            return self.filepath("RequirementsFile")

    @cached_property
    def pip(self):
        return f'"{self.python}" -m pip'

    def pip_install(self):
        logger.hr('Update Dependencies', 0)

        if not self.InstallDependencies:
            logger.info('InstallDependencies is disabled, skip')
            return

        logger.hr('Check Python', 1)
        self.execute(f'"{self.python}" --version')

        arg = []
        if self.PypiMirror:
            mirror = self.PypiMirror
            arg += ['-i', mirror]
            # Trust http mirror or skip ssl verify
            if 'http:' in mirror or not self.SSLVerify:
                arg += ['--trusted-host', urlparse(mirror).hostname]
        elif not self.SSLVerify:
            arg += ['--trusted-host', 'pypi.org']
            arg += ['--trusted-host', 'files.pythonhosted.org']

        # Don't update pip, just leave it.
        # logger.hr('Update pip', 1)
        # self.execute(f'"{self.pip}" install --upgrade pip{arg}')
        arg += ['--disable-pip-version-check']

        # Install general dependencies first
        logger.hr('Update General Dependencies', 1)
        arg_str = ' ' + ' '.join(arg) if arg else ''
        self.execute(f'{self.pip} install -r {self.requirements_file}{arg_str}')

        # Handle GPU/CPU specific dependencies
        self._install_gpu_cpu_dependencies(arg_str)

    def _install_gpu_cpu_dependencies(self, arg_str):
        """Install GPU or CPU specific dependencies based on UseGpu configuration"""
        try:
            # Initialize GPU dependency manager
            gpu_manager = GPUDependencyManager(self.pip, arg_str)

            # Install dependencies based on UseGpu setting
            if hasattr(self, 'UseGpu') and self.UseGpu:
                logger.hr('GPU Dependencies Configuration', 1)
                logger.info('UseGpu is enabled, installing GPU dependencies...')
                gpu_manager.install_dependencies(use_gpu=True)
            else:
                logger.hr('CPU Dependencies Configuration', 1)
                logger.info('UseGpu is disabled or not configured, installing CPU dependencies...')
                gpu_manager.install_dependencies(use_gpu=False)

        except Exception as e:
            logger.error(f'Failed to install GPU/CPU dependencies: {e}')
            logger.info('Falling back to standard requirements installation only')
            # Continue with normal operation, don't fail the entire installation

if __name__ == "__main__":
    pip_manager = PipManager()
    pip_manager.pip_install()