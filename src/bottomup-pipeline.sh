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
    output_dir=`dirname "${output_path}"`
    mkdir -p "${output_dir}"
    python src/bottomup.py -v --levels 1 "$name" "$institution" "$output_path"
    sleep 60
  fi

done < $1
