%if 0%{?fedora}
%global with_python3 1
%else
%global with_python3 0
%endif

Name:           python-cct
Version:        0.2.0
Release:        0.1%{?dist}
Summary:        Container configuration tool
Group:          Development/Tools
License:        MIT
URL:            https://github.com/containers-tools/cct
Source0:        https://github.com/containers-tools/cct/archive/%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python-devel
BuildRequires:  python-setuptools
BuildRequires:  PyYAML
BuildRequires:  python-lxml
Requires:       python-setuptools
Requires:       python-lxml
Requires:       PyYAML

%description
containers configuration tool

%if 0%{?with_python3}
%package -n python3-cct
Summary:        Summary

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  PyYAML
BuildRequires:  python3-lxml
Requires:       python3-setuptools
Requires:       python3-lxml
Requires:       PyYAML

%description -n python3-cct

A tool for configuring containers.
%endif

%prep
%setup -qn python-cct-%{version}

%if 0%{?with_python3}
rm -rf %{py3dir}
cp -a . %{py3dir}
find %{py3dir} -name '*.py' | xargs sed -i '1s|^#!python|#!%{__python3}|'
%endif

find -name '*.py' | xargs sed -i '1s|^#!python|#!%{__python2}|'

%build
%{__python} setup.py build

%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py build
popd
%endif


%install
%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py install --skip-build --root %{buildroot}
popd
%endif

%{__python} setup.py install --skip-build --root %{buildroot}

%files
%doc README.md
%license LICENSE
%{_bindir}/cct
%dir %{python2_sitelib}/cct
%{python2_sitelib}/cct/*
%{python2_sitelib}/cct-%{version}-py2.*.egg-info

%if 0%{?with_python3}
%files -n python3-cct
%doc README.md
%license LICENSE
%{_bindir}/cct
%dir %{python3_sitelib}/cct
%{python3_sitelib}/cct/*
%{python3_sitelib}/cct-%{version}-py3.*.egg-info
%endif
