# Created by pyp2rpm-2.0.0
%global pypi_name scitokens-credmon

Name:           python-%{pypi_name}
Version:        0.3
Release:        1%{?dist}
Summary:        SciTokens credential monitor for use with HTCondor

License:        MIT
URL:            https://github.com/htcondor/scitokens-credmon
Source0:        %{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python2-devel
BuildRequires:  python2-setuptools

%description
A HTCondor credentials monitor specific for OAuth2 and SciTokens workflows.

%package -n     python2-%{pypi_name}
Summary:        SciTokens credential monitor for use with HTCondor
%{?python_provide:%python_provide python2-%{pypi_name}}
 
Requires:       python2-condor
Requires:       python2-requests-oauthlib
Requires:       python2-six
Requires:       python-flask
Requires:       python2-cryptography
Requires:       python2-scitokens
Requires:       httpd
Requires:       mod_wsgi

%description -n python2-%{pypi_name}


%prep
%autosetup -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py2_build

%install
%py2_install
mkdir -p %{buildroot}/var/lib/condor/credentials
cp -a examples/config/README.credentials %{buildroot}/var/lib/condor/credentials


%files -n python2-%{pypi_name}
%doc 
%{_bindir}/scitokens_credmon
%{_bindir}/scitokens_credential_producer
%{python2_sitelib}/credmon
%{python2_sitelib}/scitokens_credmon-*.egg-info
%attr(2770, root, condor) /var/lib/condor/credentials
%ghost /var/lib/condor/credentials/wsgi_session_key
%ghost /var/lib/condor/credentials/CREDMON_COMPLETE
%ghost /var/lib/condor/credentials/pid
%ghost %{_sysconfdir}/httpd/conf.d/scitokens_credmon.conf

%changelog
* Thu May 02 2019 Jason Patton <jpatton@cs.wisc.edu> - 0.3-1
- Remove automatic install of config files. Put README in creddir.

* Fri Feb 08 2019 Brian Bockelman <brian.bockelman@cern.ch> - 0.2-1
- Include proper packaging and WSGI scripts for credmon.

* Fri Feb 08 2019 Brian Bockelman <brian.bockelman@cern.ch> - 0.1-1
- Initial package version as uploaded to the Test PyPI instance.
