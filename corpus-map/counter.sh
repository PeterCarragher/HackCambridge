for dd in `ls`; do
   ls $dd|wc -l|tr "\n" "    " 
   echo "$dd"|tr "\n" "    " 
   ls $dd|wc -l
done