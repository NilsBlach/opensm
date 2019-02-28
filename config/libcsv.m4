
dnl libcsv.m4: an autoconf for OpenSM Vendor Selection option
dnl
dnl To use this macro, just do LIBCSV_SEL.
dnl the new configure option --enable-libcsv will be defined.
dnl The following variables are defined:
dnl LIBCSV_LDADD - LDADD additional libs for linking the vendor lib
AC_DEFUN([LIBCSV_SEL], [
# --- BEGIN LIBCSV_SEL ---

dnl Check if they want the libcsv support
AC_MSG_CHECKING([to enable libcsv support for parx routing])
AC_ARG_ENABLE(libcsv,
[  --enable-libcsv          Enable the libcsv support for parx routing (default yes)],
        [case $enableval in
        yes) libcsv_support=yes ;;
        no)  libcsv_support=no ;;
        esac],
        libcsv_support=yes)
AC_MSG_RESULT([$libcsv_support])

if test "x$libcsv_support" = "xyes"; then
   LIBCSV_LDADD="-lcsv"
fi

dnl Define a way for the user to provide the path to the libcsv includes
AC_ARG_WITH(libcsv-includes,
    AC_HELP_STRING([--with-libcsv-includes=<dir>],
                   [define the dir where libcsv includes are installed]),
AC_MSG_NOTICE(Using libcsv includes from:$with_libcsv_includes),
with_libcsv_includes="")

if test "x$with_libcsv_includes" != "x"; then
   LIBCSV_INCLUDES="-I$with_libcsv_includes"
fi

dnl Define a way for the user to provide the path to the libcsv libs
AC_ARG_WITH(libcsv-libs,
    AC_HELP_STRING([--with-libcsv-libs=<dir>],
                   [define the dir where libcsv libs are installed]),
AC_MSG_NOTICE(Using libcsv libs from:$with_libcsv_libs),
with_libcsv_libs="")

if test "x$with_libcsv_libs" != "x"; then
   LIBCSV_LDADD="-L$with_libcsv_libs $LIBCSV_LDADD"
fi

AC_SUBST(LIBCSV_LDADD)
AC_SUBST(LIBCSV_INCLUDES)

# --- END LIBCSV_SEL ---
]) dnl LIBCSV_SEL

dnl Check for the libcsv lib dependency
AC_DEFUN([LIBCSV_CHECK_LIB], [
# --- BEGIN LIBCSV_CHECK_LIB ---
if test "$libcsv_support" != "no"; then
   if test "$disable_libcheck" != "yes"; then
      sav_LDFLAGS=$LDFLAGS
      LDFLAGS="$LDFLAGS $LIBCSV_LDADD"
      AC_CHECK_LIB(csv, csv_parse,
            AC_DEFINE(ENABLE_LIBCSV_FOR_PARX,
                      1, [Define as 1 if you want to enable libcsv support for parx routing]),
	    AC_MSG_ERROR([csv_parse() not found.]))
      LDFLAGS=$sav_LDFLAGS
   else
      AC_DEFINE(ENABLE_LIBCSV_FOR_PARX,
                1, [Define as 1 if you want to enable libcsv support for parx routing])
   fi
fi
# --- END LIBCSV_CHECK_LIB ---
]) dnl LIBCSV_CHECK_LIB

dnl Check for the vendor lib dependency
AC_DEFUN([LIBCSV_CHECK_HEADER], [
# --- BEGIN LIBCSV_CHECK_HEADER ---

dnl we might be required to ignore this check
if test "$libcsv_support" != "no"; then
   if test "$disable_libcheck" != "yes"; then
      sav_CPPFLAGS=$CPPFLAGS
      CPPFLAGS="$CPPFLAGS $LIBCSV_INCLUDES"
      AC_CHECK_HEADERS(csv.h)
      CPPFLAGS=$sav_CPPFLAGS
   fi
fi
# --- END LIBCSV_CHECK_HEADER ---
]) dnl LIBCSV_CHECK_HEADER
