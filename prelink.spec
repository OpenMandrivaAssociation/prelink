%define	name	prelink
%define	version	0.4.0
%define	date	20071009
%define rel 1
%define	release	%mkrel 1.%{date}.%{rel}

Summary:	An ELF prelinking utility
Name:		%{name}
Version:	%{version}
Release:	%{release}
License:	GPL
Epoch:		1
Group:		System/Base
Source0:	ftp://people.redhat.com/jakub/prelink/%{name}-%{date}.tar.bz2
Source2:	prelink.conf
Source3:	prelink.cron
Source4:	prelink.sysconfig
Patch0:		prelink-0.3.10-init.patch
Patch1:		cron-use-ionice.diff
Patch2:		conf-skip-debug-files.patch

Buildroot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildRequires:	elfutils-static-devel glibc-static-devel perl
Requires:	kernel >= 2.4.10 coreutils findutils
Requires:	util-linux gawk grep
Requires(post):	rpm-helper

%description
The prelink package contains a utility which modifies ELF shared libraries
and executables, so that far fewer relocations need to be resolved at runtime
and thus programs come up faster.

%prep
%setup -q -n %{name}
%patch0 -p1 -b .init
cp -a %{SOURCE2} %{SOURCE3} %{SOURCE4} .
%patch1 -p0 -b .ionice
%patch2 -p0 -b .skip_debug
perl -MConfig -e 'print "-l $Config{archlib}\n"' >> prelink.conf

%build
%configure --disable-shared
%make

%check
echo ====================TESTING=========================
%make -C testsuite check-harder
%make -C testsuite check-cycle
echo ====================TESTING END=====================

%install
rm -rf $RPM_BUILD_ROOT
%{makeinstall}
mkdir -p %{buildroot}%{_sys_macros_dir}
cp -a prelink.conf %{buildroot}%{_sysconfdir}

mkdir -p %{buildroot}%{_sysconfdir}/{sysconfig,cron.daily,logrotate.d}

cp -a prelink.cron %{buildroot}%{_sysconfdir}/cron.daily/prelink
cp -a prelink.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/prelink
chmod 755 %{buildroot}%{_sysconfdir}/cron.daily/prelink
chmod 644 %{buildroot}%{_sysconfdir}/{sysconfig/prelink,prelink.conf}
cat > %{buildroot}%{_sys_macros_dir}/%name.macros <<"EOF"
# rpm-4.1 verifies prelinked libraries using a prelink undo helper.
#       Note: The 2nd token is used as argv[0] and "library" is a
#       placeholder that will be deleted and replaced with the appropriate
#       library file path.
%%__prelink_undo_cmd     %{_sbindir}/prelink prelink -y library
EOF

chmod 644 %{buildroot}%{_sys_macros_dir}/%name.macros

mkdir -p %{buildroot}{%{_localstatedir}/misc,%{_var}/log}
touch %{buildroot}%{_localstatedir}/misc/prelink.full
touch %{buildroot}%{_localstatedir}/misc/prelink.force
touch %{buildroot}%{_var}/log/prelink.log

cat > %buildroot%{_sysconfdir}/logrotate.d/%{name} << EOF
/var/log/prelink.log {
    missingok
    notifempty
}
EOF

%post
%create_ghostfile %{_localstatedir}/misc/prelink.full root root 644
%create_ghostfile %{_localstatedir}/misc/prelink.force root root 644
%create_ghostfile %{_var}/log/prelink.log root root 600

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc doc/prelink.pdf
%verify(not md5 size mtime) %config(noreplace) %{_sysconfdir}/prelink.conf
%verify(not md5 size mtime) %config(noreplace) %{_sysconfdir}/sysconfig/prelink
%config(noreplace) %{_sys_macros_dir}/%{name}.macros
%{_sysconfdir}/cron.daily/prelink
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%{_sbindir}/prelink
%{_bindir}/execstack
%{_mandir}/man8/prelink.8*
%{_mandir}/man8/execstack.8*
%attr(0644,root,root) %verify(not md5 size mtime) %ghost %config(missingok,noreplace) %{_localstatedir}/misc/prelink.full
%attr(0644,root,root) %verify(not md5 size mtime) %ghost %config(missingok,noreplace) %{_localstatedir}/misc/prelink.force
%attr(0600,root,root) %verify(not md5 size mtime) %ghost %config(missingok,noreplace) %{_var}/log/prelink.log



