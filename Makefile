

.PHONY: test-publish
test-publish:
	poetry build
	twine upload --repository testpypi dist/* --