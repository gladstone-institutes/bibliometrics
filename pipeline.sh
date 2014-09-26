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
net_path="${output_dir}/net.pkl.gz"
cy_net_path="${output_dir}/net.xgmml"

mkdir "${output_dir}"

python src/topdown.py "--format=${input_format}" "--levels=${num_levels}" "${dont_search_trials}" "input/${basename}.txt" "${layout_opt}" "${net_path}"

python src/xgmml.py "${net_path}" "${cy_net_path}"
tar pczf "${cy_net_path}.tar.gz" "${cy_net_path}"

for t in author institution grantagency; do
  python src/rankings.py "${net_path}" "${t}" "${output_dir}/${t}.csv"
done


