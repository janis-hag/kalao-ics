#!/usr/bin/env bash

# Will symlink
# ./_file1         -> /home/kalao/.file1
# ./_folder1       -> /home/kalao/.folder1
# ./folder2/_file2 -> /home/kalao/.folder2/file2
# ...

# Colors
red="\033[31m"
green="\033[32m"
yellow="\033[33m"
blue="\033[34m"
purple="\033[35m"
default="\033[0m"

fake=false

make_symlink() {
    source=$1
    dest=$2
    if [ $source -ef $dest ]
    then
        echo -e "GOOD    ${green}symlink$default    $blue$source$default -> $purple$dest$default"
    elif [ -L $dest ]
    then
        echo -e "BAD     ${red}symlink$default    $blue$source$default -> $purple$dest$default"
    elif [ -e $dest ]
    then
        echo -e "NOT A   ${red}symlink$default    $blue$source$default -> $purple$dest$default"
    else
        if ! $fake
        then
            ln -s $source $dest
        fi
        echo -e "CREATED ${yellow}symlink$default    $blue$source$default -> $purple$dest$default"
     fi
}

install_symlinks() {
    files=$(find . -name "_*"  -printf '%P\n')

    for file in $files
    do
        source="`pwd`/$file"
        dest=$(sed 's/_//' <(echo "$HOME/.$file"))
        make_symlink $source $dest
    done
}

dry_run=false
while getopts ":fn" opt; do
  case $opt in
    d)
      dry_run=true >&2
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

install_symlinks
