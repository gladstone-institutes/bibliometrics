while read line
do
  name="$line"
  read line
  institution="$line"
  read line
  output_path="$line"

  if [ -e "$output_path" ]; then
    echo "Skipping $name"
  else
    echo $name
    python src/bottomup.py --levels 2 "$name" "$institution" $output_path
  fi

done < $1
