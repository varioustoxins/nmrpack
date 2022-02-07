#!/usr/bin/env bash

#
# this file was built with cog: https://nedbatchelder.com/code/cog/
#
# to find the main installer search for: start of file - installer_base_osx.sh
#

##[[[cog
##  import cog
##
##  for file in ['color.sh', 'output.sh', 'installer_base_osx.sh']:
##      with open(file, 'r') as fh:
##           cog.outl()
##           cog.outl(f'# start of file - {file}')
##           cog.outl('#')
##           for line in fh:
##                cog.out(line)
##           cog.outl()
##           cog.outl('#')
##           cog.outl(f'# end of file - {file}')
##]]]

# start of file - color.sh
#
#!/usr/bin/env bash
#———————————————————————————————————————————————————————————————————————————————
# © 2016 — 2017 Author: Konstantin Gredeskoul
# Ported from the licensed under the MIT license Project Pullulant, at
# https://github.com/kigster/pullulant
#
# Any modifications, © 2017 PioneerWorks, Inc. All rights reserved.
#———————————————————————————————————————————————————————————————————————————————

lib::color::enable() {
  if [[ -z "${HomebaseColorsLoaded}" ]]; then

    export txtblk='\e[0;30m' # Black - Regular
    export txtred='\e[0;31m' # Red
    export txtgrn='\e[0;32m' # Green
    export txtylw='\e[0;33m' # Yellow
    export txtblu='\e[0;34m' # Blue
    export txtpur='\e[0;35m' # Purple
    export txtcyn='\e[0;36m' # Cyan
    export txtwht='\e[0;37m' # White

    export bldblk='\e[1;30m' # Black - Bold
    export bldred='\e[1;31m' # Red
    export bldgrn='\e[1;32m' # Green
    export bldylw='\e[1;33m' # Yellow
    export bldblu='\e[1;34m' # Blue
    export bldpur='\e[1;35m' # Purple
    export bldcyn='\e[1;36m' # Cyan
    export bldwht='\e[1;37m' # White

    export unkblk='\e[4;30m' # Black - Underline
    export undred='\e[4;31m' # Red
    export undgrn='\e[4;32m' # Green
    export undylw='\e[4;33m' # Yellow
    export undblu='\e[4;34m' # Blue
    export undpur='\e[4;35m' # Purple
    export undcyn='\e[4;36m' # Cyan
    export undwht='\e[4;37m' # White

    export bakblk='\e[40m'   # Black - Background
    export bakred='\e[41m'   # Red
    export bakgrn='\e[42m'   # Green
    export bakylw='\e[43m'   # Yellow
    export bakblu='\e[44m'   # Blue
    export bakpur='\e[45m'   # Purple
    export bakcyn='\e[46m'   # Cyan
    export bakwht='\e[47m'   # White

    export txtrst='\e[0m'    # Text Reset
    export clr='\e[0m'       # Text Reset
    export rst='\e[0m'       # Text Reset

    export bold='\e[1m'
    export italic='\e[3m'
    export underlined='\e[4m'
    export strikethrough='\e[9m'

    export HomebaseColorsLoaded=1
  else
    [[ -n ${DEBUG} ]] && echo "colors already loaded..."
  fi
}

error-text()    { printf "${txtred}"; }
bold()          { ansi 1 "$@"; }
italic()        { ansi 3 "$@"; }
underline()     { ansi 4 "$@"; }
strikethrough() { ansi 9 "$@"; }
red()           { ansi 31 "$@"; }
ansi()          { echo -e "\e[${1}m${*:2}\e[0m"; }

lib::color::disable() {
    unset txtblk
    unset txtred
    unset txtgrn
    unset txtylw
    unset txtblu
    unset txtpur
    unset txtcyn
    unset txtwht

    unset bldblk
    unset bldred
    unset bldgrn
    unset bldylw
    unset bldblu
    unset bldpur
    unset bldcyn
    unset bldwht

    unset unkblk
    unset undred
    unset undgrn
    unset undylw
    unset undblu
    unset undpur
    unset undcyn
    unset undwht

    unset bakblk
    unset bakred
    unset bakgrn
    unset bakylw
    unset bakblu
    unset bakpur
    unset bakcyn
    unset bakwht

    unset txtrst
    unset clr

    unset italic
    unset bold
    unset strikethrough
    unset underlined

    unset HomebaseColorsLoaded
}

(( ${HomebaseColorsLoaded} )) || lib::color::enable

#
# end of file - color.sh

# start of file - output.sh
#
#!/usr/bin/env bash
# Private functions
__lib::output::cursor-right-by()  {
  lib::output::is_terminal && printf "\e[${1}C"
}

__lib::output::cursor-left-by()  {
  lib::output::is_terminal && printf "\e[${1}D"
}

__lib::output::cursor-up-by()  {
  lib::output::is_terminal && printf "\e[${1}A"
}

__lib::output::cursor-down-by()  {
  lib::output::is_terminal && printf "\e[${1}B"
}

__lib::output::cursor-move-to-y() {
  lib::output::is_terminal || return
  __lib::output::cursor-up-by 1000
  __lib::output::cursor-down-by ${1:-0}
}

__lib::output::cursor-move-to-x() {
  lib::output::is_terminal || return
  __lib::output::cursor-left-by 1000
  __lib::output::cursor-right-by ${1:-0}
}

cursor.rewind() {
  local x=${1:-0}
  __lib::output::cursor-move-to-x ${x}
}

__lib::ver-to-i() {
  version=${1}
  echo ${version} | awk 'BEGIN{FS="."}{ printf "1%02d%03.3d%03.3d", $1, $2, $3}'
}

lib::output::color::on() {
  printf "${bldred}" >&2
  printf "${bldblu}" >&1
}

lib::output::color::off() {
  reset-color: >&2
  reset-color: >&1
}

__lib::output::screen-width() {
  if [[ -n "${HomebaseCurrentScreenWidth}" && $(( $(millis) - ${HomebaseCurrentScreenMillis} )) -lt 20000 ]]; then
    printf -- "${HomebaseCurrentScreenWidth}"
    return
  fi

  if [[ ${HomebaseCurrentOS:-$(uname -s)} == 'Darwin' ]]; then
    w=$(stty -a | grep columns | awk '{print $6}')
  elif [[ ${HomebaseCurrentOS} == 'Linux' ]]; then
    w=$(stty -a | grep columns | awk '{print $7}' | hbsed 's/;//g')
  fi

  MIN_WIDTH=${MIN_WIDTH:-80}
  w=${w:-${MIN_WIDTH}}
  [[ "${w}" -lt "${MIN_WIDTH}" ]] && w=${MIN_WIDTH}

  #export HomebaseCurrentScreenWidth=${w}
  #export HomebaseCurrentScreenMillis=$(millis)

  printf -- "${w}"
}

__lib::output::screen-height() {
  if [[ ${HomebaseCurrentOS:-$(uname -s)} == 'Darwin' ]]; then
    h=$(stty -a | grep rows | awk '{print $4}')
  elif [[ ${HomebaseCurrentOS} == 'Linux' ]]; then
    h=$(stty -a | grep rows | awk '{print $5}' | hbsed 's/;//g')
  fi

  MIN_HEIGHT=${MIN_HEIGHT:-30}
  h=${h:-${MIN_HEIGHT}}
  [[ "${h}" -lt "${MIN_HEIGHT}" ]] && h=${MIN_HEIGHT}
  printf -- $(( $h - 2 ))
}

__lib::output::line() {
  __lib::output::repeat-char "─" $(( $(__lib::output::screen-width) - 2 ))
}

__lib::output::hr()  {
  local cols=${1:-$(__lib::output::screen-width)}
  local char=${2:-"—"}
  local color=${3:-${txtylw}}

  printf "${color}"
  __lib::output::repeat-char "─"
  reset-color
}

__lib::output::sep() {
  __lib::output::hr
  printf "\n"
}

__lib::output::repeat-char() {
  local char="${1}"
  local width=${2}
  [[ -z "${width}" ]] && width=$(__lib::output::screen-width)
  local line=""
  for i in {1..300}; do
    [[ $i -gt ${width} ]] && {
      printf -- "${line}"
      return
    }
    line="${line}${char}"
  done
  printf -- "${line}"
}

# set background color to something before calling this
__lib::output::bar() {
  __lib::output::repeat-char " "
  reset-color
}

__lib::output::box-separator() {
  printf "├"
  __lib::output::line
  __lib::output::cursor-left-by 1
  printf "┤${clr}\n"
}

__lib::output::box-top() {
  printf "┌"
  __lib::output::line
  __lib::output::cursor-left-by 1
  printf "┐${clr}\n"
}

__lib::output::box-bottom() {
  printf "└"
  __lib::output::line
  __lib::output::cursor-left-by 1
  printf "┘${clr}\n"
}

__lib::output::which-ruby() {
  if [[ -x /usr/bin/ruby ]]; then
    printf /usr/bin/ruby
  elif [[ -x /usr/local/bin/ruby ]] ; then
    printf /usr/local/bin/ruby
  else
    which ruby
  fi
}

__lib::output::clean() {
  local text="$*"
  $(__lib::output::which-ruby) -e "input=\"${text}\"; " -e 'puts input.gsub(/\e\[[;m\d]+/, "")'
}

__lib::output::boxed-text() {
  local border_color=${1}
  shift
  local text_color=${1}
  shift
  local text="$*"

  [[ lib::output::is_terminal ]] || {
    printf ">>> %80.80s <<< \n" ${text}
    return
  }

  local clean_text=$(__lib::output::clean "${text}")
  local width=$(( $(__lib::output::screen-width) - 2 ))
  local remaining_space_len=$(($width - ${#clean_text} - 1))
  printf "${border_color}│ ${text_color}"
  printf -- "${text}"
  [[ ${remaining_space_len} -gt 0 ]] && __lib::output::repeat-char " " "${remaining_space_len}"
  __lib::output::cursor-left-by 1
  printf "${border_color}│${clr}\n"
}

#
# Usage: __lib::output::box border-color text-color "line 1" "line 2" ....
#
__lib::output::box() {
  local border_color=${1}
  shift
  local text_color=${1}
  shift
  local line

  [[ lib::output::is_terminal ]] || {
    for line in "$@"; do
      printf ">>> %80.80s <<< \n" ${line}
    done
    return
  }

  [[ -n "${opts_suppress_headers}" ]] && return

  printf "\n${border_color}"
  __lib::output::box-top

  local __i=0
  for line in "$@"; do
    [[ $__i == 1 ]] && {
      printf "${border_color}"
      __lib::output::box-separator
    }
    __lib::output::boxed-text "${border_color}" "${text_color}" "${line}"
    __i=$(( $__i + 1 ))
  done

  printf "${border_color}"
  __lib::output::box-bottom
  reset-color:
}

__lib::output::center() {
  local color="${1}"
  shift
  local text="$*"

  local clean_text=$(__lib::output::clean "${text}")
  local width=$(( $(__lib::output::screen-width) - 2 ))
  local remaining_space_len=$(( 1 + ($width - ${#clean_text}) / 2 ))

  local offset=0
  [[ $(( ( ${width} - ${#clean_text} ) % 2 )) == 1 ]] && offset=1

  printf "${color}"
  cursor.at.x -1
  __lib::output::repeat-char " " ${remaining_space_len}
  printf "%s" "${text}"
  __lib::output::repeat-char " " $(( ${remaining_space_len} + ${offset} ))
  reset-color
  cursor.at.x -1
}

__lib::output::left-justify() {
  local color="${1}"
  shift
  local text="$*"
  echo
  printf "${color}"
  ( lib::output::is_terminal ) && {
    local width=$(( 2 * $(__lib::output::screen-width) / 3 ))
    [[ ${width} -lt 70 ]] && width="70"
    printf -- "  %-${width}.${width}s${clr}\n\n" "« ${text} »"
  }

  ( lib::output::is_terminal ) || {
    printf -- "  « ${text} »"
    printf -- "  ${clr}\n\n"
  }
}

################################################################################
# Public functions
################################################################################

# Prints text centered on the screen
# Usage: center "colors/prefix" "text"
#    eg: center "${bakred}${txtwht}" "Welcome Friends!"
center() {
  __lib::output::center "$@"
}

left() {
  __lib::output::left-justify "$@"
}

cursor.at.x() {
  __lib::output::cursor-move-to-x "$@"
}

cursor.at.y() {
  __lib::output::cursor-move-to-y "$@"
}

screen.width() {
  __lib::output::screen-width
}

screen.height() {
  __lib::output::screen-height
}

lib::output::is_terminal() {
  lib::output::is_tty || lib::output::is_redirect || lib::output::is_pipe
}

lib::output::is_ssh() {
  [[ -n "${SSH_CLIENT}" || -n "${SSH_CONNECTION}" ]]
}

lib::output::is_tty() {
  [[ -t 1 ]]
}

lib::output::is_pipe() {
  [[ -p /dev/stdout ]]
}

lib::output::is_redirect() {
  [[ ! -t 1 && ! -p /dev/stdout ]]
}

box::yellow-in-red() {
  __lib::output::box "${bldred}" "${bldylw}" "$@"
}

box::yellow-in-yellow() {
  __lib::output::box "${bldylw}" "${txtylw}" "$@"
}

box::blue-in-yellow() {
  __lib::output::box "${bldylw}" "${bldblu}" "$@"
}

box::blue-in-green() {
  __lib::output::box "${bldblu}" "${bldgrn}" "$@"
}

box::yellow-in-blue() {
  __lib::output::box "${bldylw}" "${bldblu}" "$@"
}

box::red-in-yellow() {
  __lib::output::box "${bldred}" "${bldylw}" "$@"
}

box::red-in-red() {
  __lib::output::box "${bldred}" "${txtred}" "$@"
}

box::green-in-magenta() {
  __lib::output::box "${bldgrn}" "${bldpur}" "$@"
}

box::red-in-magenta() {
  __lib::output::box "${bldred}" "${bldpur}" "$@"
}

box::green-in-green() {
  __lib::output::box "${bldgrn}" "${bldgrn}" "$@"
}

box::magenta-in-green() {
  __lib::output::box "${bldpur}" "${bldgrn}" "$@"
}

box::magenta-in-blue() {
  __lib::output::box "${bldblu}" "${bldpur}" "$@"
}

hl::blue() {
  left "${bldwht}${bakpur}" "$@"
}

hl::green() {
  left "${txtblk}${bakgrn}" "$@"
}

hl::yellow() {
  left "${txtblk}${bakylw}" "$@"
}

hl::subtle() {
  left "${bldcyn}${bakblk}${underlined}" "$@"
}

hl::desc() {
  left "${txtblk}${bakylw}" "$@"
}

h::yellow() {
  center "${txtblk}${bakylw}" "$@"
}

h::red() {
  center "${txtwht}${bakred}" "$@"
}

h::green() {
  center "${txtblk}${bakgrn}" "$@"
}

h::blue() {
  center "${txtblk}${bakblu}" "$@"
}

h::black() {
  center "${bldylw}${bakblk}" "$@"
}

h1::green() {
  box::green-in-magenta "$@"
}

h1::purple() {
  box::magenta-in-green "$@"
}

h1::blue() {
  box::magenta-in-blue "$@"
}

h1::red() {
  box::red-in-red "$@"
}

h1::yellow() {
  box::yellow-in-red "$@"
}

h1() {
  box::blue-in-yellow "$@"
}

h2() {
  box::blue-in-green "$@"
}

h3() {
  hl::subtle "$@"
}

hdr() {
  h1 "$@"
}

hr::colored() {
  local color=${1:-"red"}
  __lib::output::hr $(__lib::output::screen-width) "—" ${color}
}

function hr() {
  [[ -z "$*" ]] || printf $*
  __lib::output::hr
}

stdout() {
  local file=$1
  printf "\n${txtgrn}"
  [[ -s ${file} ]] && cat ${file}
  [[ -n ${file} ]] && reset-color
}

stderr() {
  local file=$1
  printf "\n${txtred}"
  [[ -s ${file} ]] && cat ${file}
  [[ -n ${file} ]] && reset-color
}

duration() {
  local millis=$1
  [[ -n $(which bc) ]] || return
  if [[ -n $millis && $millis -gt 0 ]] ; then
    cursor.at.x 3
    printf "${bldblu}%4.1fs " $(echo "scale=1;${millis}/1000" | bc)
  fi
}

ok() {
  __lib::output::cursor-left-by 1000
  printf " ${bldgrn}✔︎ ${clr}"
}

not_ok() {
  __lib::output::cursor-left-by 1000
  printf " ${bldred}✘ ${clr}"
}

kind_of_ok() {
  __lib::output::cursor-left-by 1000
  printf " ${bldylw}⚠ ${clr}"
}

ok:() {
  ok $@
  echo
}

not_ok:() {
  not_ok $@
  echo
}

kind_of_ok:() {
  kind_of_ok $@
  echo
}

puts() {
  printf "  ⇨ ${txtwht}$*${clr}"
}

okay() {
  header=$(printf -- "${bakgrn}${bldwht} « OKAY » ${clr}")
  box::green-in-green "${header}   ${bldgrn}$@" >&2
}

success() {
  printf -- "    ${bakgrn}${bldylw}  « SUCCESS »  ${clr} ${bldgrn}$*${clr}" >&2
  echo
}

err() {
  printf -- "    ${bldylw}${bakred}  « ERROR »  ${clr} ${bldred}$*${clr}" >&2
}

inf() {
  printf -- "    ${txtblu}${clr}${txtblu}$*${clr}"
}

warn() {
  printf -- "    ${bldwht}${bakylw} « WARNING » ${clr} ${bldylw}$*${clr}" >&2
}

warning() {
  header=$(printf -- "${txtblk}${bakylw} « WARNING » ${clr}")
  box::yellow-in-yellow "${header} ${bldylw}$*" >&2
}

br() {
  echo
}

debug() {
  if [[ -n ${DEBUG} ]]; then
    info $@ 1>&2
  fi
}

info() {
  inf $@
  echo
}

error() {
  header=$(printf -- "${txtblk}${bakred} « ERROR » ${clr}")
  box::red-in-red "${header} ${bldylw}$@" >&2
}

info:() {
  inf $*
  ok:
}

error:() {
  err $*
  not_ok:
}

warning:() {
  warn $*
  kind_of_ok:
}

shutdown() {
  local message=${1:-"Shutting down..."}
  echo
  box::red-in-red "${message}"
  echo
  exit 1
}

reset-color() {
  printf "${clr}\n"
}

reset-color:() {
  printf "${clr}"
}

#
# end of file - output.sh

# start of file - installer_base_osx.sh
#
#!/usr/bin/env bash


# LibBash
source color.sh
source output.sh

LOG_FILE="/tmp/nmpack-installer-log-`date +%F-%T`.txt"

default_spack_path=${HOME}/programs/spack


h1   "NMRPack Installer V1"
info
info "note: on error check the log file $LOG_FILE"
info
hl::green   "Checking installed software"


XCS=$(xcode-select -p 2> /dev/null)
XCS_OK=$?

if [ "$XCS_OK" == "0" ] ; then
  inf "xcode tools:       ${XCS}"
  ok:
else
  inf  "xcode tools:       missing"
  not_ok:
fi

SPACK=$(which spack)
SPACK_OK=$?

if [ "$SPACK" != "" ] ; then
  grep 'the real spack script is here' $SPACK 2>&1 > /dev/null
  SPACK_IS_FUNCTION=$?
else
  SPACK_IS_FUNCTION=1
fi

if [ "$SPACK" != "" ] && [ "$SPACK_IS_FUNCTION" == "0" ] ; then
  SPACK=$( grep 'the real spack script is here' $SPACK | awk '{print NF}' )
fi
SPACK=${SPACK%/*}
SPACK=${SPACK%/*}

if [ "$SPACK_OK" != "0" ] ; then
  if [ -f "/tmp/nmrpack_spack_install_receipt" ] ; then
    SPACK=$(cat /tmp/nmrpack_spack_install_receipt)
    if [ -f ${SPACK}/bin/spack ] ; then
      SPACK_OK=0
    fi
  fi
fi

if [ "$SPACK_OK" != "0" ] ; then
  if [ -f ${default_spack_path}/bin/spack ] ; then
    SPACK=$default_spack_path
    SPACK_OK=0
  fi
fi

if [ "$SPACK_OK" == "0" ] ; then
  inf "spack:             ${SPACK}"
  ok:
else
  inf  "spack:             missing"
  not_ok:
fi

if [ "$SPACK_OK" == "0" ] ; then
  SPACK_EXE=${SPACK}/bin/spack
fi

NMRPACK_OK=1
if [ "$SPACK_OK" == "0" ] ; then
  NMRPACK=$($SPACK_EXE repo list | grep nmrpack)
  NMRPACK_OK=$?
  if [ "$NMRPACK_OK" == "0" ] ; then
    NMRPACK=$( echo $NMRPACK | awk '{print $2}' )
  else
    NMRPACK='missing'
  fi
fi

if [ "$NMRPACK_OK" == "0" ] ; then
  inf "nmrpack:           ${NMRPACK}"
  ok:
else
  inf "nmrpack:           missing"
  not_ok:
fi

BZIP2=$(which bzip2)
BZIP2_OK=$?
if [ "$BZIP2_OK" == "0" ] ; then
  inf "bzip2:             ${BZIP2}"
  ok:
else
  inf  "bzip2:             missing (unexpected comes with os)"
  not_ok:
fi

XZ=$(which xz)
XZ_OK=$?

if [ "$SPACK_OK" == 0 ] && [ $XZ_OK != 0 ]; then
  $SPACK_EXE find xz 2>&1 > /dev/null ; XZ_OK=$?
  if [ "$XZ_OK" == "0" ]  ; then
    XZ='spack find -p xz | awk '\''FNR==2 {printf ("%%s/bin/xz\\n",$2)}'\'
  fi
fi

if [ "$XZ_OK" == "0" ] ; then
  inf "xz:                ${XZ}"
  ok:
else
  inf  "xz:                missing"
  not_ok:
fi

ZSTD=$(which zstd)
ZSTD_OK=$?

if [ "$SPACK_OK" == 0 ] && [ $ZSTD_OK != 0 ]; then
  $SPACK_EXE find zstd 2>&1 > /dev/null ; ZSTD_OK=$?
  if [ "$ZSTD_OK" == "0" ]  ; then
    ZSTD='spack find -p zstd | awk '\''FNR==2 {printf ("%%s/lib\\n",$2)}'\'
  fi
fi

if [ "$ZSTD_OK" == "0" ] ; then
  inf "zstd:              ${ZSTD}"
  ok:
else
  inf  "zstd:              missing"
  not_ok:
fi

GNUPG2=$(which gpg)
GNUPG2_OK=$?

if [ "$SPACK_OK" == 0 ] && [ $GNUPG2_OK != 0 ]; then
  $SPACK_EXE find gnupg 2>&1 > /dev/null ; GNUPG2_OK=$?
  if [ "$GNUPG2_OK" == "0" ]  ; then
    GNUPG2='spack find -p gnupg | awk '\''FNR==2 {printf ("%%s/bin/gnupg\\n",$2)}'\'
  fi
fi


if [ "$GNUPG2_OK" == "0" ] ; then
  inf "gnupg2:            ${GNUPG2}"
  ok:
else
  inf  "gnupg2:            missing"
  not_ok:
fi

SVN=$(which svn)
SVN_OK=$?
if [ "$SVN_OK" == "0" ] ; then
  inf "svn:               ${SVN}"
  ok:
else
  inf  "svn:               missing (unexpected comes with os)"
  not_ok:
fi

HG=$(which hg)
HG_OK=$?


if [ "$SPACK_OK" == 0 ] && [ $HG_OK != 0 ]; then
  $SPACK_EXE find mercurial 2>&1 > /dev/null ; HG_OK=$?
  if [ "$HG_OK" == "0" ]  ; then
    HG='spack find -p mercurial | awk '\''FNR==2 {printf ("%%s/bin/hg\\n",$2)}'\'
  fi
fi


if [ "$HG_OK" == "0" ] ; then
  inf "hg:                ${HG}"
  ok:
else
  inf "hg:                missing"
  not_ok:
fi

GFORTRAN=$(which gfortran)
GFORTRAN_OK=$?

if [ "$SPACK_OK" == 0 ] && [ $GFORTRAN_OK != 0 ]; then
  $SPACK_EXE find gcc 2>&1 > /dev/null ; GFORTRAN_OK=$?
  if [ $GFORTRAN_OK == 0 ]  ; then
    GFORTRAN_SPACK=1
    GFORTRAN='spack find -p gcc | awk '\''FNR==2 {printf ("%%s/bin/gfortran\\n",$2)}'\'
  else
    GFORTRAN_SPACK=0
  fi
else
  GFORTRAN_SPACK=0
fi

if [ "$GFORTRAN_OK" == "0" ] ; then
  inf "gfortran:          ${GFORTRAN}"
  ok:
else
  inf "gfortran:          missing"
  not_ok:
fi

shell=$(echo $SHELL  | tr '/' ' '  | awk '{print $NF}')

SHELL_OK=0
SHELL_RC_FILE="unknown"
case $shell in
    zsh)
      grep "nmrpack initialise spack" ${HOME}/.zshenv > /dev/null
      SHELL_OK=$?
      SHELL_RC_FILE=.zshenv
    ;;
    bash)
      for run_command_file in ".bash_profile" ".bash_login" ".profile" ; do
        if [ -f  ${HOME}/${run_command_file} ] ; then
          grep "nmrpack initialise spack" ${HOME}/${run_command_file} > /dev/null
          SHELL_OK=$?
          if [ "$SHELL_OK"  ==  "0" ] ; then
            SHELL_RC_FILE=$run_command_file
            break
          fi
        fi
      done
    ;;
    *)
      SHELL_OK=1
    ;;
esac

if [ "$SHELL_OK" == "0" ] ; then
  inf "shell support:     installed in $SHELL_RC_FILE for shell $shell"
  ok:
else
  inf "shell support:     missing for $shell"
  not_ok:
fi

SPACK_LOAD_BASE_OK=0
if [ ! -f ${HOME}/.nmrpack/spack_preload.sh ]  ; then
  SPACK_LOAD_BASE_OK=1
fi

if [ "$SPACK_LOAD_BASE_OK" == "0" ] ; then
  if [ -f ${HOME}/.nmrpack/spack_preload.sh ] ; then
    grep "do not edit this file it is maintained by the nmrpack installer" ${HOME}/.nmrpack/spack_preload.sh > /dev/null
    SPACK_LOAD_BASE_OK=$?
  fi
fi

if [ "$SPACK_LOAD_BASE_OK" == "0" ] ; then
  inf "package support:   installed in ${HOME}/.nmrpack/spack_preload.sh"
  ok:
else
  inf "package support:   missing "
  not_ok:
fi

XZ_signature=xz
ZSTD_signature=zstd
GNUPG2_signature=gnupg
HG_signature=mercurial
GFORTRAN_signature=gcc

SPACK_LOAD_DEPENDENCIES_OK=0
SPACK_LOAD_COMMANDS=( "# !NOTE! do not edit this file it is maintained by the nmrpack installer" )
MISSING_LOAD=""
OK_LOAD=""
for package_name in XZ ZSTD GNUPG2 HG GFORTRAN ; do
  package_value="${!package_name}"

  ! echo $package_value | head -n1 | awk '{print $1;}'| grep spack > /dev/null
  package_needs_load=$?
  signature_key=${package_name}_signature
  signature=$(eval "echo \$$signature_key")

  if [ -f  ${HOME}/.nmrpack/spack_preload.sh ] ; then
    ! grep $signature ${HOME}/.nmrpack/spack_preload.sh > /dev/null
    package_in_prerun=$?
  else
    package_in_prerun=0
  fi

  if [ "$package_needs_load" == "1" ]  && [ "$package_in_prerun" == "0" ] ; then
    SPACK_LOAD_DEPENDENCIES_OK=$(( $SPACK_LOAD_DEPENDENCIES_OK + 1 ))
    SPACK_LOAD_COMMANDS+=("spackload $signature")
    MISSING_LOAD="$MISSING_LOAD $signature"
  else
    if [ "$package_needs_load" == "1" ] ; then
      OK_LOAD="$OK_LOAD $signature"
    fi
  fi

done

SPACK_LOAD_COMMANDS=$( IFS=$'\n'; echo "${SPACK_LOAD_COMMANDS[*]}" )

if [ "$SPACK_LOAD_DEPENDENCIES_OK" == "0" ] ; then
  inf "load packages:     installed:$OK_LOAD"
  ok:
else
  inf "load packages:     missing for:$MISSING_LOAD"
  not_ok:
fi

GFORTRAN_SUPPORT_OK=0
if [ -f  ${HOME}/.spack/darwin/compilers.yaml ] ; then
    ! grep "f77: null" ${HOME}/.spack/darwin/compilers.yaml > /dev/null
    GFORTRAN_SUPPORT_OK=$(( $GFORTRAN_SUPPORT_OK + $?))
    ! grep "fc: null" ${HOME}/.spack/darwin/compilers.yaml > /dev/null
    GFORTRAN_SUPPORT_OK=$(( $GFORTRAN_SUPPORT_OK + $?))
else
    GFORTRAN_SUPPORT_OK=1
fi

if [ "$GFORTRAN_SUPPORT_OK" == "0" ] ; then
  inf "gfortran support:  installed in ${HOME}/.spack/darwin/compilers.yaml"
  ok:
else
  inf "gfortran support:  missing in ${HOME}/.spack/darwin/compilers.yaml"
  not_ok:
fi


MISSING=$(( $BZIP2_OK + $XZ_OK + $ZSTD_OK + $GNUPG2_OK + $SVN_OK + $HG_OK  + $GFORTRAN_OK + $NMRPACK_OK + $SHELL_OK + $SPACK_LOAD_BASE_OK + $SPACK_LOAD_DEPENDENCIES_OK  + $GFORTRAN_SUPPORT_OK ))

if [ "$MISSING" == "0" ] ; then
  info
  info "nothing to do!"
  info "exiting..."
fi

# Ask the user if they want to proceed, defaulting to Yes.
# Choosing no exits the program. The arguments are printed as a question.
my_ask() {
  local question=$*

  inf "${bldcyn}${question}${clr} [Y/n] ${bldylw}"

  read a 2>/dev/null
  code=$?
  if [[ ${code} != 0 ]]; then
    error "Unable to read from STDIN."
    exit 12
  fi
  echo
  if [[ ${a} == 'y' || ${a} == 'Y' || ${a} == '' ]]; then
    return 0
  else
    return 1
  fi
}

info ""
if [ "$MISSING" != "0" ] ; then
   my_ask "Do you want to install missing features"
   if [ "$?" == "0" ]  ; then
     info ""
     hl::green "installing..."
     info ""
     INSTALL=1
   else
     info exiting...
     exit 1
   fi
fi


if [ "$INSTALL" == "1" ] ; then
  if [ "$XCS_OK" != "0" ] ; then

    echo "installing xcode tools" >> $LOG_FILE

    if [  -f /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress ] ; then
      echo "installing xcode tools failed: xcode tools installer already running" >> $LOG_FILE
      info '[xcode tools] xcode tools installer already running'
      info 'please complete the current installation and rerun this installer...'
      info 'exiting...'
      exit 2
    fi

    info ""
    info '[xcode tools]: please click the Install button in the dialog and accept the license'
    xcode-select --install >> $LOG_FILE &
    sleep 1

    chars="/-\|"
    i=0
    while  [  -f /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress ] ; do
      sleep 1

      echo -en "    ${chars:$i:1}" "\r"
      i=$((i+1))
      if [ "$i" ==  "4" ] ; then
        i=1
      fi
    done

    XCS=$(xcode-select -p) 2>&1 >> $LOG_FILE
    XCS_OK=$?
    if [ "$XCS_OK" == "0" ] ; then
      echo "xcode installation completed" >> $LOG_FILE
      info "[xcode tools]: installed in ${XCS}"
      info ""
    else
      echo "xcode installation failed" >> $LOG_FILE
      info "[xcode tools]: failed to install"
      info "exiting..."
      exit 2
    fi

  fi

  if [ "$SPACK_OK" != "0" ] ; then

    echo "installing spack" >> $LOG_FILE
    info ""
    info '[spack]: installing spack'
    path=
    info '[spack]: select an installation path'
    inf "[spack]: enter a value or type enter for default [$default_spack_path]:"
    read -p "" path
    path=${path:-$default_spack_path}

    if [ ! -d $path ]; then
      info "[spack]: path $path doesn\'t exists creating it"
      mkdir -p $path
    fi

    if [ ! -d $path ]; then
      echo "could not install spack as could not create path $path" >> $LOG_FILE
      info "[spack]: couldn't create $path"
      info "exiting..."
      exit 2
    fi

    if [ "$(ls -A $path)" ] ; then
      echo "could not install spack couldn't create path $path" >> $LOG_FILE
      info "[spack]: directory $path already exists and is not empty"
      info "[spack]: installation directory must be empty"
      info "exiting..."
      exit 2
    fi

    info "[spack]: cloning spack using git"
    git clone --quiet -c feature.manyFiles=true https://github.com/spack/spack.git ~/programs/spack 2>&1 >> $LOG_FILE  &
    clone_pid=$!

    i=0
    chars="/-\|"
    while  ps -p $clone_pid > /dev/null ; do
      sleep 1
      echo -en "    ${chars:$i:1}" "\r"
      i=$((i+1))
      if [ "$i" ==  "4" ] ; then
        i=1
      fi
    done

    if [ ! -d ${path}/.git ] ; then
      echo "spack failed to install" >> $LOG_FILE
      info "[spack]: failed to install"
      info exiting...
      exit 2
    else
      echo "spack installed in $path" >> $LOG_FILE
      info "[spack]: installed in $path"
      info ""
      SPACK=${path}
      SPACK_OK=0
    fi
  fi

  if [ "$SPACK_OK" == "0" ] ; then
    SPACK_EXE=${SPACK}/bin/spack
  fi

  if [ "$SPACK_OK" == "0" ] && [ "$NMRPACK_OK" == "1" ] ; then


    echo "installing nmrpack" >> $LOG_FILE
    default_nmrpack_path=${SPACK%/*}/nmrpack
    info ""
    info '[nmrpack]: installing nmrpack'
    path=
    info '[nmrpack]: select an installation path'
    info "[nmrpack]: enter a value or type enter for default [$default_nmrpack_path]:"
    read -p "" path

    path=${path:-$default_nmrpack_path}

    if [ ! -d $path ]; then
      info "[nmrpack]: path $path doesn\'t exists creating it"
      mkdir -p $path
    fi

    if [ ! -d $path ]; then
      echo "could not install nmrpack as could not create path $path" >> $LOG_FILE
      info "[nmrpack]: couldn't create $path"
      info "exiting..."
      exit 2
    fi

    if [ "$(ls -A $path)" ] ; then
      echo "could not install nmrpack couldn't create path $path" >> $LOG_FILE
      info "[nmrpack]: directory $path already exists and is not empty"
      info "[nmrpack]: installation directory must be empty"
      info "exiting..."
      exit 2
    fi

    info "[nmrpack]: downloading nmrpack using curl"
    curl --stderr - -L https://github.com/varioustoxins/nmrpack/archive/master.zip -o ${path}/nmrpack.zip 2>&1 >> $LOG_FILE  &
    clone_pid=$!

    i=0
    chars="/-\|"
    while  ps -p $clone_pid > /dev/null ; do
      sleep 1
      echo -en "    ${chars:$i:1}" "\r"
      i=$((i+1))
      if [ "$i" ==  "4" ] ; then
        i=1
      fi
    done

    if [ ! -f ${path}/nmrpack.zip ] ; then
      echo "nmrpack failed to download" >> $LOG_FILE
      info "[nmrpack]: failed to download"
      info exiting...
      exit 2
    fi

    info "[nmrpack]: extracting nmrpack using unzip"
    shopt -s dotglob nullglob
    unzip -d "$path" "${path}/nmrpack.zip" 2>&1 >> $LOG_FILE
    mv "$path"/*/* "$path" 2>&1 >> $LOG_FILE
    rmdir ${path}/nmrpack-master 2>&1 >> $LOG_FILE
    rm  ${path}/nmrpack.zip 2>&1 >> $LOG_FILE

    if [ ! -f ${path}/repo.yaml ] ; then
      echo "nmrpack failed to extract" >> $LOG_FILE
      info "[nmrpack]: failed to extract"
      info exiting...
      exit 2
    fi

    $SPACK_EXE repo add $path 2>&1 >> $LOG_FILE
    NMRPACK_OK=$?

    if [ "$NMRPACK_OK" != "0" ] ; then
      echo "nmrpack failed to install into spack" >> $LOG_FILE
      info "[nmrpack]: nmrpack failed to install into spack"
      info exiting...
      exit 2
    fi

  fi


  if [ "$SPACK_OK" == "0"   ] && [ $GFORTRAN_OK != "0" ] ; then

    echo "installing gcc and gfortran with spack" >> $LOG_FILE
    info '[gfortran]: installing gfortran by installing gcc with spack'
    info '[gfortran]: this may take some time'

    $SPACK_EXE install gcc 2>&1 >> $LOG_FILE  &
    spack_gcc_pid=$!


    i=0
    chars="/-\|"
    while  ps -p $spack_gcc_pid > /dev/null ; do
      sleep 1
      echo -en "    ${chars:$i:1}" "\r"
      i=$((i+1))
      if [ "$i" ==  "4" ] ; then
        i=1
      fi
    done

    $SPACK_EXE verify gcc 2>&1 > /dev/null
    GFORTRAN_OK=$?

    if [ "$GFORTRAN_OK" != "0" ] ; then
      echo "installing gcc & gfortran with spack failed" >> $LOG_FILE
      info "[gfortran]: failed to install"
    else
      echo "installation of gfortran & gcc with spack succeeded" >> $LOG_FILE
      info "[gfortran]: gfortran installed by spack"
      info ""
    fi
  fi

  if [ "$SPACK_OK" == "0"   ] && [ $XZ_OK != "0" ] ; then

    echo "installing xz with spack" >> $LOG_FILE
    info '[xz]: installing xz with spack'
    info '[xz]: this may take some time'

    $SPACK_EXE install xz 2>&1 >> $LOG_FILE  &
    spack_xz_pid=$!


    i=0
    chars="/-\|"
    while  ps -p $spack_xz_pid > /dev/null ; do
      sleep 1
      echo -en "    ${chars:$i:1}" "\r"
      i=$((i+1))
      if [ "$i" ==  "4" ] ; then
        i=1
      fi
    done

    $SPACK_EXE find -p xz 2>&1 > /dev/null
    XZ_OK=$?

    if [ $XZ_OK != "0" ] ; then
      echo "installing xz with spack failed" >> $LOG_FILE
      info "[xz]: failed to install"
    else
      echo "installation of xz with spack succeeded" >> $LOG_FILE
      info "[xz]: xz installed by spack"
      info ""
    fi
  fi

  if [ "$SPACK_OK" == "0"   ] && [ $ZSTD_OK != "0" ] ; then

    echo "installing zstd with spack" >> $LOG_FILE
    info '[zstd]: installing zstd with spack'
    info '[zstd]: this may take some time'

    $SPACK_EXE install zstd 2>&1 >> $LOG_FILE  &
    spack_zstd_pid=$!


    i=0
    chars="/-\|"
    while  ps -p $spack_zstd_pid > /dev/null ; do
      sleep 1
      echo -en "    ${chars:$i:1}" "\r"
      i=$((i+1))
      if [ "$i" ==  "4" ] ; then
        i=1
      fi
    done

    $SPACK_EXE find -p zstd 2>&1 > /dev/null
    ZSTD_OK=$?

    if [ $ZSTD_OK != "0" ] ; then
      echo "installing zstd with spack failed" >> $LOG_FILE
      info "[zstd]: failed to install"
    else
      echo "installation of zstd with spack succeeded" >> $LOG_FILE
      info "[zstd]: zstd installed by spack"
      info ""
    fi
  fi

  if [ "$SPACK_OK" == "0"   ] && [ $GNUPG2_OK != "0" ] ; then

    echo "installing gnupg2 with spack" >> $LOG_FILE
    info '[gnupg2]: installing gnupg2 with spack'
    info '[gnupg2]: this may take some time'

    $SPACK_EXE install gnupg 2>&1 >> $LOG_FILE  &
    spack_gnupg_pid=$!


    i=0
    chars="/-\|"
    while  ps -p $spack_gnupg_pid > /dev/null ; do
      sleep 1
      echo -en "    ${chars:$i:1}" "\r"
      i=$((i+1))
      if [ "$i" ==  "4" ] ; then
        i=1
      fi
    done

    $SPACK_EXE find -p gnupg 2>&1 > /dev/null
    GNUPG2_OK=$?

    if [ $GNUPG2_OK != "0" ] ; then
      echo "installing gnupg2 with spack failed" >> $LOG_FILE
      info "[gnupg2]: failed to install"
    else
      echo "installation of gnupg2 with spack succeeded" >> $LOG_FILE
      info "[gnupg2]: gnupg2 installed by spack"
      info ""
    fi
  fi

  if [ "$SPACK_OK" == "0"   ] && [ $HG_OK != "0" ] ; then

    echo "installing mercurial with spack" >> $LOG_FILE
    info '[mercurial]: installing mercurial with spack'
    info '[mercurial]: this may take some time'

    $SPACK_EXE install mercurial 2>&1 >> $LOG_FILE  &
    spack_hg_pid=$!

    i=0
    chars="/-\|"
    while  ps -p $spack_hg_pid > /dev/null ; do
      sleep 1
      echo -en "    ${chars:$i:1}" "\r"
      i=$((i+1))
      if [ "$i" ==  "4" ] ; then
        i=1
      fi
    done

    $SPACK_EXE find -p mercurial 2>&1 > /dev/null
    HG_OK=$?

    if [ $HG_OK != "0" ] ; then
      echo "installing mercurial with spack failed" >> $LOG_FILE
      info "[mercurial]: failed to install"
    else
      echo "installation of mercurial with spack succeeded" >> $LOG_FILE
      info "[mercurial]: mercurial installed by spack"
      info ""
    fi
  fi


  if [ "$SHELL_OK" != "0" ] ; then

    echo "installing spack support for $shell" >> $LOG_FILE

    # note this fails if the user moves ther home or spack
    read -r -d '' sh_setup <<SH_HERE

# nmrpack initialise spack
if [ -f  ${SPACK}/share/spack/setup-env.sh ] ; then
  . ${SPACK}/share/spack/setup-env.sh
fi
if [ -f ${HOME}/.nmrpack/spack_preload.sh ] ; then
  . ${HOME}/.nmrpack/spack_preload.sh
fi
# nmrpack finish initialise spack
SH_HERE

    case $shell in
      zsh)
         config="${HOME}/.zshenv"
         if [ ! -f $config ] ; then
           info "[shell support] zsh config: $config missing creating it"
           touch $config
         fi

         grep spack/share/spack/setup-env.sh $config 2>&1 > /dev/null
         SPACK_ENV_OK=$?

         if [ "$SPACK_ENV_OK" != "0" ] ; then
           echo "installing spack support into $config" >> $LOG_FILE
           info "[shell support] adding spack initialisation to $config"

           echo "$sh_setup" >> $config
         fi
      ;;

      bash)
        if [ -f  ${HOME}/.bash_profile ] ; then
          config=${HOME}/.bash_profile
        elif [ -f ${HOME}/.bash_login ]; then
          config=${HOME}/.bash_profile
        elif [ -f ${HOME}/.profile ]; then
          config=${HOME}/.profile
        else
          config=${HOME}/.bash_profile
        fi

        if [ ! -f $config ] ; then
         info "[shell support] zsh config: $config missing creating it"
         touch $config
        fi

        grep spack/share/spack/setup-env.sh $config 2>&1 > /dev/null
        SPACK_ENV_OK=$?

        if [ "$SPACK_ENV_OK" != "0" ] ; then
          echo "installing spack support into $config" >> $LOG_FILE
          info "[shell support] adding spack initialisation to $config"

          echo "$sh_setup" >> $config
        fi
      ;;

      *)
        echo "could not install spack shell support as i dont recognise shell $shell" >> $LOG_FILE
        info "[shell support] I don\'t recognise the shell $shell"
        info "[shell support] consult the spack manual for setup information"
        info "[shell support] and let the nmrpack developers know there is"
        info "[shell support] a problem with this integration"
      ;;
    esac
    info ""

  fi


  if [ "$SPACK_LOAD_BASE_OK" != "0"  ] ; then

    info "[spack packages load support]: install support for extra packages"
    echo "setting up spack extra packages support" >> $LOG_FILE

    if [ ! -d  ${HOME}/.nmrpack ] ; then

      info "[spack packages load support]: make ~/.nmrpack"
      mkdir ${HOME}/.nmrpack 2>&1 >> $LOG_FILE

      if [ ! -d ${HOME}/.nmrpack ] ; then
          info "[spack packages load support]: could'nt make ~/.nmrpack"
          info "[spack packages load support]: exiting..."
          exit 1
      fi
    fi

    info "[spack packages load support]: create pre load script"
    touch ${HOME}/.nmrpack/spack_preload.sh

    if [ ! -f ${HOME}/.nmrpack/spack_preload.sh ]  ; then
        info "[spack packages load support]: failed to create ${HOME}/.nmrpack/spack_preload.sh"
        info "[spack packages load support]: exiting..."
        exit 1
    fi

  fi

  if [ "$SPACK_LOAD_DEPENDENCIES_OK" != "0" ] ; then
    info "[spack load packages]: install loading of extra packages"
    echo "install loading of extra packages" >> $LOG_FILE
    echo "$SPACK_LOAD_COMMANDS" > ${HOME}/.nmrpack/spack_preload.sh
    echo "you will need to close and open your shell for theses changes to take effect"


    grep "do not edit this file it is maintained by the nmrpack installer" ${HOME}/.nmrpack/spack_preload.sh >/dev/null
    if [ "$?" != "0" ]; then
      echo "failed to update ${HOME}/.nmrpack/spack_preload.sh"
      info "[spack load packages]: failed to update file ${HOME}/.nmrpack/spack_preload.sh"
      info "[spack load packages]: exiting..."
      exit 1
    fi
  fi

  if [ "$GFORTRAN_SUPPORT_OK" != "0" ] ; then
   backup=${HOME}/.spack/darwin/compilers.yaml.`date +%F-%T`
   my_ask "[gfortran support] do you want to update compilers? A backup will be made."
   if [ "$?" == "0" ]  ; then
     info "[gfortran support updating ${HOME}/.spack/darwin/compilers.yaml"
     info "[gfortran support] copy backup of ${HOME}/.spack/darwin/compilers.yaml to $backup"
     cp ${HOME}/.spack/darwin/compilers.yaml  $backup
     if [ ! -f $backup ] ; then
       info "[gfortran support] couldn't create $backup"
       info "[gfortran support] exiting..."
       exit 1
     fi
     script='/fc: null/ {printf "      fc: %s\n",gfortran ; next } ; /f77: null/ {printf "      f77: %s\n",gfortran ; next } ;  {print $0}'
     file=${HOME}/.spack/darwin/compilers.yaml
     awk  "$script"  gfortran=$GFORTRAN $backup > $file

     OK=0
     ! grep 'fc: null' $file > /dev/null
     OK=$(( $OK + $? ))
     ! grep 'f77: null' $file > /dev/null
     OK=$(( $OK + $? ))

     if [ "$OK" != "0" ] ; then
       info "[gfortran support] failed to update $file with gfortran"
       info "[gfortran support] exiting..."
       exit 1
     else
       info "[gfortran support] success gfortran added to $file"
     fi
   else
     info "[gfortran support] no changes made"
   fi
  fi
fi
#
# end of file - installer_base_osx.sh
##[[[end]]]
