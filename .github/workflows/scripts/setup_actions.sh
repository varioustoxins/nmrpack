mkdir unused
# https://askubuntu.com/questions/91740/how-to-move-all-files-in-current-folder-to-subfolder second solution
mv `ls -a | grep -v unused` unused
mv unused/.github .
rm -rf unused