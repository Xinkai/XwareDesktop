# 请填写第一行的commit号

%global commit
%global reponame        XwareDesktop
%global debug_package   %{nil}
%global __python        %{__python3}

Name:               xware-desktop
Version:            0.9
Release:            1%{?dist}
Summary:            An attempt to bring Xware (Xunlei on routers) to desktop Linux.

Group:              Applications/Internet
License:            GPLv3
URL:                https://github.com/Xinkai/XwareDesktop/wiki
Source0:            https://github.com/Xinkai/XwareDesktop/archive/%{commit}/%{commit}.tar.gz

BuildRequires:      python-qt5-devel
BuildRequires:      glibc-devel(x86-32)
BuildRequires:      libgcc(x86-32)
BuildRequires:      libmount-devel
BuildRequires:      coffee-script
BuildRequires:      chrpath >= 0.14
BuildRequires:      findutils
BuildRequires:      sed

Requires:           python3 >= 3.3
Requires:           glibc(x86-32)
Requires:           zlib(x86-32)
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
install -D -m 664 build/xwared.service %{buildroot}/usr/lib/systemd/system/xwared.service

%files
%doc
/opt/xware-desktop
/usr/share/applications/xware-desktop.desktop
/usr/share/icons/hicolor
/usr/lib/systemd/system/xwared.service
/usr/bin/xware-desktop

%pre
    if [ $1 -eq 1 ]; then
        # pre_install
    fi

    if [ $1 -eq 2 ]; then
        # pre_upgrade
        find /opt/xware-desktop -name "__pycache__" -print0 | xargs -0 rm -rf
    fi

%post
    # Fedora specific, same as Arch
    systemctl daemon-reload
    update-desktop-database -q

    python3   -O -m compileall -q /opt/xware-desktop/frontend

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
        echo "Xware Desktop卸载完成。配置文件未删除，你可以手动删除/opt/xware-desktop内所有内容。"
        rm -rf /opt/xware-desktop/frontend
        rm -rf /opt/xware-desktop/daemon
        rm -rf /opt/xware-desktop/shared
    fi

%changelog
