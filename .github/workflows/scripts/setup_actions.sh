mkdir unused
# https://askubuntu.com/questions/91740/how-to-move-all-files-in-current-folder-to-subfolder second solution
ls | grep -v unused | xargs mv -t unused
mv unused/.github .
rm -rf unused