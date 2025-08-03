

.PHONY: test-publish
test-publish:
	poetry build
	twine upload --repository testpypi dist/* --


.PHONY: format
format:
	poetry run ruff format