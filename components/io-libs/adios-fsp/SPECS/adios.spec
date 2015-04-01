#-fsp-header-comp-begin----------------------------------------------

%include %{_sourcedir}/FSP_macros

# FSP convention: the default assumes the gnu compiler family;
# however, this can be overridden by specifing the compiler_family
# variable via rpmbuild or other mechanisms.

%{!?compiler_family: %define compiler_family gnu}
%{!?mpi_family: %define mpi_family openmpi}
%{!?PROJ_DELIM:      %define PROJ_DELIM   %{nil}}

# Compiler dependencies
BuildRequires: lmod%{PROJ_DELIM}
%if %{compiler_family} == gnu
BuildRequires: gnu-compilers%{PROJ_DELIM}
Requires:      gnu-compilers%{PROJ_DELIM}
%endif
%if %{compiler_family} == intel
BuildRequires: gcc-c++ intel-compilers%{PROJ_DELIM}
Requires:      gcc-c++ intel-compilers%{PROJ_DELIM}
%if 0%{FSP_BUILD}
BuildRequires: intel_licenses
%endif
%endif

# MPI dependencies
%if %{mpi_family} == impi
BuildRequires: intel-mpi%{PROJ_DELIM}
Requires:      intel-mpi%{PROJ_DELIM}
%endif
%if %{mpi_family} == mvapich2
BuildRequires: mvapich2-%{compiler_family}%{PROJ_DELIM}
Requires:      mvapich2-%{compiler_family}%{PROJ_DELIM}
%endif
%if %{mpi_family} == openmpi
BuildRequires: openmpi-%{compiler_family}%{PROJ_DELIM}
Requires:      openmpi-%{compiler_family}%{PROJ_DELIM}
%endif

#-fsp-header-comp-end------------------------------------------------

%define somver 0
%define sover %somver.0.0

# Base package name
%define pname adios
%define PNAME %(echo %{pname} | tr [a-z] [A-Z])

Summary: The Adaptable IO System (ADIOS)
Name:    %{pname}-%{compiler_family}%{PROJ_DELIM}
Version: 1.8.0
Release: 1
License: BSD-3-Clause
Group:   fsp/io-libs
Url:     http://www.olcf.ornl.gov/center-projects/adios/
Source0: %{pname}-%{version}.tar.gz
Source1: FSP_macros
Source2: FSP_setup_compiler

# Minimum Build Requires
BuildRequires: mxml-devel cmake zlib-devel glib2-devel
BuildRequires: %{mpi_family}-devel

# libm.a from CMakeLists
BuildRequires: glibc-static

BuildRequires: phdf5-%{compiler_family}-%{mpi_family}%{PROJ_DELIM}
Requires:      phdf5-%{compiler_family}-%{mpi_family}%{PROJ_DELIM}

BuildRequires: netcdf-%{compiler_family}-%{mpi_family}%{PROJ_DELIM}
#BuildRequires: libmpe2-devel
#BuildRequires: python-modules-xml
BuildRequires: python-devel
#BuildRequires: bzlib-devel
#BuildRequires: libsz2-devel
# This is the legacy name for lustre-lite
# BuildRequires: liblustre-devel
BuildRequires: lustre-lite
BuildRequires: python-numpy-%{compiler_family}%{PROJ_DELIM}

# define fdupes, clean up rpmlint errors
BuildRequires: fdupes

###############################################################
# Disable until we get the numpy headers
#Requires: python-module-%pname = %version-%release

# Default library install path
%define install_path %{FSP_LIBS}/%{compiler_family}/%{mpi_family}/%{pname}/%version

%description
The Adaptable IO System (ADIOS) provides a simple, flexible way for
scientists to desribe the data in their code that may need to be
written, read, or processed outside of the running simulation. By
providing an external to the code XML file describing the various
elements, their types, and how you wish to process them this run, the
routines in the host code (either Fortran or C) can transparently change
how they process the data.

%package -n python-module-%pname
Summary: Python module of the Adaptable IO System (ADIOS)
Group: Development/Python

%description -n python-module-%pname
The Adaptable IO System (ADIOS) provides a simple, flexible way for
scientists to desribe the data in their code that may need to be
written, read, or processed outside of the running simulation. By
providing an external to the code XML file describing the various
elements, their types, and how you wish to process them this run, the
routines in the host code (either Fortran or C) can transparently change
how they process the data.

This package contains python module of ADIOS.

%prep
%setup -q -n %{pname}-%{version}

sed -i 's|@BUILDROOT@|%buildroot|' wrappers/numpy/setup*
%ifarch x86_64
LIBSUFF=64
%endif
sed -i "s|@64@|$LIBSUFF|" wrappers/numpy/setup*

%build
# FSP compiler/mpi designation
export FSP_COMPILER_FAMILY=%{compiler_family}
export FSP_MPI_FAMILY=%{mpi_family}
. %{_sourcedir}/FSP_setup_compiler
. %{_sourcedir}/FSP_setup_mpi
%if %{compiler_family} == intel
export CFLAGS="-fp-model strict $CFLAGS"
%endif

module load phdf5
module load netcdf

TOPDIR=$PWD

export CFLAGS="-fPIC -I$TOPDIR/src/public -I$MPI_DIR/include -I$NETCDF_INC -I$HDF5_INC -lpthread -L$NETCDF_LIB -lnetcdf -L$HDF5_LIB" 

export CC=mpicc
export CXX=mpicxx
export F77=mpif77
export FC=mpif90
export MPICC=mpicc
export MPIFC=mpif90
export MPICXX=mpicxx

%if %{compiler_family} == intel
export CFLAGS="-fp-model strict $CFLAGS"
%endif
./configure --prefix=%{install_path} \
	--with-mxml=/usr/include \
	--with-lustre=/usr/include/lustre \
	--with-phdf5="$HDF5_DIR" \
	--with-zlib=/usr/include \
	--with-netcdf="$NETCDF_DIR"
make VERBOSE=1

%install
# FSP compiler designation
export FSP_COMPILER_FAMILY=%{compiler_family}
export FSP_MPI_FAMILY=%{mpi_family}
. %{_sourcedir}/FSP_setup_compiler
. %{_sourcedir}/FSP_setup_mpi

make DESTDIR=$RPM_BUILD_ROOT install

module load numpy
module load mkl

chmod +x adios_config
export PATH=$(pwd):$PATH

export CFLAGS="-I%buildroot%{install_path}/include -I$PYTHONPATH/numpy/core/include -I$(pwd)/src/public -L%buildroot%{install_path}/lib"
pushd wrappers/numpy
make MPI=y python
python setup.py install --prefix=%buildroot$PYTHONPATH
popd

install -m644 utils/skel/lib/skel_suite.py \
	utils/skel/lib/skel_template.py \
	utils/skel/lib/skel_test_plan.py \
	%buildroot$PYTHONPATH

rm -f $(find examples -name '*.o') \
	examples/staging/stage_write/writer_adios
rm -f $(find examples -type f -name .gitignore)
rm -rf $(find examples -type d -name ".lib")
chmod 644 $(find examples -type f -name "*.xml")

install -d %buildroot%{install_path}/lib
cp -fR examples %buildroot%{install_path}/lib
%fdupes -s %buildroot%{install_path}/lib/examples

# install -d %buildroot%python_sitelibdir
mv %buildroot%{install_path}/lib/python/*.py %buildroot$PYTHONPATH

# FSP module file
# compiler_family doesn't get expanded, but FSP_COMPILER_FAMILY does...
echo $FSP_COMPILER_FAMILY
%{__mkdir} -p %{buildroot}%{FSP_MODULEDEPS}/$FSP_COMPILER_FAMILY/%{pname}
%{__cat} << EOF > %{buildroot}/%{FSP_MODULEDEPS}/$FSP_COMPILER_FAMILY/%{pname}/%{version}
#%Module1.0#####################################################################

proc ModulesHelp { } {

puts stderr " "
puts stderr "This module loads the %{PNAME} library built with the $FSP_COMPILER_FAMILY compiler toolchain."
puts stderr "\nVersion %{version}\n"

}
module-whatis "Name: %{PNAME} built with $FSP_COMPILER_FAMILY toolchain"
module-whatis "Version: %{version}"
module-whatis "Category: runtime library"
module-whatis "Description: %{summary}"
module-whatis "%{url}"

set             version             %{version}

prepend-path    PATH                %{install_path}/bin
prepend-path    MANPATH             %{install_path}/share/man
prepend-path    INCLUDE             %{install_path}/include
prepend-path    LD_LIBRARY_PATH     %{install_path}/lib

setenv          %{PNAME}_DIR        %{install_path}
setenv          %{PNAME}_LIB        %{install_path}/lib
setenv          %{PNAME}_INC        %{install_path}/include

EOF

%{__cat} << EOF > %{buildroot}/%{FSP_MODULEDEPS}/$FSP_COMPILER_FAMILY/%{pname}/.version.%{version}
#%Module1.0#####################################################################
##
## version file for %{pname}-%{version}
##
set     ModulesVersion      "%{version}"
EOF

pushd /home/abuild/rpmbuild/
find
echo -e '\n\n'
popd

%files
%defattr(-,root,root,-)
%doc AUTHORS COPYING ChangeLog KNOWN_BUGS NEWS README TODO
#%exclude %{install_path}/lib/examples
%{FSP_HOME}

#%files -n python-module-%pname
#%python_sitelibdir/*
#%exclude %python_sitelibdir/argparse.py*

#%files examples
#%{install_path}/lib/examples


%changelog
