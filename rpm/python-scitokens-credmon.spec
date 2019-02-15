# Created by pyp2rpm-2.0.0
%global pypi_name scitokens-credmon

Name:           python-%{pypi_name}
Version:        0.2
Release:        1%{?dist}
Summary:        Scitokens credential monitor for use with HTCondor

License:        MIT
URL:            https://github.com/htcondor/scitokens-credmon
Source0:        https://test-files.pythonhosted.org/packages/09/17/ac47313b45b62691fa50a19311a60e3f16f9e6a20c7bdf7e41fe904cc2b2/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python2-devel
BuildRequires:  python-setuptools

%description
A HTCondor credentials monitor specific for OAuth2 and SciTokens workflows.

%package -n     python2-%{pypi_name}
Summary:        Scitokens credential monitor for use with HTCondor
%{?python_provide:%python_provide python2-%{pypi_name}}
 
Requires:       condor-python
Requires:       python-requests-oauthlib
Requires:       python-six
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


%files -n python2-%{pypi_name} 
%doc 
%{_bindir}/scitokens_credmon
%{_bindir}/scitokens_credential_producer
%{python2_sitelib}/credmon
%{python2_sitelib}/scitokens_credmon-%{version}-py?.?.egg-info
%attr(2770, root, condor) /var/lib/condor/credentials
%ghost /var/lib/condor/credentials/wsgi_session_key
/var/www/wsgi-scripts/%{pypi_name}/%{pypi_name}.wsgi
%config(noreplace) %{_sysconfdir}/condor/config.d/50-scitokens-credmon.conf
%config(noreplace) %{_sysconfdir}/httpd/conf.d/scitokens_credmon.conf

%changelog
* Fri Feb 08 2019 Brian Bockelman <brian.bockelman@cern.ch> - 0.2-1
- Include proper packaging and WSGI scripts for credmon.

* Fri Feb 08 2019 Brian Bockelman <brian.bockelman@cern.ch> - 0.1-1
- Initial package version as uploaded to the Test PyPI instance.
