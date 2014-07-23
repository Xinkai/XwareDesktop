# 请填写第一行的commit号

%global commit
%global reponame        XwareDesktop
%global debug_package   %{nil}
%global __python        %{__python3}

Name:               xware-desktop
Version:            0.11
Release:            1%{?dist}
Summary:            An attempt to bring Xware (Xunlei on routers) to desktop Linux.

Group:              Applications/Internet
License:            GPLv3
URL:                https://github.com/Xinkai/XwareDesktop/wiki
Source0:            https://github.com/Xinkai/XwareDesktop/archive/%{commit}/%{commit}.tar.gz

BuildRequires:      python-qt5-devel
BuildRequires:      glibc-devel(x86-32)
BuildRequires:      libgcc(x86-32)
BuildRequires:      coffee-script
BuildRequires:      chrpath >= 0.14
BuildRequires:      findutils
BuildRequires:      sed

Requires:           python3 >= 3.4
Requires:           glibc(x86-32)
Requires:           zlib(x86-32)
Requires:           python3-qt5 >= 5.2
Requires:           qt5-qtwebkit >= 5.2
Requires:           qt5-qtmultimedia >= 5.2
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

%files
%doc
/opt/xware-desktop
/usr/share/applications/xware-desktop.desktop
/usr/share/icons/hicolor
/usr/bin/xware-desktop

%pre
    if [ $1 -eq 1 ]; then
        # pre_install
    fi

    if [ $1 -eq 2 ]; then
        # pre_upgrade
    fi

%post
    # Fedora specific, same as Arch
    update-desktop-database -q

    setcap CAP_SYS_ADMIN=+ep /opt/xware-desktop/chmns

    echo "欢迎使用Xware Desktop。"
    echo "设置方法和注意事项见项目主页。"
    echo "项目主页 https://github.com/Xinkai/XwareDesktop/wiki"
    echo "Github https://github.com/Xinkai/XwareDesktop"

%preun
    if [ $1 -eq 0 ]; then
        # uninstall
    fi

%postun
    if [ $1 -eq 0 ]; then
        # uninstall
        echo "Xware Desktop卸载完成。"
        echo "用户配置文件位于~/.xware-desktop，并未删除。"
    fi

%changelog
