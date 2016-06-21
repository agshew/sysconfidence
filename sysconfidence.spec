Name:           sysconfidence
Version:        20151109
Release:        1%{?dist}
Summary:        System benchmarks with comprehensive statistics

Group:          Applications/System
License:        Free with conditions
URL:            https://github.com/agshew/sysconfidence
Source0:        %{name}-%{version}.tar.gz
Source1:        %{name}-modulefile
BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:  mpi
Requires:       mpi
AutoReq:	no

%description
A system performance benchmark that produces comprehensive
statistics instead of one (or a few) numbers that cannot fully characterize a
machine.


%prep
%setup -q
scripts/config.sh x86cluster

%build
type mpicc &> /dev/null || 
if [[ "$?" -ne 0 ]]; then
  . /etc/profile.d/modules.sh
  export MODULEPATH=$MODULEPATH:/opt/modules/modulefiles
  module load openmpi-gnu
fi
make %{?_smp_mflags}


%install
rm -rf %{buildroot}
%{__mkdir_p} %{buildroot}/opt/%{name}/bin
%{__mkdir_p} %{buildroot}/opt/%{name}/doc
%{__mkdir_p} %{buildroot}/opt/modules/modulefiles/%{name}
%{__install}  -p -m755 ./sysconfidence  %{buildroot}/opt/%{name}/bin/sysconfidence
%{__install}  -p -m755 ./scripts/scgraph.py  %{buildroot}/opt/%{name}/bin/scgraph.py
%{__install}  -p -m755 ./scripts/scpercentiles.py  %{buildroot}/opt/%{name}/bin/scpercentiles.py
%{__install}  -p -m755 ./README.md  %{buildroot}/opt/%{name}/doc/
%{__install}  -p -m755 ./LICENSE  %{buildroot}/opt/%{name}/doc/
%{__install}  -p -m755 %{SOURCE1}  %{buildroot}/opt/modules/modulefiles/%{name}/%{version}

%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%attr(0755,root,root) %dir /opt/%{name}
%attr(0755,root,root) %dir /opt/%{name}/bin
%attr(0755,root,root) %dir /opt/%{name}/doc
%attr(0755,root,root) /opt/%{name}/bin/sysconfidence
%attr(0755,root,root) /opt/%{name}/bin/scgraph.py
%attr(0755,root,root) /opt/%{name}/bin/scpercentiles.py
%attr(0755,root,root) /opt/modules/modulefiles/%{name}/%{version}
%doc /opt/%{name}/doc/*



%changelog
* Mon Nov 09 2015 Andrew G. Shewmaker <shewa@lanl.gov> 20151109
- use newer MPI 2.2 datatype instead of fortran type
- only load openmpi-gnu module if mpicc isn't available
- add spec file to repo

* Thu Nov 05 2015 Andrew G. Shewmaker <shewa@lanl.gov> 20151105
- First cut.
