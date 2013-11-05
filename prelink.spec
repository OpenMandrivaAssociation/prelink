%define	date	20111012

Summary:	An ELF prelinking utility
Name:		prelink
Epoch:		1
Version:	0.4.6
Release:	1.%{date}.6
License:	GPLv2+
Group:		System/Base
# actually, ripped from latest srpm from
# http://mirrors.kernel.org/fedora/development/15/source/SRPMS/prelink-0.4.4-1.fc15.src.rpm
Source0:	http://people.redhat.com/jakub/prelink/%{name}-%{date}.tar.bz2
Source2:	prelink.conf
Source3:	prelink.cron
Source4:	prelink.sysconfig
Source5:	prelink.macros
Source6:	prelink.logrotate
Patch0:		prelink-0.4.6-init.patch
Patch3:		fix-libgelf-linking.patch

BuildRequires:	elfutils-static-devel
BuildRequires:	glibc-static-devel
BuildRequires:	perl
Requires:	coreutils
Requires:	gawk
Requires:	grep
Requires:	findutils
Requires:	util-linux
Requires(post):	rpm-helper

%description
The prelink package contains a utility which modifies ELF shared libraries
and executables, so that far fewer relocations need to be resolved at runtime
and thus programs come up faster.

%prep
%setup -qn %{name}
%patch0 -p1 -b .init
cp -a %{SOURCE2} %{SOURCE3} %{SOURCE4} .
%patch1 -p0 -b .ionice
%patch2 -p0 -b .skip_debug
%patch3 -p1 -b .fix_libgelf
perl -MConfig -e '$path = "-l $Config{archlib}\n-l $Config{installvendorarch}\n"; $path =~ s/$Config{version}/*/g; print $path' >> prelink.conf
echo -e "-l %{py_platsitedir}\\n-l %{py_platlibdir}/lib-dynload\\n"|sed -e 's#%{py_ver}#*#g' >> prelink.conf
sed -i -e '/^prelink_LDADD/s/=/= -pthread/' src/Makefile.{am,in}

%build
%configure2_5x --disable-shared
%make

%check
%define testcc CC='gcc -Wl,--add-needed' CXX='g++ -Wl,--add-needed'
echo ====================TESTING=========================
#make -C testsuite check-harder %{testcc}
#make -C testsuite check-cycle %{testcc}
echo ====================TESTING END=====================

%install
%{makeinstall_std}
install -m644 %{SOURCE2} -D %{buildroot}%{_sysconfdir}/prelink.conf
install -m755 %{SOURCE3} -D %{buildroot}%{_sysconfdir}/cron.daily/prelink
install -m644 %{SOURCE4} -D %{buildroot}%{_sysconfdir}/sysconfig/prelink
install -m644 %{SOURCE5} -D %{buildroot}%{_sys_macros_dir}/%{name}.macros
install -m644 %{SOURCE6} -D %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

mkdir -p %{buildroot}{%{_localstatedir}/lib/misc,%{_var}/log/prelink}
touch %{buildroot}%{_localstatedir}/lib/misc/prelink.full
touch %{buildroot}%{_localstatedir}/lib/misc/prelink.force
touch %{buildroot}%{_var}/log/prelink/prelink.log

mkdir -p %{buildroot}%{_sysconfdir}/prelink.conf.d
touch %{buildroot}%{_sysconfdir}/prelink.cache

%post
%create_ghostfile %{_localstatedir}/lib/misc/prelink.full root root 644
%create_ghostfile %{_localstatedir}/lib/misc/prelink.force root root 644
%create_ghostfile %{_var}/log/prelink/prelink.log root root 600

%preun
if [ "$1" = "0" ]; then
 echo undo prelinking, it might take some time
 %{_sbindir}/prelink -ua 2> /dev/null
fi

# This is a bit sub-optimal and only does libraries for now,
# once trigger functionality in rpm has been extended so that
# matching files can be passed by name, we can do it faster
# and also trigger it on binaries as well.
# XXX: disabled, too slow, will rather consider re-enabling it
# per file when triggers has been extended with the necessary
# functionality
%if 0
#"%{distepoch}" >= "2012.0"
%triggerin -- /lib/*.so.*, /lib64/*.so.*, %{_prefix}/lib/*.so.*, %{_prefix}/lib64/*.so.*
[ -f %{_sysconfdir}/sysconfig/prelink ] && . %{_sysconfdir}/sysconfig/prelink
echo "`date`, %{_sbindir}/prelink $PRELINK_OPTS --libs-only --all --quick --verbose:" >> %{_var}/log/prelink/prelink.log
/usr/bin/time %{_sbindir}/prelink $PRELINK_OPTS --libs-only --all --quick --verbose &>> %{_var}/log/prelink/prelink.log
%endif

%files
%doc doc/prelink.pdf
%verify(not md5 size mtime) %config(noreplace) %{_sysconfdir}/prelink.conf
%verify(not md5 size mtime) %config(noreplace) %{_sysconfdir}/sysconfig/prelink
%verify(not md5 size mtime) %{_sysconfdir}/prelink.cache
%dir %{_sysconfdir}/prelink.conf.d
%config(noreplace) %{_sys_macros_dir}/%{name}.macros
%{_sysconfdir}/cron.daily/prelink
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%{_sbindir}/prelink
%{_bindir}/execstack
%{_mandir}/man8/prelink.8*
%{_mandir}/man8/execstack.8*
%dir %{_var}/log/prelink
%attr(0644,root,root) %verify(not md5 size mtime) %ghost %config(missingok,noreplace) %{_localstatedir}/lib/misc/prelink.full
%attr(0644,root,root) %verify(not md5 size mtime) %ghost %config(missingok,noreplace) %{_localstatedir}/lib/misc/prelink.force
%attr(0600,root,root) %verify(not md5 size mtime) %ghost %config(missingok,noreplace) %{_var}/log/prelink/prelink.log

