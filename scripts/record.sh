#! /bin/bash

file="$1"
train_dir="$2"

while read -r line; do
    url="$line"
    record_file=$(echo "$line" | sed 's/https:\/\///' | sed 's/\//__/g')
    record_dir="$train_dir/$record_file"

    if [[ -d "$record_dir" ]]; then
        echo "exists: $url, $record_dir"
    else
        echo "record: $url, $record_dir"
        timeout --foreground 60 blaze record --record_dir $record_dir $url
    fi
done < "$file"
