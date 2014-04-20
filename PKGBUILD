# Maintainer: Xinkai <yeled.nova@gmail.com>
pkgdesc="An attempt to bring Xware (Xunlei on routers) to desktop Linux."
url="http://www.cuoan.net/xware-desktop"

_commit=""
_md5sums=""
pkgver=""
pkgrel=

pkgname="xware_desktop-git"
arch=("i686" "x86_64")
conflicts=("xware_desktop")
license=("GPL" "custom")

makedepends=("python-pyqt5" "coffee-script" "chrpath" "findutils")
if test "$CARCH" == x86_64; then
    makedepends+=("lib32-glib2" "gcc-multilib")
else
    makedepends+=("glib2" "gcc")
fi

depends=("python-pyqt5" "qt5-webkit" "qt5-multimedia" "libcap" "python-requests" "python-pyinotify" "desktop-file-utils")
if test "$CARCH" == x86_64; then
    depends+=("lib32-glibc" "lib32-zlib" "lib32-glib2")
else
    depends+=("glibc" "zlib" "glib2")
fi

if [ ! -f .localdev ]; then
    source=("${_commit}.tar.gz::https://github.com/Xinkai/XwareDesktop/archive/${_commit}.tar.gz")
    md5sums=(${_md5sums})
    _nonlocal=1
fi

install=xware_desktop.install

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
    install -D -m 644 src/xwared.service ${pkgdir}/usr/lib/systemd/system/xwared.service
    echo -e "\n__githash__ = \"${_commit}\"\n" >> ${pkgdir}/opt/xware_desktop/frontend/__init__.py
}
