# Created by pyp2rpm-2.0.0
%global pypi_name scitokens-credmon

Name:           python-%{pypi_name}
Version:        0.1
Release:        1%{?dist}
Summary:        Scitokens credential monitor for use with HTCondor

License:        MIT
URL:            https://github.com/htcondor/scitokens-credmon
Source0:        https://test-files.pythonhosted.org/packages/09/17/ac47313b45b62691fa50a19311a60e3f16f9e6a20c7bdf7e41fe904cc2b2/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python2-devel
BuildRequires:  python-setuptools

%description


%package -n     python2-%{pypi_name}
Summary:        Scitokens credential monitor for use with HTCondor
%{?python_provide:%python_provide python2-%{pypi_name}}
 
Requires:       condor-python
Requires:       python-requests-oauthlib
Requires:       python-six
Requires:       python-flask
%description -n python2-%{pypi_name}



%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py2_build

%install
%py2_install
cp %{buildroot}/%{_bindir}/condor_credmon %{buildroot}/%{_bindir}/condor_credmon-2
ln -sf %{_bindir}/condor_credmon-2 %{buildroot}/%{_bindir}/condor_credmon-%{python2_version}


%files -n python2-%{pypi_name} 
%doc 
%{_bindir}/condor_credmon
%{_bindir}/condor_credmon-2
%{_bindir}/condor_credmon-%{python2_version}
%{python2_sitelib}/credmon
%{python2_sitelib}/scitokens_credmon-%{version}-py?.?.egg-info

%changelog
* Fri Feb 08 2019 Brian Bockelman <brian.bockelman@cern.ch> - 0.1-1
- Initial package version as uploaded to the Test PyPI instance.
