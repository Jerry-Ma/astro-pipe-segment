#! /bin/sh
#
# hselect.sh
# Copyright (C) 2015 Jerry Ma <jerry.ma.nk@gmail.com>
#
#----------------------------------------------------------------------------
#"THE BEER-WARE LICENSE" (Revision 42):
#Jerry wrote this file. As long as you retain this notice you
#can do whatever you want with this stuff. If we meet some day, and you think
#this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp
#----------------------------------------------------------------------------


print_usage(){
cat <<EOF
+- hselect.sh
 usage: $0 [options] <fits image> <keywords>
     Implementation of IRAF images.imutil.HSELECT in bash + WCSTools.
     By default, the short filename ('\$i') is prepended to the keyword
     list. This behavior is overridden if '\$I' or '\$i' are present
     explicitly, for which the full or short filename apears at given
     column.
         Note: this script only works with the primary header for now.
 dependencies:
     WCSTools imhead
+- arguments
     <fits image>        The fits images to be search on. wildcard is
                         supported.
     <keywords>          A list of standard 'grep' pattern for filtering
                         the header. They should be separated by comma,
                         and when there are spaces, the entire argument
                         should be single quoted.
+- options
     -h          --help
                 Print this message
     -f <field>  --search-field=<field>
                 Restric the 'grep' searching to given fields:
                     key: the header keys
                     value: the header values
                     keyvalue: the keys plus values
                     all: the keys plus values plus comments
     -d          --dry-run
                 Print out command list instead of run
+- script by Z.Ma
EOF
}

detect_bin(){
    if which $1 >/dev/null 2>&1; then
        echo "$1"
    else
        bin=($(locate -b "\\$1"))
        if [[ ${bin[*]} ]]; then
            echo "${bin[0]}"
        fi
    fi
}
checkerr=()
optspec=":f:hd-:"
while getopts "$optspec" optchar; do
    case "${optchar}" in
        f)  field="$OPTARG"
            ;;
        h)  print_usage; exit 0
            ;;
        d)  dryrun="yes"
            ;;
        -)  case "${OPTARG}" in
                search-field)
                    field="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                    ;;
                search-field=*)
                    field="${OPTARG#*=}"
                    ;;
                help)
                    print_usage; exit 0
                    ;;
                dry-run)
                    dryrun="yes"
                    ;;
                *)  if [[ $OPTERR == 1 ]]; then
                        checkerr+=("[!] unknown option --${OPTARG}")
                    fi
                    ;;
            esac;;
        *)
            if [[ $OPTERR != 1 ]] || [[ ${optspec:0:1} == ":" ]]; then
                checkerr+=("[!] unknown option -${OPTARG}")
            fi
            ;;
    esac
done
shift $((OPTIND - 1))
imhead=$(detect_bin "imhead")
if [[ ! $imhead ]]; then
    checkerr+=("[!] dependency required: WCSTools imhead")
fi
image=()
while (( "$#" )); do
    if [[ $1 == -?* ]] ; then
        checkerr+=("[!] option $1 should sit before positional arguments")
        shift
        continue
    fi
    image+=("$1")
    shift
done
if [[ ${#image[@]} -lt 2 ]]; then
    checkerr+=("[!] no image and/or keywords specified")
else
    keywords=${image[-1]}
    unset image[${#image[@]}-1]
fi
if [[ ${checkerr[*]} ]]; then
    print_usage 1>&2
    for i in "${checkerr[@]}"; do
        echo "$i" 1>&2
    done
    exit 1
fi

# forge grep argument
grep_arg=()
grep_inv_arg=()
IFS=',' read -ra grepkeys <<< "$keywords"
for ((i=0; i<${#grepkeys[@]}; i++)); do
    if [[ ${grepkeys[$i]} =~ ^~(.+) ]]; then
        grep_inv_arg+=(${BASH_REMATCH[1]})
    else
        grep_arg+=(${grepkeys[$i]})
    fi
done

echo ${image[@]}
for ((i=0; i<${#grep_arg[@]}; i++)); do
    if [[ ${grep_arg[$i]} == '$i' ]]; then
        fnamemode='short'
    else if [[ ${grep_arg[$i]} == '$I' ]]; then
        fnamemode='long'
    fi
    if [[ $i == 0 ]]; then
        grep_cmd="${grep_arg[$i]}"
    else
        grep_cmd="${grep_cmd}|${grep_arg[$i]}"
    fi
done
grep_inv_cmd="aldskjfalfjasldfj"
for ((i=0; i<${#grep_inv_arg[@]}; i++)); do
    grep_inv_cmd="${grep_inv_cmd}|${grep_inv_arg[$i]}"
done

echo "grep args:" ${grep_cmd}
echo "grep -v args:" ${grep_inv_cmd}

_grep="grep --color -E"
for ((i=0; i<${#image[@]}; i++)); do
    if [[ $dryrun ]]; then
        echo "$imhead ${image[$i]} | ${_grep} -v '${grep_inv_cmd}' | ${_grep} '${grep_cmd}'"
    else
        $imhead ${image[$i]} \
            | ${_grep} -v '^COMMENT' \
            | ${_grep} -v "${grep_inv_cmd}" | ${_grep} "${grep_cmd}" \
            | sed 's/^\(.*\)=\(.*\) \/ .*/\1\-_-\2/' | sed 's/\s\+//g' | sed 's/-_-/ /g' \
            | (echo "filename '${image[$i]}'" && cat) \
            | awk '
{
    for (i=1; i<=NF; i++)  {
        a[NR,i] = $i
    }
}
NF>p { p = NF }
END {
    for(j=1; j<=p; j++) {
        str=a[1,j]
        for(i=2; i<=NR; i++){
            str=str" "a[i,j];
        }
        print str
    }
}'
    fi
done


