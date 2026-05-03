.PHONY: install test validate rebuild smoke paper clean

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

validate:
	python scripts/validate_paper_full.py

rebuild:
	python scripts/validate_and_build.py --raw_dir results/raw_camera_ready --questions data/questions.json --out_dir build/camera_ready --use_intersection --n_boot 2000

smoke:
	python scripts/validate_and_build.py --raw_dir results/raw_camera_ready --questions data/questions.json --out_dir /tmp/sycobench_build --use_intersection --n_boot 50

paper:
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error sycobench_camera_ready.tex

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -delete
