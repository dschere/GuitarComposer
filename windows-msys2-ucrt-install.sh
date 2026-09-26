# Installation script for windows msys2 ucrt 
# Update the system
pacman -Syu --noconfirm

pacman -Sy --noconfirm  mingw-w64-ucrt-x86_64-cmake
pacman -Sy --noconfirm  libuv git
pacman -Sy --noconfirm  mingw-w64-ucrt-x86_64-toolchain gcc base-devel
pacman -Sy --noconfirm  mingw-w64-x86_64-libevent

pacman -Sy --noconfirm  mingw-w64-ucrt-x86_64-python
pacman -Sy --noconfirm  mingw-w64-ucrt-x86_64-python-setuptools
pacman -Sy --noconfirm  mingw-w64-ucrt-x86_64-python-lxml
pacman -Sy --noconfirm  mingw-w64-ucrt-x86_64-python-numpy
pacman -Sy --noconfirm  mingw-w64-ucrt-x86_64-python-scipy
pacman -Sy --noconfirm  mingw-w64-ucrt-x86_64-python-pyqt6
pacman -Sy --noconfirm  mingw-w64-ucrt-x86_64-python-pyqt6-sip


# For PyInstaller:
pacman -Sy --noconfirm mingw-w64-ucrt-x86_64-pyinstaller

# For cx_Freeze:
pacman -Sy --noconfirm mingw-w64-ucrt-x86_64-python-cx-freeze

env -i PATH=$(echo $PATH):/mingw64/bin /mingw64/lib /mingw64/include

# create virtual environment + pacman packages
python -m venv msys2_venv --system-site-packages
source msys2_venv/bin/activate

python -m pip install --upgrade pip
python -m pip install partitura pydantic pyqtdarktheme singleton-decorator typing_extensions pyudev requests

python setup.py build_ext --inplace
# or if using a modern pyproject.toml / pip:
pip install -e .

pyi-makespec --onedir windows_msys2_ucrt_main.py

"""
must modify the .spec file
Modify the .spec file if your C extension loads files dynamically, or if PyInstaller misses a specific pacman DLL. Inside your_main_script.spec, update the binaries or datas list:python# Example manually linking an MSYS2 DLL if automatic tracing fails
binaries=[('/ucrt64/bin/libcrypto-3-x64.dll', '.')]


pyinstaller your_main_script.spec
"""