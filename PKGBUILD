
pkgdesc="An attemp to bring Xware (Xunlei on routers) to desktop Linux."
url="http://www.cuoan.net/xware_desktop"

pkgname="xware_desktop"
pkgver="0.1"
arch=("i686" "x86_64")
pkgrel=2
license=("GPL")

makedepends=("git" "python-pyqt5")
if test "$CARCH" == x86_64; then
    makedepends+=("lib32-glib2")
else
    makedepends+=("glib2")
fi

depends=("python-pyqt5" "qt5-webkit")
if test "$CARCH" == x86_64; then
    depends+=("lib32-glibc" "lib32-zlib" "lib32-glib2")
else
    depends+=("glibc" "zlib" "glib2")
fi

source=("Xware1.0.7_x86_32_glibc.zip")
md5sums=("34e522b8248919d7ee4284b8b369de27")

install=.install

build() {
  make all
}

package() {
  # copy xware to /opt/xware_desktop/xware
  install -D ETMDaemon                       ${pkgdir}/opt/xware_desktop/xware/lib/ETMDaemon
  install -D EmbedThunderManager             ${pkgdir}/opt/xware_desktop/xware/lib/EmbedThunderManager
  install -D portal                          ${pkgdir}/opt/xware_desktop/xware/portal
  
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

