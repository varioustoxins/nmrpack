mkdir unused
mv `ls -A | grep -v unused` unused
mv unused/.github .
rm -rf unused