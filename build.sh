set -o xtrace

setup_root() {
    apt-get install -qq -y \
        python3-pip \
        cmake

    pip3 install -qq \
        numba \
        pytest \
        scikit-image \
        tqdm \
        matplotlib
}

setup_checker() {
    python3 -c 'import numba; print(numba.__version__)'
}

"$@"