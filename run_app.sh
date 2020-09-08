#!/bin/bash
if [[ $private_repo ]]; then
  pip install -e "git+https://$pr_token@github.com/$pr_path#egg=ya-fetcher"
fi
python -m awesome-1frag-projects
