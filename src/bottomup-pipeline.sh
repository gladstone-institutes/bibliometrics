while read line
do
  name="$line"
  read line
  institution="$line"
  read line
  output_path="$line"

  echo $name
  python src/bottomup.py --levels 2 "$name" "$institution" $output_path

done < $1
