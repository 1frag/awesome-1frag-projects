#!/bin/bash
if [[ $private_repo ]]; then
  pip install -e "git+https://$pr_token@github.com/$pr_path#egg=iadaptation"
fi
python app.py
