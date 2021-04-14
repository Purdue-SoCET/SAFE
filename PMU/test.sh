# !/bin/sh
# for i in 1 2 3 4 5
# do
#   echo "Looping ... number $i"
# done

for i in 1 2 3 4 5 6 7 8 9 10
do
  python main.py > test.txt
  if grep -q 'CONTEXT' test.txt; then
    echo $i
    cat test.txt
    # echo "uh"
  fi
done > final.txt