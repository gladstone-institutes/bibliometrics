basename="${1}"
input_format="${2}"
num_levels="${3}"
perform_layout="${4}"

dont_search_trials=""
if [ "${input_format}" = "pmid" ]; then
  dont_search_trials="--dont-search-trials"
fi

layout_opt=""
if [ "${perform_layout}" = "layout" ]; then
  layout_opt="--layout"
fi

output_dir="${basename}-levels-${num_levels}-output"

mkdir "${output_dir}"

python src/topdown.py "--format=${input_format}" "--levels=${num_levels}" "${dont_search_trials}" "input/${basename}.txt" "${layout_opt}" "${output_dir}/net"

python src/xgmml.py "${output_dir}/net.pkl.gz" "${output_dir}/net"
tar pczf "${output_dir}/net.xgmml.tar.gz" "${output_dir}/net.xgmml"

for t in author institution grantagency; do
  python src/rankings.py "${output_dir}/net.pkl.gz" "${t}" "${output_dir}/${t}"
done


