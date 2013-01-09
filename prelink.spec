%define	date	20111012

Name:		prelink
Version:	0.4.6
Release:	1.%{date}.3
Summary:	An ELF prelinking utility
License:	GPLv2+
Epoch:		1
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

BuildRequires:	elfutils-static-devel glibc-static-devel perl
Requires:	coreutils findutils
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
%make -C testsuite check-harder %{testcc}
%make -C testsuite check-cycle %{testcc}
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


%changelog
* Sun Jul 17 2011 Per Øyvind Karlsen <peroyvind@mandriva.org> 1:0.4.5-1.20110622.5
+ Revision: 690149
- we might just as well prelink python modules as we do for perl.. :)

* Sat Jul 16 2011 Per Øyvind Karlsen <peroyvind@mandriva.org> 1:0.4.5-1.20110622.4
+ Revision: 690110
- disable file trigger for cooker also for now..
- don't enable file trigger on 2011

* Fri Jul 15 2011 Per Øyvind Karlsen <peroyvind@mandriva.org> 1:0.4.5-1.20110622.3
+ Revision: 690047
- fix so that perl module path doesn't have perl version hardcoded

* Fri Jul 15 2011 Per Øyvind Karlsen <peroyvind@mandriva.org> 1:0.4.5-1.20110622.2
+ Revision: 690046
- apply some cosmetics
- fix incorrect path to log ghost file created and for logrotate
- add a file trigger to run prelink in quick mode for libraries

* Thu Jul 14 2011 Per Øyvind Karlsen <peroyvind@mandriva.org> 1:0.4.5-1.20110622.1
+ Revision: 690038
- haul out some trash
- update license
- new version

* Fri Apr 08 2011 Paulo Andrade <pcpa@mandriva.com.br> 1:0.4.4-1.20101123.1
+ Revision: 651897
- Update to latest fedora version

* Sat Aug 28 2010 Tomasz Pawel Gajc <tpg@mandriva.org> 1:0.4.3-1.20100106.1mdv2011.0
+ Revision: 573979
- update to new version 0.4.3

* Wed Dec 02 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 1:0.4.2-1.20091104.1mdv2010.1
+ Revision: 472611
- Updated to 20091104 snapshot.

* Sat Sep 26 2009 Frederik Himpe <fhimpe@mandriva.org> 1:0.4.2-1.20090925.1mdv2010.0
+ Revision: 449647
- Update to new version 20090925

* Thu Jul 30 2009 Frederik Himpe <fhimpe@mandriva.org> 1:0.4.2-1.20090709.1mdv2010.0
+ Revision: 404832
- Update to new version 0.4.2-20090709 from Fedora

* Thu Dec 18 2008 Frederic Crozat <fcrozat@mandriva.com> 1:0.4.0-1.20071009.4mdv2009.1
+ Revision: 315630
- Add preun script to undo prelink when uninstalling package
- Update configuration to prelink kde3 too

* Mon Jun 02 2008 Pixel <pixel@mandriva.com> 1:0.4.0-1.20071009.3mdv2009.0
+ Revision: 214231
- adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

  + Thierry Vignaud <tv@mandriva.org>
    - remove useless kernel require
    - kill re-definition of %%buildroot on Pixel's request

  + Olivier Blin <oblin@mandriva.com>
    - restore BuildRoot

* Thu Dec 06 2007 Thierry Vignaud <tv@mandriva.org> 1:0.4.0-1.20071009.2mdv2008.1
+ Revision: 115914
- prelink perl modules in vendor directory too
- log file has moved
- enable test suite

* Wed Dec 05 2007 Thierry Vignaud <tv@mandriva.org> 1:0.4.0-1.20071009.1mdv2008.1
+ Revision: 115690
- prelink perl too
- patch 2: skip debug files from *-debug packages
- patch 1: use ionice
- alter management of extra sources so that we can patch them while still easily
  enabling to sync with fedora
- sync description with fedora
- new release (from fedora)

* Tue Nov 13 2007 Thierry Vignaud <tv@mandriva.org> 1:0.3.10-1.20061201.2mdv2008.1
+ Revision: 108452
- use ionice


* Sat Jan 13 2007 Olivier Thauvin <nanardon@mandriva.org> 0.3.10-1.20061201.1mdv2007.0
+ Revision: 108357
- From (Frederik Himpe <fhimpe at telenet.be>)
  * update to 0.3.10 (supports DT_GNU_HASH)
  * run /sbin/init U after init is prelinked, otherwise umounting of / will fail

* Tue Aug 08 2006 Olivier Thauvin <nanardon@mandriva.org> 1:0.3.6-1.20060213.1mdv2007.0
+ Revision: 54230
- fix release tag according software version
- add sources files...
- 20060213
- Import prelink

* Tue Jan 31 2006 Per Øyvind Karlsen <pkarlsen@mandriva.com> 0.3.6-1mdk
- 0.3.6
- fix executable-marked-as-config-file

* Sat Jan 14 2006 Olivier Thauvin <nanardon@mandriva.org> 0.3.5-2mdk
- don't use anymore /etc/rpm/macros.%%name but /etc/rpm/macros.d

* Fri Jul 08 2005 Per Øyvind Karlsen <pkarlsen@mandriva.com> 0.3.5-1mdk
- 0.3.5
- fix requires
- %%mkrel

* Thu Feb 17 2005 Per Øyvind Karlsen <peroyvind@linux-mandrake.com> 0.3.4-1mdk
- 0.3.4

* Fri Dec 17 2004 Per Øyvind Karlsen <peroyvind@linux-mandrake.com> 0.3.3-1mdk
- 0.3.3 (sync with fedora)

* Thu Jul 29 2004 Thierry Vignaud <tvignaud@mandrakesoft.com> 0.3.2-2mdk
- fix update from mdk10.0

* Thu Jun 17 2004 Per Øyvind Karlsen <peroyvind@linux-mandrake.com> 0.3.2-1mdk
- sync with fedora
- cosmetics
- disable tests

