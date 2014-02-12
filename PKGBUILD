
pkgdesc="An attempt to bring Xware (Xunlei on routers) to desktop Linux."
url="http://www.cuoan.net/xware_desktop"

pkgname="xware_desktop"
pkgver="0.1"
arch=("i686" "x86_64")
pkgrel=2
license=("GPL")

makedepends=("git" "python-pyqt5" "coffee-script")
if test "$CARCH" == x86_64; then
    makedepends+=("lib32-glib2" "gcc-multilib")
else
    makedepends+=("glib2" "gcc")
fi

depends=("python-pyqt5" "qt5-webkit")
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
    ln -s ${srcdir}/../xware ${srcdir}
  fi
}

build() {
  make all
}

package() {
  # copy xware to /opt/xware_desktop/xware
  install -D xware/ETMDaemon                 ${pkgdir}/opt/xware_desktop/xware/lib/ETMDaemon
  install -D xware/EmbedThunderManager       ${pkgdir}/opt/xware_desktop/xware/lib/EmbedThunderManager
  install -D xware/portal                    ${pkgdir}/opt/xware_desktop/xware/portal
  
  # copy libmounthelper
  install -D build/libmounthelper.so         ${pkgdir}/opt/xware_desktop/libmounthelper.so
  
  # copy systemd service
  install -D xwared.service                  ${pkgdir}/usr/lib/systemd/system/xwared.service

  install -D build/xwared                    ${pkgdir}/opt/xware_desktop/xwared

  # install frontend
  cp -R frontend                             ${pkgdir}/opt/xware_desktop/frontend
  rm -rf ${pkgdir}/opt/xware_desktop/frontend/__pycache__
  rm -rf ${pkgdir}/opt/xware_desktop/frontend/ui
  rm -f  ${pkgdir}/opt/xware_desktop/frontend/xwarejs.coffee
  rm -f  ${pkgdir}/opt/xware_desktop/frontend/Makefile

  # install desktop entry
  install -D frontend/ui/rc/thunder.ico      ${pkgdir}/opt/xware_desktop/frontend/thunder.ico
  install -D frontend/xware_desktop.desktop  ${pkgdir}/usr/share/applications/xware_desktop.desktop

  chmod -R 775 ${pkgdir}/opt/xware_desktop
}

