# Maintainer: Xinkai <yeled.nova@gmail.com>
pkgdesc="An attempt to bring Xware (Xunlei on routers) to desktop Linux."
url="https://github.com/Xinkai/XwareDesktop/wiki"

_commit=""
_md5sums=""
pkgver=""
pkgrel=

pkgname="xware-desktop-git"
arch=("i686" "x86_64")
conflicts=("xware-desktop")
license=("GPL" "custom")

makedepends=("python-pyqt5" "coffee-script" "chrpath" "findutils" "sed")
if test "$CARCH" == x86_64; then
    makedepends+=("gcc-multilib")
else
    makedepends+=("gcc")
fi

depends=("python-pyqt5" "qt5-webkit" "qt5-multimedia" "libcap" "python-requests" "python-pyinotify" "desktop-file-utils")
if test "$CARCH" == x86_64; then
    depends+=("lib32-glibc" "lib32-zlib")
else
    depends+=("glibc" "zlib")
fi

if [ ! -f .localdev ]; then
    source=("${_commit}.tar.gz::https://github.com/Xinkai/XwareDesktop/archive/${_commit}.tar.gz")
    md5sums=(${_md5sums})
    _nonlocal=1
fi

install=xware-desktop.install

build() {
    if test $_nonlocal; then
        cd XwareDesktop-${_commit}
    else
        cd ../
    fi
    make all
}

package() {
    if test $_nonlocal; then
        cd XwareDesktop-${_commit}
    else
        cd ../
    fi
    make DESTDIR=${pkgdir} install
    echo -e "\n__githash__ = \"${_commit}\"\n" >> ${pkgdir}/opt/xware-desktop/shared/__init__.py
}
