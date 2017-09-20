#! /bin/bash
#
# imsel.sh
# script by Jerry Ma <jerry.ma.nk@gmail.com>
#
#----------------------------------------------------------------------------
#"THE BEER-WARE LICENSE" (Revision 42):
#Jerry wrote this file. As long as you retain this notice you
#can do whatever you want with this stuff. If we meet some day, and you think
#this stuff is worth it, you can buy me a beer in return
#----------------------------------------------------------------------------

print_usage(){
cat <<EOF
+- imsel.sh
 usage: $0 [options] <coordinate list> <fits image>
     Take the <coordinate list>, investigate the given <fits images>,
     return fits file name if the coordinate is covered. Cutouts can
     be written to <cut dir>[./imselcut by default] if size is
     specified in unit of <pixel>. Catalogue can be grepped if -g
     specified and catalogue share the same basename with the fits
     image.
 dependencies:
     WCSTools imsize, sky2xy, getfits
+- arguments
     <coordinate list>   The input file contain Ra, Dec in the first
                         two column; alternatively use '-' to indicate
                         a piped-in input
     <fits image>        The fits image to be search on. wildcard is
                         supported.
+- options
     -h          --help
                 Print this message
     -v          --verbose
                 Output ra, dec, x, y and boundaries to STDERR
     -c <pixel>  --cut-size=<pixel>
                 Invoke 'getfits' to cut image to size of
                 <pixel> x <pixel> and output to ./imselcut
     -g <colnum> --grep-catalogue=<colnum>
                 Call awk to cutout the associated catalogue
                 accord to the x, y position, with the column
                 number of x given in <colnum>
     -o <dir>    --out-dir=<dir>
                 Directory to create for outputed cutouts
                 default ./imselcut
     -f <fmt>    --out-fmt=<fmt>
                 Format string that operates on the coordinate list
                 to create the prefix of the output cutout filenames.
                 The format string is evaluated against the entry
                 of coordinate list, e.g. -f '\$3_\$4_\$5' will
                 expand to 'a_b_c' if the line is "120.0 -10.0 a b c".
                 A spectial variable '\$i' will expand to the index
                 (starting from 1) of the entry.
                 default is "cut_\$i_"
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
optspec=":c:g:hdof:v-:"
while getopts "$optspec" optchar; do
    case "${optchar}" in
        c)  cutsize="$OPTARG"
            ;;
        g)  grepcat="$OPTARG"
            ;;
        h)  print_usage; exit 0
            ;;
        v)  verbose=yes
            ;;
        d)  dryrun=yes
            ;;
        o)  outdir="$OPTARG"
            ;;
        f)  cutoutfmt="$OPTARG"
            ;;
        -)  case "${OPTARG}" in
                cut-size)
                    cutsize="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                    ;;
                cut-size=*)
                    cutsize="${OPTARG#*=}"
                    ;;
                grep-catalogue)
                    grepcat="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                    ;;
                grep-catalogue=*)
                    grepcat="${OPTARG#*=}"
                    ;;
                help)
                    print_usage; exit 0
                    ;;
                out-dir)
                    outdir="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                    ;;
                out-dir=*)
                    outdir="${OPTARG#*=}"
                    ;;
                out-fmt)
                    cutoutfmt="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                    ;;
                out-fmt=*)
                    cutoutfmt="${OPTARG#*=}"
                    ;;
                verbose)
                    verbose="yes"
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
imsize=$(detect_bin "imsize")
if [[ ! $imsize ]]; then
    checkerr+=("[!] dependency required: WCSTools imsize")
fi
sky2xy=$(detect_bin "sky2xy")
if [[ ! $sky2xy ]] && [[ $cutsize ]]; then
    checkerr+=("[!] dependency required: WCSTools sky2xy")
fi
getfits=$(detect_bin "getfits")
if [[ ! $getfits ]] && [[ $cutsize ]]; then
    checkerr+=("[!] dependency required: WCSTools getfits")
fi
if [[ ! ${cutoutfmt} =~ ^[\-+\$_./{}A-Za-z0-9]*$ ]]; then
    # do not allow [a-zA-Z]
    checkerr+=('[!] only [{}-+$_./A-Za-z0-9] are allowed in -f argument')
fi
image=()
while (( "$#" )); do
    if [[ $1 == -?* ]] ; then
        checkerr+=("[!] option $1 should sit before positional arguments")
        shift
        continue
    fi
    if [[ $coordlist ]]; then
        image+=("$1")
    else
        coordlist="$1"
    fi
    shift
done
regf="[0-9]+\.?[0-9]*"
regh="[0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}\.?[0-9]*"
ra=()
dec=()
if [[ $coordlist == "-" ]] || [[ -f $coordlist ]]; then
    if [[ $coordlist == "-" ]]; then
        IFS=$'\n' read -d '' -r -a lines < /proc/${$}/fd/0
    elif [[ -f $coordlist ]]; then
        IFS=$'\n' read -d '' -r -a lines < $coordlist
    fi
    deg_regex="^[[:space:]]*(${regf})[[:space:]]+([-+]?${regf})"
    hms_regex="^[[:space:]]*(${regh})[[:space:]]+([-+]?${regh})"
    for ((i=0; i<${#lines[@]}; i++)); do
        if [[ ${lines[$i]} =~ $deg_regex ]]; then
            if [[ $coord_fmt == "hhmmss" ]]; then
                checkerr+=("[!]inconsistent coordinate format: $lines")
            elif [[ ! $coord_fmt ]]; then
                coord_fmt="degree"
                strfmt="%-15.3f"
            fi
        elif [[ ${lines[$i]} =~ $hms_regex ]]; then
            if [[ $coord_fmt == "degree" ]]; then
                checkerr+=("[!]inconsistent coordinate format: $lines")
            elif [[ ! $coord_fmt ]]; then
                coord_fmt="hhmmss"
                strfmt="%-15s"
            fi
        else
            continue
        fi
        ra+=(${BASH_REMATCH[1]})
        dec+=(${BASH_REMATCH[2]})
    done
    if [[ ! ${ra[*]} ]]; then
        checkerr+=("[!] empty coordinate list: $coordlist")
    fi
else
    checkerr+=("[!] invalid coordinate file: $coordlist")
fi
if [[ ! ${image[*]} ]]; then
    checkerr+=("[!] no target image specified")
fi
if [[ ${checkerr[*]} ]]; then
    print_usage 1>&2
    for i in "${checkerr[@]}"; do
        echo "$i" 1>&2
    done
    exit 1
fi

imsize_regex="RA:[[:space:]]+(${regf})[[:space:]]+-[[:space:]]+(${regf}).+Dec:[[:space:]]+([-+]?${regf})[[:space:]]+-[[:space:]]+([-+]?${regf})"
imsize_par="-rd"

imsize_regex_xy="([0-9]+)x([0-9]+)[[:space:]]+pix"
imsize_par_xy="-d"

sky2xy_regex="->[[:space:]]+([-+]?${regf})[[:space:]]+([-+]?${regf})"
for ((i=0; i<${#image[@]}; i++)); do
    range=$($imsize $imsize_par ${image[$i]})
    if [[ $range =~ $imsize_regex ]]; then
        imname[$i]=${image[$i]}
        ra_min[$i]=${BASH_REMATCH[1]}
        ra_max[$i]=${BASH_REMATCH[2]}
        dec_min[$i]=${BASH_REMATCH[3]}
        dec_max[$i]=${BASH_REMATCH[4]}
        # add imsize x and y
        range_xy=$($imsize $imsize_par_xy ${image[$i]})
        if [[ $range_xy =~ $imsize_regex_xy ]]; then
            xsize[$i]=${BASH_REMATCH[1]}
            ysize[$i]=${BASH_REMATCH[2]}
            # echo ${xsize[$i]}, ${ysize[$i]}
        fi
        # handle coord wrap
        # use bc to support older bash
        if (( $(bc <<< "${ra_min[$i]} > ${ra_max[$i]}") == 1 )); then
            rawrap="yes"
        fi
        imok[$i]='yes'
    else
        echo "[!] imsize fail: ${image[$i]}" 1>&2
        imok[$i]='no'
    fi
done
h2d(){
    hms_regex="([-+]?)([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2}\.?[0-9]*)"
    if [[ $1 =~ $hms_regex ]]; then
        sign=${BASH_REMATCH[1]}
        hh=${BASH_REMATCH[2]}
        mm=${BASH_REMATCH[3]}
        ss=${BASH_REMATCH[4]}
        if [[ $sign ]]; then
            deg=$(bc -l <<< "${hh}+${mm}/60+${ss}/3600")
            printf "%.15f\n" ${sign}${deg}
        else
            deg=$(bc -l <<< "${hh}*15+${mm}/4+${ss}/240")
            printf "%.15f\n" ${sign}${deg}
        fi
    else
        echo $1
    fi
}
formatline(){
    i=$1; shift
    if [[ ! ${cutoutfmt} ]]; then
        echo "cut_${i}_"
    else
        # quote $i
        cutoutfmt=$(sed 's/\$\([A-Za-z][A-Za-z0-9]*\)_/${\1}_/g' <<< ${cutoutfmt})
        out=$(eval "echo ${cutoutfmt}")
        echo ${out}
    fi
}
for ((i=0; i<${#ra[@]}; i++)); do
    #h2d ${ra[$i]}
    #h2d ${dec[$i]}
    for ((j=0; j<${#image[@]}; j++)); do
        if [[ ${imok[$j]} == 'no' ]]; then
            # echo "[!] skip ${image[$j]}" 1>&2
            continue
        fi
        # h2d ${ra_min[$j]}
        # h2d ${ra_max[$j]}
        # h2d ${dec_min[$j]}
        # h2d ${dec_max[$j]}
        _ra=$(h2d ${ra[$i]})
        if (( $(bc <<< "${_ra} < 0") == 1 )); then
            _ra=$(bc -l <<< "${_ra} + 360.")
        fi
        _dec=$(h2d ${dec[$i]})
        # handle ra wrap
        if [[ $rawrap ]]; then
            if (( $(bc <<< "${_ra} >= ${ra_min[$j]}") == 1 )) || \
               (( $(bc <<< "${_ra} <= ${ra_max[$j]}") == 1 )); then
                ra_in="yes"
            fi
        else
            echo ${ra_min[$j]}
            if (( $(bc <<< "${_ra} >= ${ra_min[$j]}") == 1 )) && \
               (( $(bc <<< "${_ra} <= ${ra_max[$j]}") == 1 )); then
                ra_in="yes"
            fi
        fi
        if [[ $ra_in ]] && \
            (( $(bc <<< "${_dec} >= ${dec_min[$j]}") == 1 )) && \
            (( $(bc <<< "${_dec} <= ${dec_max[$j]}") == 1 ))
        then
            if [[ $verbose ]]; then
                echo ${imname[$j]}
                printf " |ra    |$strfmt|$strfmt|$strfmt|\n" "${ra_min[$j]}" "$ra" "${ra_max[$j]}" 1>&2
                printf " |dec   |$strfmt|$strfmt|$strfmt|\n" "${dec_min[$j]}" "$dec" "${dec_max[$j]}" 1>&2
            fi
            if [[ $cutsize ]]; then
                xy=$($sky2xy ${imname[$j]} ${ra[$i]} ${dec[$i]})
                if [[ $xy =~ $sky2xy_regex ]]; then
                    x=${BASH_REMATCH[1]}
                    y=${BASH_REMATCH[2]}
                    if (( $(bc <<< "$x < 1") == 1 )); then
                        x=1
                    fi
                    if (( $(bc <<< "$x > ${xsize[$j]}") == 1 )); then
                        x=${xsize[$j]}
                    fi
                    if (( $(bc <<< "$y < 1") == 1 )); then
                        y=1
                    fi
                    if (( $(bc <<< "$y > ${ysize[$j]}") == 1 )); then
                        y=${ysize[$j]}
                    fi
                    x_min=$(bc -l <<< "$x-${cutsize}*0.5")
                    x_max=$(bc -l <<< "$x+${cutsize}*0.5")
                    y_min=$(bc -l <<< "$y-${cutsize}*0.5")
                    y_max=$(bc -l <<< "$y+${cutsize}*0.5")
                    if [[ $verbose ]]; then
                        printf " |x     |$strfmt|$strfmt|$strfmt|\n" "$x_min" "$x" "$x_max" 1>&2
                        printf " |y     |$strfmt|$strfmt|$strfmt|\n" "$y_min" "$y" "$y_max" 1>&2
                    fi
                    if [[ ! ${outdir} ]]; then
                        outdir="imselcut"
                    fi
                    imnamelong=${imname[$j]}
                    imnamedir=${imnamelong%/*}
                    imnamebase=${imnamelong##*/}
                    cutoutnamebase=$(formatline $(($i+1)) ${lines[$i]})
                    # replace spaces with underscore
                    cutoutnamebase=${cutoutnamebase// /_}
                    cutoutname="$outdir/${cutoutnamebase}${imnamebase}"
                    cutoutdir=${cutoutname%/*}
                    mkdir -p ${cutoutdir}
                    if [[ $dryrun ]]; then
                        echo "getfits" ${imname[$j]} $x $y $cutsize $cutsize -o "${cutoutname}"
                    else
                        $getfits ${imname[$j]} $x $y $cutsize $cutsize -o "${cutoutname}"
                        printf "cutsize(${cutsize}x${cutsize}): ${cutoutname}\n"
                    fi
                    if [[ $grepcat ]]; then
                        catname=${imnamelong%%.*}.cat
                        catnamebase=${catname##*/}
                        catoutname="$outdir/${cutoutnamebase}${catnamebase}"
                        awk -v xmin=$x_min \
                            -v ymin=$y_min \
                            -v xmax=$x_max \
                            -v ymax=$y_max \
                            -v colx=$grepcat \
                            '{if($0!~/^[[:space:]]*#/){
                                if($colx>xmin && $colx<xmax && $(colx+1)>ymin && $(colx+1)<ymax){
                                    print $0}}
                              else{
                                print $0}}' $catname > ${catoutname}
                        printf "grep catlog: ${catoutname}\n"
                    fi
                else
                    echo "[!] sky2xy fail: $xy" 1>&2
                fi
            fi
        fi
    done
done
