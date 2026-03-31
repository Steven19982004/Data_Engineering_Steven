PYTHON=python3

.PHONY: install build ask eval test

install:
	$(PYTHON) -m pip install -r requirements.txt

build:
	PYTHONPATH=src $(PYTHON) scripts/run_pipeline.py

ask:
	PYTHONPATH=src $(PYTHON) scripts/run_agent.py --question "找出 2015 年后的高评分科幻片"

eval:
	PYTHONPATH=src $(PYTHON) scripts/run_eval.py

test:
	PYTHONPATH=src pytest
