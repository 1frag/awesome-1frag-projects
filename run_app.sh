#!/bin/bash
if [[ $private_repo ]]; then
  mkdir tmp
  curl -L "https://$pr_token@github.com/$pr_path/archive/$pr_branch.zip" --output ./tmp/ya-fetcher.zip
  unzip ./tmp/ya-fetcher.zip -d ./tmp
  cd "$(dirname "$(find ./tmp/*/setup.py)")"
  pip install -r requirements.txt
  python setup.py install
  cd /app
fi
python -m awesome-1frag-projects
