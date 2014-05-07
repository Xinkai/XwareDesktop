# 请填写第一行的commit号

%global commit
%global reponame        XwareDesktop
%global debug_package   %{nil}
%global __python        %{__python3}

Name:               xware-desktop
Version:            0.8
Release:            1%{?dist}
Summary:            An attempt to bring Xware (Xunlei on routers) to desktop Linux.

Group:              Applications/Internet
License:            GPLv3
URL:                https://github.com/Xinkai/XwareDesktop/wiki
Source0:            https://github.com/Xinkai/XwareDesktop/archive/%{commit}/%{commit}.tar.gz

BuildRequires:      python-qt5-devel
BuildRequires:      glibc-devel(x86-32)
BuildRequires:      libgcc(x86-32)
BuildRequires:      pkgconfig(x86-32)
BuildRequires:      glib2-devel(x86-32)
BuildRequires:      libmount-devel
BuildRequires:      coffee-script
BuildRequires:      chrpath >= 0.14
BuildRequires:      findutils

Requires:           python3 >= 3.3
Requires:           glibc(x86-32)
Requires:           zlib(x86-32)
Requires:           glib2(x86-32)
Requires:           libmount
Requires:           python3-qt5
Requires:           qt5-qtwebkit
Requires:           qt5-qtmultimedia
Requires:           python3-requests
Requires:           python3-inotify
Requires(post):     desktop-file-utils
Requires(post):     libcap

%description
An attempt to bring Xware (Xunlei on routers) to desktop Linux.

%prep
%autosetup -n %{reponame}-%{commit}

%build

%install
make DESTDIR=%{buildroot} install
install -D -m 664 src/xwared.service %{buildroot}/usr/lib/systemd/system/xwared.service

%files
%doc
/opt/xware_desktop
/usr/share/applications/xware_desktop.desktop
/usr/lib/systemd/system/xwared.service
/usr/bin/xware-desktop

%pre
    if [ $1 -eq 1 ]; then
        # pre_install
        getent group xware >/dev/null 2>&1
        RET=$?
        if [ $RET -eq 0 ]; then
            useradd --no-create-home --gid xware --shell /bin/false --system xware
        else
            useradd --no-create-home --user-group --shell /bin/false --system xware
        fi    
    fi

    if [ $1 -eq 2 ]; then
        # pre_upgrade
        find /opt/xware_desktop/frontend -name "__pycache__" -print0 | xargs -0 rm -rf
    fi

%post
    # Fedora specific, same as Arch
    systemctl daemon-reload
    update-desktop-database -q

    touch     /opt/xware_desktop/{settings.ini,mounts}
    touch     /opt/xware_desktop/xware/cfg/{cid_store.dat,dht.cfg,download.cfg,etm.cfg,kad.cfg}
    chmod 664 /opt/xware_desktop/{settings.ini,mounts}
    chmod 664 /opt/xware_desktop/xware/cfg/{cid_store.dat,dht.cfg,download.cfg,etm.cfg,kad.cfg}
    python3   -O -m compileall -q /opt/xware_desktop/frontend
    chown -R xware:xware /opt/xware_desktop
    setcap "CAP_SETUID=+ep CAP_SETGID=+ep" /opt/xware_desktop/permissioncheck

    echo "欢迎使用Xware Desktop。"
    echo "设置方法和注意事项见项目主页。"
    echo "项目主页 https://github.com/Xinkai/XwareDesktop/wiki"
    echo "Github https://github.com/Xinkai/XwareDesktop"

%preun
    if [ $1 -eq 0 ]; then
        # uninstall
        systemctl stop xwared
    fi

%postun
    if [ $1 -eq 0 ]; then
        # uninstall
        userdel xware 2>/dev/null
        echo "Xware Desktop卸载完成。配置文件未删除，你可以手动删除/opt/xware_desktop内所有内容。"
        rm -rf /opt/xware_desktop/frontend
    fi

%changelog
