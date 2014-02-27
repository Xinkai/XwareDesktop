
pkgdesc="An attempt to bring Xware (Xunlei on routers) to desktop Linux."
url="http://www.cuoan.net/xware_desktop"
_commit="39989a29949fdaab75e78b040b8dff4c2031af7f"

pkgname="xware_desktop-git"
pkgver="20140228"
arch=("i686" "x86_64")
conflicts=("xware_desktop")
pkgrel=2
license=("GPL" "custom")

makedepends=("python-pyqt5" "coffee-script")
if test "$CARCH" == x86_64; then
    makedepends+=("lib32-glib2" "gcc-multilib")
else
    makedepends+=("glib2" "gcc")
fi

depends=("python-pyqt5" "qt5-webkit" "libcap" "python-requests" "python-pyinotify")
if test "$CARCH" == x86_64; then
    depends+=("lib32-glibc" "lib32-zlib" "lib32-glib2")
else
    depends+=("glibc" "zlib" "glib2")
fi

if [ ! -f .localdev ]; then
    source=("${_commit}.tar.gz::https://github.com/Xinkai/XwareDesktop/archive/${_commit}.tar.gz")
    md5sums=('SKIP')
    _nonlocal=1
fi

install=xware_desktop.install

build() {
    if test $_nonlocal; then
        cd XwareDesktop-${_commit}/src
    fi
    make all
}

package() {
    if test $_nonlocal; then
        cd XwareDesktop-${_commit}/src
    fi
    make DEST_DIR=${pkgdir} install
}

