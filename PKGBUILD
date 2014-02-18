
pkgdesc="An attempt to bring Xware (Xunlei on routers) to desktop Linux."
url="http://www.cuoan.net/xware_desktop"

pkgname="xware_desktop-git"
pkgver="20140218"
arch=("i686" "x86_64")
conflicts=("xware_desktop")
pkgrel=1
license=("GPL" "custom")

makedepends=("git" "python-pyqt5" "coffee-script")
if test "$CARCH" == x86_64; then
    makedepends+=("lib32-glib2" "gcc-multilib")
else
    makedepends+=("glib2" "gcc")
fi

depends=("python-pyqt5" "qt5-webkit" "libcap" "python-requests")
if test "$CARCH" == x86_64; then
    depends+=("lib32-glibc" "lib32-zlib" "lib32-glib2")
else
    depends+=("glibc" "zlib" "glib2")
fi

if [ ! -f .localdev ]; then
    source=("git+https://github.com/Xinkai/XwareDesktop.git")
    md5sums=('SKIP')
fi

install=xware_desktop.install

prepare() {
  if [ ! -f ${srcdir}/../.localdev ]; then
    cp -R ${srcdir}/XwareDesktop/src/* ${srcdir}
    mkdir -p ${srcdir}/xware
    cp -R ${srcdir}/XwareDesktop/xware/* ${srcdir}/xware
    rm -rf ${srcdir}/XwareDesktop
  else
    ln -sf ${srcdir}/../xware ${srcdir}
  fi
}

build() {
  make all
}

package() {
  make DEST_DIR=$pkgdir install
}

