local home    = os.getenv("HOME")
local version = myModuleVersion()
local pkgName = myModuleName()
local pkg     = pathJoin(home,"local","modules",pkgName,version)
local pkgbin  = pathJoin(home,"local","modules",pkgName,version,"bin")
local pkglib  = pathJoin(home,"local","modules",pkgName,version,"lib64")
setenv("GMSH_ROOT", pkg)
prepend_path("PATH", pkgbin)
prepend_path("LD_LIBRARY_PATH", pkglib)
prepend_path("PYTHONPATH", pkglib)
